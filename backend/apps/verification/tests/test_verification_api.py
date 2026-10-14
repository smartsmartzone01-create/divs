from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.identity.models import Account
from apps.notifications.models import Notification
from apps.operations.models import OperationsMembership
from apps.profiles.models import DriverProfile, OperationsProfile
from apps.registrations.models import DriverRegistration
from apps.verification.models import DriverVerification, DriverVerificationCheck
from apps.verification.services import record_verified_licence_classes, review_driver_check


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

    def _pass_all_checks(self):
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

    def test_all_checks_and_validated_licence_class_are_required_for_discovery(self):
        self._pass_all_checks()
        self.verification.refresh_from_db()
        self.assertEqual(self.verification.status, DriverVerification.Status.APPROVED)
        self.assertFalse(self.verification.is_discoverable)

        licence_check = next(
            check for check in self.checks
            if check.check_type == DriverVerificationCheck.CheckType.DRIVING_LICENCE
        )
        record_verified_licence_classes(
            check_id=licence_check.id,
            reviewer=self.reviewer,
            licence_classes=["C", "CE"],
        )
        self.assertTrue(self.verification.is_discoverable)

    def test_licence_classes_cannot_be_recorded_before_validation(self):
        licence_check = next(
            check for check in self.checks
            if check.check_type == DriverVerificationCheck.CheckType.DRIVING_LICENCE
        )
        with self.assertRaisesMessage(Exception, "only be recorded after"):
            record_verified_licence_classes(
                check_id=licence_check.id,
                reviewer=self.reviewer,
                licence_classes=["C"],
            )

    def test_operations_user_can_record_validated_licence_classes(self):
        self._pass_all_checks()
        licence_check = next(
            check for check in self.checks
            if check.check_type == DriverVerificationCheck.CheckType.DRIVING_LICENCE
        )
        self.client.force_authenticate(user=self.reviewer)
        url = reverse(
            "verification:operations-verified-licence-classes",
            kwargs={"check_id": licence_check.id},
        )
        response = self.client.post(
            url, {"licence_classes": ["C", "CE"]}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [item["licence_class"] for item in response.data], ["C", "CE"]
        )

    def test_invalid_licence_cannot_be_marked_passed(self):
        licence_check = next(
            check for check in self.checks
            if check.check_type == DriverVerificationCheck.CheckType.DRIVING_LICENCE
        )
        with self.assertRaisesMessage(Exception, "invalid licence result must use the failed status"):
            review_driver_check(
                check_id=licence_check.id,
                reviewer=self.reviewer,
                status=DriverVerificationCheck.Status.PASSED,
                result_code=DriverVerificationCheck.ResultCode.INVALID,
            )

    def test_identity_mismatch_cannot_be_marked_passed(self):
        check = next(
            item for item in self.checks
            if item.check_type == DriverVerificationCheck.CheckType.NATIONAL_IDENTITY
        )
        with self.assertRaisesMessage(Exception, "only pass when its result confirms"):
            review_driver_check(
                check_id=check.id,
                reviewer=self.reviewer,
                status=DriverVerificationCheck.Status.PASSED,
                result_code=DriverVerificationCheck.ResultCode.MISMATCH,
            )

    def test_record_found_cannot_be_marked_passed(self):
        check = next(
            item for item in self.checks
            if item.check_type == DriverVerificationCheck.CheckType.TRAFFIC_RECORDS
        )
        with self.assertRaisesMessage(Exception, "only pass when its result confirms"):
            review_driver_check(
                check_id=check.id,
                reviewer=self.reviewer,
                status=DriverVerificationCheck.Status.PASSED,
                result_code=DriverVerificationCheck.ResultCode.RECORD_FOUND,
            )

    def test_check_cannot_pass_without_a_result(self):
        check = next(
            item for item in self.checks
            if item.check_type == DriverVerificationCheck.CheckType.NATIONAL_IDENTITY
        )
        with self.assertRaisesMessage(Exception, "only pass when its result confirms"):
            review_driver_check(
                check_id=check.id,
                reviewer=self.reviewer,
                status=DriverVerificationCheck.Status.PASSED,
                result_code="",
            )

    def test_inconclusive_result_cannot_be_marked_passed(self):
        check = next(
            item for item in self.checks
            if item.check_type == DriverVerificationCheck.CheckType.NATIONAL_IDENTITY
        )
        with self.assertRaisesMessage(Exception, "inconclusive result requires further review"):
            review_driver_check(
                check_id=check.id,
                reviewer=self.reviewer,
                status=DriverVerificationCheck.Status.PASSED,
                result_code=DriverVerificationCheck.ResultCode.INCONCLUSIVE,
            )

    def test_failed_check_rejects_verification(self):
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
