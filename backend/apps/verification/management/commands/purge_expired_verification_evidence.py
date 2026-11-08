from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.verification.models import (
    DriverVerificationEvidence,
    DriverVerificationEvidenceEvent,
)
from apps.verification.storage import _s3_client
from django.conf import settings


class Command(BaseCommand):
    help = (
        "Remove private files only when evidence has an explicit expiry, "
        "is marked expired, and is not under legal hold. Metadata and audit "
        "history are retained."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--execute",
            action="store_true",
            help="Perform deletion. Without this flag, the command is a dry run.",
        )

    def handle(self, *args, **options):
        if not settings.R2_EVIDENCE_STORAGE_ENABLED:
            raise CommandError("Private evidence storage is not configured.")

        now = timezone.now()
        eligible = DriverVerificationEvidence.objects.filter(
            status=DriverVerificationEvidence.Status.EXPIRED,
            expires_at__isnull=False,
            expires_at__lte=now,
            legal_hold=False,
            storage_deleted_at__isnull=True,
        ).exclude(storage_key="").order_by("expires_at")

        if not options["execute"]:
            count = eligible.count()
            self.stdout.write(
                self.style.WARNING(
                    f"DRY RUN: {count} expired evidence file(s) are eligible. "
                    "No objects were deleted. Re-run with --execute to proceed."
                )
            )
            return

        client = _s3_client()
        deleted = 0
        for candidate in eligible.values_list("pk", flat=True).iterator():
            try:
                with transaction.atomic():
                    evidence = (
                        DriverVerificationEvidence.objects.select_for_update()
                        .filter(pk=candidate)
                        .first()
                    )
                    if (
                        evidence is None
                        or evidence.status != DriverVerificationEvidence.Status.EXPIRED
                        or evidence.expires_at is None
                        or evidence.expires_at > timezone.now()
                        or evidence.legal_hold
                        or evidence.storage_deleted_at is not None
                        or not evidence.storage_key
                    ):
                        continue

                    object_key = evidence.storage_key
                    client.delete_object(
                        Bucket=settings.R2_BUCKET_NAME,
                        Key=object_key,
                    )
                    evidence.storage_key = ""
                    evidence.storage_deleted_at = timezone.now()
                    evidence.save(
                        update_fields=["storage_key", "storage_deleted_at", "updated_at"]
                    )
                    DriverVerificationEvidenceEvent.objects.create(
                        evidence=evidence,
                        event_type="retention_file_deleted",
                        previous_status=evidence.status,
                        new_status=evidence.status,
                        notes="Private file deleted after explicit expiry; evidence metadata and audit history retained.",
                    )
                    deleted += 1
            except Exception as exc:
                raise CommandError(
                    f"Retention cleanup stopped while processing evidence {candidate}. "
                    "Earlier deletions may have completed; rerun safely after resolving the error."
                ) from exc

        self.stdout.write(self.style.SUCCESS(
            f"Retention cleanup complete. Deleted {deleted} private file(s); metadata retained."
        ))
