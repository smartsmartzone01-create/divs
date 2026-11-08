from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.verification.services import process_expired_verification_evidence


class Command(BaseCommand):
    help = (
        "Expire accepted verification evidence and reopen any manual checks "
        "that no longer have valid supporting evidence."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--execute",
            action="store_true",
            help="Apply expiry and verification changes. Without this flag, run a dry run.",
        )

    def handle(self, *args, **options):
        now = timezone.now()
        result = process_expired_verification_evidence(
            now=now,
            dry_run=not options["execute"],
        )
        if result["dry_run"]:
            self.stdout.write(self.style.WARNING(
                "DRY RUN: "
                f"{result['evidence_expired']} accepted evidence record(s) are due; "
                f"{result['checks_to_reopen']} manual check(s) would be reopened; "
                f"{result['profiles_to_deactivate']} active profile(s) would be deactivated. "
                "No changes were made. Re-run with --execute to apply."
            ))
            return

        self.stdout.write(self.style.SUCCESS(
            "Expiry processing complete: "
            f"{result['evidence_expired']} evidence record(s) expired; "
            f"{result['checks_reopened']} check(s) reopened; "
            f"{result['verifications_reopened']} verification(s) returned to review; "
            f"{result['profiles_deactivated']} active profile(s) deactivated."
        ))
