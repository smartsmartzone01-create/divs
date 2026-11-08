from datetime import timedelta
from unittest.mock import patch

from django.core.management import call_command, CommandError
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.identity.models import Account
from apps.registrations.models import DriverRegistration
from apps.profiles.models import DriverProfile
from apps.verification.models import DriverVerificationEvidence


@override_settings(
    R2_EVIDENCE_STORAGE_ENABLED=True,
    R2_BUCKET_NAME="divs-private-evidence",
)
class EvidenceReconciliationCommandTests(TestCase):
    def setUp(self):
        self.actor = Account.objects.create_user(
            email="reconcile-driver@example.com",
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
        self.check = DriverProfile.objects.create(registration=registration).verification.checks.first()

    def _evidence(self, key):
        return DriverVerificationEvidence.objects.create(
            verification_check=self.check,
            evidence_type=self.check.check_type,
            source=DriverVerificationEvidence.Source.DRIVER_UPLOAD,
            original_filename="identity.jpg",
            content_type="image/jpeg",
            file_size=4,
            sha256="a" * 64,
            storage_key=key,
            uploaded_by=self.actor,
        )

    @patch("apps.verification.management.commands.reconcile_verification_evidence._s3_client")
    def test_deletes_only_old_unreferenced_objects_under_evidence_prefix(self, get_client):
        old = timezone.now() - timedelta(hours=48)
        recent = timezone.now() - timedelta(hours=2)
        get_client.return_value.get_paginator.return_value.paginate.return_value = [
            {
                "Contents": [
                    {"Key": "verification-evidence/orphan", "LastModified": old},
                    {"Key": "verification-evidence/linked", "LastModified": old},
                    {"Key": "verification-evidence/recent", "LastModified": recent},
                    {"Key": "other-prefix/object", "LastModified": old},
                ]
            }
        ]
        self._evidence("verification-evidence/linked")

        call_command("reconcile_verification_evidence")

        get_client.return_value.delete_object.assert_called_once_with(
            Bucket="divs-private-evidence",
            Key="verification-evidence/orphan",
        )

    @patch("apps.verification.management.commands.reconcile_verification_evidence._s3_client")
    def test_dry_run_does_not_delete_orphaned_objects(self, get_client):
        old = timezone.now() - timedelta(hours=48)
        get_client.return_value.get_paginator.return_value.paginate.return_value = [
            {"Contents": [{"Key": "verification-evidence/orphan", "LastModified": old}]}
        ]

        call_command("reconcile_verification_evidence", "--dry-run")

        get_client.return_value.delete_object.assert_not_called()

    @patch("apps.verification.management.commands.reconcile_verification_evidence._s3_client")
    def test_database_error_stops_reconciliation_without_deleting(self, get_client):
        old = timezone.now() - timedelta(hours=48)
        get_client.return_value.get_paginator.return_value.paginate.return_value = [
            {"Contents": [{"Key": "verification-evidence/orphan", "LastModified": old}]}
        ]
        with patch(
            "apps.verification.management.commands.reconcile_verification_evidence.DriverVerificationEvidence.objects.filter",
            side_effect=RuntimeError("database unavailable"),
        ):
            with self.assertRaises(CommandError):
                call_command("reconcile_verification_evidence")

        get_client.return_value.delete_object.assert_not_called()

    @patch("apps.verification.management.commands.reconcile_verification_evidence._s3_client")
    def test_rejects_zero_age_threshold(self, get_client):
        with self.assertRaises(CommandError):
            call_command("reconcile_verification_evidence", "--minimum-age-hours=0")
        get_client.assert_not_called()
