from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.identity.models import Account
from apps.performance.models import AvailabilityRestriction, DriverScore
from apps.profiles.models import DriverProfile
from apps.registrations.models import DriverRegistration
from apps.verification.models import DriverVerificationCheck
from apps.verification.services import record_verified_licence_classes, review_driver_check


class PublicDriverDiscoveryTests(APITestCase):
    def setUp(self):
        self.reviewer = Account.objects.create_user(
            email="reviewer@example.com", password="StrongPassword123!"
        )
        self.url = reverse("discovery:public-drivers")

    def _create_verified_driver(self, email, score=80, area="Mikocheni"):
        account = Account.objects.create_user(email=email, password="StrongPassword123!")
        registration = DriverRegistration.objects.create(
            account=account,
            first_name="Amani",
            middle_name="",
            last_name=email.split("@")[0].title(),
            nationality="Tanzanian",
            region="Dar es Salaam",
            district="Kinondoni",
            residential_area=area,
            current_residential_address="Private full address not for public search",
            driving_experience="4_to_7_years",
        )
        profile = DriverProfile.objects.create(registration=registration)
        result_codes = {
            DriverVerificationCheck.CheckType.NATIONAL_IDENTITY: DriverVerificationCheck.ResultCode.MATCH,
            DriverVerificationCheck.CheckType.DRIVING_LICENCE: DriverVerificationCheck.ResultCode.VALID,
            DriverVerificationCheck.CheckType.TRAFFIC_RECORDS: DriverVerificationCheck.ResultCode.CLEAR,
            DriverVerificationCheck.CheckType.ACCIDENT_RECORDS: DriverVerificationCheck.ResultCode.CLEAR,
        }
        checks = list(profile.verification.checks.all())
        for check in checks:
            review_driver_check(
                check_id=check.id,
                reviewer=self.reviewer,
                status=DriverVerificationCheck.Status.PASSED,
                result_code=result_codes[check.check_type],
            )
        licence_check = next(
            check for check in checks
            if check.check_type == DriverVerificationCheck.CheckType.DRIVING_LICENCE
        )
        record_verified_licence_classes(
            check_id=licence_check.id, reviewer=self.reviewer, licence_classes=["C"]
        )
        if score is not None:
            DriverScore.objects.create(driver=profile, calculated_score=score)
        return profile

    def test_public_search_does_not_require_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

    def test_verified_classes_filter_and_safe_fields(self):
        self._create_verified_driver("driver-one@example.com", score=91)
        response = self.client.get(self.url, {"licence_class": "c", "residential_area": "miko"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        driver = response.data["results"][0]
        self.assertEqual(driver["verified_licence_classes"], ["C"])
        self.assertEqual(driver["performance_score"], 91)
        self.assertNotIn("current_residential_address", driver)
        self.assertNotIn("contact_phone_number", driver)

    def test_scored_drivers_rank_before_unscored_drivers(self):
        self._create_verified_driver("unscored@example.com", score=None)
        self._create_verified_driver("scored@example.com", score=40)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["performance_score"], 40)
        self.assertIsNone(response.data["results"][1]["performance_score"])

    def test_active_restriction_excludes_driver_from_available_results(self):
        profile = self._create_verified_driver("restricted@example.com", score=95)
        AvailabilityRestriction.objects.create(
            driver=profile,
            kind=AvailabilityRestriction.Kind.CRITICAL_INCIDENT,
            reason="Precautionary review",
            created_by=self.reviewer,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)
