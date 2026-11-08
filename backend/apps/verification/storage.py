import hashlib
import io
import logging
import uuid

import boto3
from botocore.config import Config
from django.conf import settings
from django.db import transaction
from PIL import Image, UnidentifiedImageError
from pypdf import PdfReader

from apps.verification.models import DriverVerificationEvidence


logger = logging.getLogger(__name__)


class EvidenceStorageError(Exception):
    """Raised when an evidence file cannot be safely validated or stored."""


def _s3_client():
    if not settings.R2_EVIDENCE_STORAGE_ENABLED:
        raise EvidenceStorageError("Private evidence storage is not configured.")

    return boto3.client(
        "s3",
        endpoint_url=settings.R2_ENDPOINT_URL,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        region_name=settings.R2_REGION,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


def _read_and_validate(uploaded_file):
    max_bytes = settings.R2_MAX_UPLOAD_BYTES
    if uploaded_file.size <= 0 or uploaded_file.size > max_bytes:
        raise EvidenceStorageError(f"The file must be between 1 byte and {max_bytes // (1024 * 1024)} MB.")

    content = uploaded_file.read(max_bytes + 1)
    if len(content) != uploaded_file.size or len(content) > max_bytes:
        raise EvidenceStorageError("The uploaded file size is invalid.")

    detected_type = None
    try:
        image = Image.open(io.BytesIO(content))
        image.verify()
        image = Image.open(io.BytesIO(content))
        if image.format not in {"JPEG", "PNG"}:
            raise EvidenceStorageError("Only JPEG, PNG, and PDF files are accepted.")
        if image.width > 12000 or image.height > 12000 or image.width * image.height > 40000000:
            raise EvidenceStorageError("The image dimensions are too large.")
        detected_type = "image/jpeg" if image.format == "JPEG" else "image/png"
    except UnidentifiedImageError:
        if not content.startswith(b"%PDF-"):
            raise EvidenceStorageError("The file content is not a supported JPEG, PNG, or PDF.")
        try:
            reader = PdfReader(io.BytesIO(content), strict=True)
            if reader.is_encrypted:
                raise EvidenceStorageError("Encrypted PDF files are not accepted.")
            if not reader.pages or len(reader.pages) > 20:
                raise EvidenceStorageError("PDF files must contain between 1 and 20 pages.")
        except EvidenceStorageError:
            raise
        except Exception as exc:
            raise EvidenceStorageError("The PDF file is invalid or damaged.") from exc
        detected_type = "application/pdf"
    except (OSError, ValueError, Image.DecompressionBombError) as exc:
        raise EvidenceStorageError("The image file is invalid or damaged.") from exc

    return content, detected_type, hashlib.sha256(content).hexdigest()


def store_verification_evidence(*, check, uploaded_file, actor, source):
    if source not in {
        DriverVerificationEvidence.Source.DRIVER_UPLOAD,
        DriverVerificationEvidence.Source.OPERATIONS_UPLOAD,
    }:
        raise EvidenceStorageError("Unsupported evidence upload source.")

    if check.verification.status in {"approved", "rejected"}:
        raise EvidenceStorageError("Evidence cannot be uploaded after a final verification decision.")

    content, content_type, digest = _read_and_validate(uploaded_file)
    object_key = f"verification-evidence/{check.verification_id}/{uuid.uuid4().hex}"
    client = _s3_client()

    try:
        client.put_object(
            Bucket=settings.R2_BUCKET_NAME,
            Key=object_key,
            Body=content,
            ContentType=content_type,
            Metadata={"sha256": digest},
        )
    except Exception as exc:
        raise EvidenceStorageError("The private evidence file could not be stored.") from exc

    safe_filename = (uploaded_file.name or "evidence").replace("\\", "/").rsplit("/", 1)[-1]
    safe_filename = "".join(char for char in safe_filename if char.isprintable() and char not in "\r\n")[:255]

    # Keep the database transaction inside this try block. This also catches a
    # failure raised while the transaction commits, not only row-creation errors.
    try:
        with transaction.atomic():
            evidence = DriverVerificationEvidence.objects.create(
                verification_check=check,
                evidence_type=check.check_type,
                source=source,
                status=DriverVerificationEvidence.Status.SUBMITTED,
                original_filename=safe_filename or "evidence",
                content_type=content_type,
                file_size=len(content),
                sha256=digest,
                storage_key=object_key,
                uploaded_by=actor,
            )

            from apps.verification.models import DriverVerificationEvidenceEvent

            DriverVerificationEvidenceEvent.objects.create(
                evidence=evidence,
                actor=actor,
                event_type="uploaded",
                new_status=DriverVerificationEvidence.Status.SUBMITTED,
            )
    except Exception:
        try:
            client.delete_object(Bucket=settings.R2_BUCKET_NAME, Key=object_key)
        except Exception:
            # Do not hide the database failure, but leave an operational signal
            # so an orphaned private object can be reconciled.
            logger.exception("Could not clean up R2 evidence object after database failure: %s", object_key)
        raise

    return evidence


def retrieve_verification_evidence(evidence):
    client = _s3_client()
    try:
        result = client.get_object(
            Bucket=settings.R2_BUCKET_NAME,
            Key=evidence.storage_key,
        )
    except Exception as exc:
        raise EvidenceStorageError("The private evidence file could not be retrieved.") from exc
    return result["Body"], evidence.content_type, evidence.original_filename
