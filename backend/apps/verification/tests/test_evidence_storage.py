import io
from datetime import timedelta
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone
from PIL import Image

from apps.identity.models import Account
from apps.registrations.models import DriverRegistration
from apps.profiles.models import DriverProfile
from apps.verification.models import (
    DriverVerificationEvidence,
    DriverVerificationEvidenceEvent,
)
from apps.verification.storage import (
    EvidenceStorageError,
    _read_and_validate,
    retrieve_verification_evidence,
    store_verification_evidence,
)


class EvidenceFileValidationTests(SimpleTestCase):
    def _jpeg(self):
        output = io.BytesIO()
        Image.new("RGB", (32, 32), color="white").save(output, format="JPEG")
        return output.getvalue()

    def test_accepts_real_jpeg_content_and_hashes_it(self):
        content = self._jpeg()
        uploaded = SimpleUploadedFile("identity.jpg", content, content_type="image/jpeg")

        validated, content_type, digest = _read_and_validate(uploaded)

        self.assertEqual(validated, content)
        self.assertEqual(content_type, "image/jpeg")
        self.assertEqual(len(digest), 64)

    def test_rejects_svg_even_when_named_as_jpeg(self):
        uploaded = SimpleUploadedFile(
            "identity.jpg",
            b"<svg xmlns='http://www.w3.org/2000/svg'></svg>",
            content_type="image/jpeg",
        )

        with self.assertRaises(EvidenceStorageError):
            _read_and_validate(uploaded)

    @override_settings(R2_MAX_UPLOAD_BYTES=5)
    def test_rejects_files_over_configured_size_limit(self):
        uploaded = SimpleUploadedFile("large.jpg", b"123456", content_type="image/jpeg")

        with self.assertRaises(EvidenceStorageError):
            _read_and_validate(uploaded)

    def test_rejects_malformed_pdf(self):
        uploaded = SimpleUploadedFile(
            "identity.pdf",
            b"%PDF-1.7\nthis is not a valid PDF",
            content_type="application/pdf",
        )

        with self.assertRaises(EvidenceStorageError):
            _read_and_validate(uploaded)


@override_settings(
    R2_EVIDENCE_STORAGE_ENABLED=True,
    R2_BUCKET_NAME="divs-private-evidence",
    R2_MAX_UPLOAD_BYTES=10 * 1024 * 1024,
)
class EvidenceR2StorageTests(TestCase):
    def setUp(self):
        self.actor = Account.objects.create_user(
            email="evidence-driver@example.com",
            password="StrongPassword123!",
        )
        registration = DriverRegistration.objects.create(
            account=self.actor,
            first_name="Amani",
            middle_name="",
            last_name="Juma",
            nationality="Tanzanian",
            region="Dar es Salaam",
            district="Kinondoni",
            current_residential_address="Mikocheni",
            driving_experience="1_to_3_years",
        )
        self.profile = DriverProfile.objects.create(registration=registration)
        self.check = self.profile.verification.checks.first()

    def _jpeg_upload(self, name="identity.jpg"):
        output = io.BytesIO()
        Image.new("RGB", (32, 32), color="white").save(output, format="JPEG")
        return SimpleUploadedFile(name, output.getvalue(), content_type="image/jpeg")

    @patch("apps.verification.storage._s3_client")
    def test_upload_writes_private_object_and_records_metadata_and_event(self, get_client):
        client = get_client.return_value

        evidence = store_verification_evidence(
            check=self.check,
            uploaded_file=self._jpeg_upload("folder\\\\identity.jpg"),
            actor=self.actor,
            source=DriverVerificationEvidence.Source.DRIVER_UPLOAD,
        )

        client.put_object.assert_called_once()
        upload_args = client.put_object.call_args.kwargs
        self.assertEqual(upload_args["Bucket"], "divs-private-evidence")
        self.assertTrue(upload_args["Key"].startswith("verification-evidence/"))
        self.assertEqual(upload_args["ContentType"], "image/jpeg")
        self.assertEqual(len(upload_args["Metadata"]["sha256"]), 64)
        self.assertEqual(evidence.storage_key, upload_args["Key"])
        self.assertEqual(evidence.original_filename, "identity.jpg")
        self.assertEqual(evidence.status, DriverVerificationEvidence.Status.SUBMITTED)
        self.assertEqual(evidence.scan_status, DriverVerificationEvidence.ScanStatus.PENDING)
        self.assertTrue(
            DriverVerificationEvidenceEvent.objects.filter(
                evidence=evidence,
                event_type="uploaded",
                new_status=DriverVerificationEvidence.Status.SUBMITTED,
            ).exists()
        )

    @patch("apps.verification.storage._s3_client")
    def test_retrieval_rejects_keys_outside_private_evidence_prefix(self, get_client):
        for key in (
            "other-prefix/private-object",
            "../verification-evidence/object",
            "verification-evidence/../other-object",
            "verification-evidence\\\\outside",
        ):
            evidence = type(
                "EvidenceStub",
                (),
                {
                    "storage_key": key,
                    "content_type": "image/jpeg",
                    "original_filename": "identity.jpg",
                    "scan_status": DriverVerificationEvidence.ScanStatus.CLEAN,
                    "storage_deleted_at": None,
                    "status": DriverVerificationEvidence.Status.SUBMITTED,
                },
            )()
            with self.subTest(key=key):
                with self.assertRaises(EvidenceStorageError):
                    retrieve_verification_evidence(evidence)

        get_client.assert_not_called()


    @patch("apps.verification.storage._s3_client")
    def test_retrieval_refuses_pending_or_failed_scan_without_contacting_r2(self, get_client):
        for scan_status in (
            DriverVerificationEvidence.ScanStatus.PENDING,
            DriverVerificationEvidence.ScanStatus.ERROR,
            DriverVerificationEvidence.ScanStatus.INFECTED,
        ):
            evidence = type(
                "EvidenceStub",
                (),
                {
                    "storage_key": "verification-evidence/private-object",
                    "content_type": "image/jpeg",
                    "original_filename": "identity.jpg",
                    "scan_status": scan_status,
                    "storage_deleted_at": None,
                    "status": DriverVerificationEvidence.Status.SUBMITTED,
                },
            )()
            with self.subTest(scan_status=scan_status):
                with self.assertRaises(EvidenceStorageError):
                    retrieve_verification_evidence(evidence)

        get_client.assert_not_called()

    @patch("apps.verification.storage._s3_client")
    def test_retrieval_refuses_expired_timestamp_before_contacting_r2(self, get_client):
        evidence = type(
            "EvidenceStub",
            (),
            {
                "storage_key": "verification-evidence/expired-object",
                "content_type": "image/jpeg",
                "original_filename": "identity.jpg",
                "scan_status": DriverVerificationEvidence.ScanStatus.CLEAN,
                "storage_deleted_at": None,
                "status": DriverVerificationEvidence.Status.ACCEPTED,
                "expires_at": timezone.now() - timedelta(seconds=1),
            },
        )()
        with self.assertRaises(EvidenceStorageError):
            retrieve_verification_evidence(evidence)
        get_client.assert_not_called()

    @patch("apps.verification.storage._s3_client")
    def test_retrieval_reads_object_using_private_storage_key(self, get_client):
        body = io.BytesIO(b"private evidence bytes")
        get_client.return_value.get_object.return_value = {"Body": body}
        evidence = type(
            "EvidenceStub",
            (),
            {
                "storage_key": "verification-evidence/private-object",
                "content_type": "image/jpeg",
                "original_filename": "identity.jpg",
                "scan_status": DriverVerificationEvidence.ScanStatus.CLEAN,
                "storage_deleted_at": None,
                "status": DriverVerificationEvidence.Status.SUBMITTED,
            },
        )()

        returned_body, content_type, filename = retrieve_verification_evidence(evidence)

        self.assertEqual(returned_body.read(), b"private evidence bytes")
        self.assertEqual(content_type, "image/jpeg")
        self.assertEqual(filename, "identity.jpg")
        get_client.return_value.get_object.assert_called_once_with(
            Bucket="divs-private-evidence",
            Key="verification-evidence/private-object",
        )

    @patch(
        "apps.verification.models.DriverVerificationEvidenceEvent.objects.create",
        side_effect=RuntimeError("simulated database write failure"),
    )
    @patch("apps.verification.storage._s3_client")
    def test_database_failure_removes_uploaded_r2_object(self, get_client, _event_create):
        client = get_client.return_value

        with self.assertRaisesRegex(RuntimeError, "simulated database write failure"):
            store_verification_evidence(
                check=self.check,
                uploaded_file=self._jpeg_upload(),
                actor=self.actor,
                source=DriverVerificationEvidence.Source.DRIVER_UPLOAD,
            )

        client.put_object.assert_called_once()
        client.delete_object.assert_called_once()
        self.assertFalse(
            DriverVerificationEvidence.objects.filter(
                verification_check=self.check,
            ).exists()
        )
