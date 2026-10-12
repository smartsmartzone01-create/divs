from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.identity.models import Account
from apps.profiles.models import DriverProfile
from apps.registrations.models import DriverRegistration


class DriverProfileAPITests(APITestCase):
    def setUp(self):
        self.account = Account.objects.create_user(
            email="driver@example.com",
            phone_number="+255700000001",
            password="StrongPassword123!",
        )
        self.registration = DriverRegistration.objects.create(
            account=self.account,
            first_name="Amani",
            middle_name="Juma",
            last_name="Mashauri",
            nationality="Tanzanian",
            region="Dar es Salaam",
            district="Kinondoni",
            current_residential_address="Mikocheni, near the main road",
            driving_experience="1_to_3_years",
        )
        self.profile = DriverProfile.objects.create(registration=self.registration)
        self.url = reverse("profiles:driver")
        self.client.force_authenticate(user=self.account)

    def test_driver_can_retrieve_profile_with_registration_information(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data["id"]), str(self.profile.id))
        self.assertEqual(response.data["status"], DriverProfile.Status.ACTIVE)
        self.assertEqual(response.data["registration"]["first_name"], "Amani")
        self.assertEqual(response.data["registration"]["middle_name"], "Juma")
        self.assertEqual(response.data["registration"]["last_name"], "Mashauri")
        self.assertEqual(response.data["registration"]["nationality"], "Tanzanian")
        self.assertEqual(response.data["registration"]["region"], "Dar es Salaam")
        self.assertEqual(response.data["registration"]["district"], "Kinondoni")
        self.assertEqual(
            response.data["registration"]["current_residential_address"],
            "Mikocheni, near the main road",
        )
        self.assertEqual(response.data["registration"]["driving_experience"], "1_to_3_years")
        self.assertEqual(response.data["registration"]["contact_email"], self.account.email)
        self.assertEqual(
            response.data["registration"]["contact_phone_number"],
            self.account.phone_number,
        )
        self.assertIn("created_at", response.data)
        self.assertIn("updated_at", response.data)
        self.assertNotIn("verification_status", response.data)
        self.assertNotIn("work_eligibility", response.data)

    def test_profile_endpoint_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_account_without_driver_profile_is_denied(self):
        other_account = Account.objects.create_user(
            email="client@example.com",
            password="StrongPassword123!",
        )
        self.client.force_authenticate(user=other_account)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_suspended_driver_profile_is_denied(self):
        self.profile.status = DriverProfile.Status.SUSPENDED
        self.profile.save(update_fields=["status", "updated_at"])

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_account_only_receives_its_own_profile(self):
        other_account = Account.objects.create_user(
            email="other-driver@example.com",
            password="StrongPassword123!",
        )
        other_registration = DriverRegistration.objects.create(
            account=other_account,
            first_name="Neema",
            middle_name="",
            last_name="Kassim",
            nationality="Tanzanian",
            region="Arusha",
            district="Arusha City",
            current_residential_address="Sakina",
            driving_experience="4_to_7_years",
        )
        DriverProfile.objects.create(registration=other_registration)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data["id"]), str(self.profile.id))
        self.assertEqual(response.data["registration"]["first_name"], "Amani")
        self.assertNotEqual(response.data["registration"]["first_name"], "Neema")
