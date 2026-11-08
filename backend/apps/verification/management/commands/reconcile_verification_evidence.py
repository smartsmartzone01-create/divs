from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.verification.models import DriverVerificationEvidence
from apps.verification.storage import _s3_client


class Command(BaseCommand):
    help = (
        "Remove old unreferenced objects from the private verification-evidence "
        "R2 prefix. Objects newer than the grace period are always retained."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--minimum-age-hours",
            type=int,
            default=24,
            help="Minimum object age before an unreferenced object can be deleted (default: 24).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report orphaned objects without deleting them.",
        )

    def handle(self, *args, **options):
        minimum_age_hours = options["minimum_age_hours"]
        if minimum_age_hours < 1:
            raise CommandError("--minimum-age-hours must be at least 1.")

        if not settings.R2_EVIDENCE_STORAGE_ENABLED:
            raise CommandError("Private verification evidence storage is not configured.")

        try:
            client = _s3_client()
            paginator = client.get_paginator("list_objects_v2")
            pages = paginator.paginate(
                Bucket=settings.R2_BUCKET_NAME,
                Prefix="verification-evidence/",
            )
        except Exception as exc:
            raise CommandError("Could not list private verification evidence objects.") from exc

        cutoff = timezone.now() - timedelta(hours=minimum_age_hours)
        inspected = retained = orphaned = deleted = 0

        try:
            for page in pages:
                for item in page.get("Contents", []):
                    key = item.get("Key", "")
                    modified = item.get("LastModified")
                    if not key.startswith("verification-evidence/") or not modified:
                        retained += 1
                        continue

                    inspected += 1
                    if modified >= cutoff:
                        retained += 1
                        continue

                    # A database failure aborts the command; it is never
                    # interpreted as proof that an object is orphaned.
                    if DriverVerificationEvidence.objects.filter(storage_key=key).exists():
                        retained += 1
                        continue

                    orphaned += 1
                    if options["dry_run"]:
                        self.stdout.write(f"DRY RUN orphan: {key}")
                        continue

                    client.delete_object(Bucket=settings.R2_BUCKET_NAME, Key=key)
                    deleted += 1
                    self.stdout.write(f"Deleted orphan: {key}")
        except Exception as exc:
            raise CommandError(
                "Evidence reconciliation stopped safely. Review the error and rerun; "
                "objects already deleted are not restored."
            ) from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"Reconciliation complete. Inspected: {inspected}; retained: {retained}; "
                f"orphaned: {orphaned}; deleted: {deleted}; dry_run: {options['dry_run']}."
            )
        )
