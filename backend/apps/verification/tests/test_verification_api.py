from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.identity.models import Account
from apps.notifications.models import Notification
from apps.operations.models import OperationsMembership
from apps.profiles.models import DriverProfile, OperationsProfile
from apps.registrations.models import DriverRegistration
from apps.verification.models import DriverVerification, DriverVerificationCheck


class DriverVerificationAPITests(APITestCase):
    def setUp(self):
        self.driver = Account.objects.create_user(
            email="driver@example.com", password="StrongPassword123!"
        )
        registration = DriverRegistration.objects.create(
            account=self.driver,
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
        self.verification = self.profile.verification
        self.url = reverse("verification:driver-me")

    def test_driver_can_read_only_their_check_progress(self):
        self.client.force_authenticate(user=self.driver)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], DriverVerification.Status.PENDING)
        self.assertEqual(len(response.data["checks"]), 4)
        self.assertFalse(response.data["is_discoverable"])
        self.assertNotIn("government_response", response.data)
        self.assertNotIn("national_id_number", response.data)

    def test_driver_endpoint_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_client_cannot_read_driver_verification_endpoint(self):
        client_account = Account.objects.create_user(
            email="client@example.com", password="StrongPassword123!"
        )
        self.client.force_authenticate(user=client_account)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class VerificationReviewServiceTests(APITestCase):
    def setUp(self):
        self.reviewer = Account.objects.create_user(
            email="operator@example.com", password="StrongPassword123!"
        )
        admin = Account.objects.create_superuser(
            email="system-admin@example.com", password="StrongPassword123!"
        )
        membership = OperationsMembership.objects.create(
            account=self.reviewer,
            role=OperationsMembership.Role.OPERATOR,
            approved_by=admin,
        )
        OperationsProfile.objects.create(membership=membership)
        driver = Account.objects.create_user(
            email="another-driver@example.com", password="StrongPassword123!"
        )
        registration = DriverRegistration.objects.create(
            account=driver,
            first_name="Neema",
            middle_name="",
            last_name="Kassim",
            nationality="Tanzanian",
            region="Arusha",
            district="Arusha City",
            current_residential_address="Sakina",
            driving_experience="4_to_7_years",
        )
        profile = DriverProfile.objects.create(registration=registration)
        self.verification = profile.verification
        self.checks = list(self.verification.checks.all())

    def test_operations_user_can_record_minimal_manual_check_outcome(self):
        self.client.force_authenticate(user=self.reviewer)
        url = reverse(
            "verification:operations-check-review",
            kwargs={"check_id": self.checks[0].id},
        )
        response = self.client.post(
            url,
            {"status": "passed", "result_code": "clear"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["method"], "manual")
        self.assertEqual(response.data["status"], "passed")

    def test_all_four_passed_checks_approve_verification(self):
        from apps.verification.services import review_driver_check

        result_codes = {
            DriverVerificationCheck.CheckType.NATIONAL_IDENTITY: DriverVerificationCheck.ResultCode.MATCH,
            DriverVerificationCheck.CheckType.DRIVING_LICENCE: DriverVerificationCheck.ResultCode.VALID,
            DriverVerificationCheck.CheckType.TRAFFIC_RECORDS: DriverVerificationCheck.ResultCode.CLEAR,
            DriverVerificationCheck.CheckType.ACCIDENT_RECORDS: DriverVerificationCheck.ResultCode.CLEAR,
        }
        for check in self.checks:
            review_driver_check(
                check_id=check.id,
                reviewer=self.reviewer,
                status=DriverVerificationCheck.Status.PASSED,
                result_code=result_codes[check.check_type],
            )
        self.verification.refresh_from_db()
        self.assertEqual(self.verification.status, DriverVerification.Status.APPROVED)
        self.assertTrue(self.verification.is_discoverable)

    def test_failed_check_rejects_verification(self):
        from apps.verification.services import review_driver_check

        review_driver_check(
            check_id=self.checks[0].id,
            reviewer=self.reviewer,
            status=DriverVerificationCheck.Status.FAILED,
            result_code=DriverVerificationCheck.ResultCode.RECORD_FOUND,
        )
        self.verification.refresh_from_db()
        self.assertEqual(self.verification.status, DriverVerification.Status.REJECTED)
        self.assertFalse(self.verification.is_discoverable)
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.verification.profile.registration.account,
                recipient_role=Notification.RecipientRole.DRIVER,
                event_type="driver.verification.rejected",
            ).exists()
        )
