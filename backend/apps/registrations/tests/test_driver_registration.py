from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.identity.models import Account
from apps.registrations.models import DriverRegistration


class DriverRegistrationAPITests(APITestCase):
    def setUp(self):
        self.account = Account.objects.create_user(
            email="driver@example.com",
            phone_number="+255700000001",
            password="StrongPassword123!",
        )
        self.client.force_authenticate(user=self.account)
        self.url = reverse("registrations:driver")
        self.valid_payload = {
            "first_name": "Amani",
            "middle_name": "Juma",
            "last_name": "Mashauri",
            "nationality": "Tanzanian",
            "region": "Dar es Salaam",
            "district": "Kinondoni",
            "current_residential_address": "Mikocheni, near the main road",
            "driving_experience": "1_to_3_years",
        }

    def test_authenticated_driver_can_create_registration(self):
        response = self.client.post(self.url, self.valid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DriverRegistration.objects.count(), 1)
        self.assertEqual(response.data["contact_email"], self.account.email)
        self.assertEqual(response.data["contact_phone_number"], self.account.phone_number)
        self.assertNotIn("verification_status", response.data)

    def test_registration_requires_required_fields(self):
        payload = {**self.valid_payload}
        payload.pop("district")
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("district", response.data)
        self.assertEqual(DriverRegistration.objects.count(), 0)

    def test_middle_name_is_optional(self):
        payload = {**self.valid_payload}
        payload.pop("middle_name")
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["middle_name"], "")

    def test_registration_cannot_set_contact_details(self):
        payload = {**self.valid_payload, "contact_email": "attacker@example.com", "contact_phone_number": "+255700000099"}
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["contact_email"], self.account.email)
        self.assertEqual(response.data["contact_phone_number"], self.account.phone_number)

    def test_account_cannot_create_two_registrations(self):
        self.client.post(self.url, self.valid_payload, format="json")
        response = self.client.post(self.url, self.valid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(DriverRegistration.objects.count(), 1)

    def test_driver_can_retrieve_and_update_own_registration(self):
        self.client.post(self.url, self.valid_payload, format="json")
        get_response = self.client.get(self.url)
        patch_response = self.client.patch(
            self.url,
            {"current_residential_address": "New current residential address"},
            format="json",
        )
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_response.data["current_residential_address"], "New current residential address")

    def test_registration_endpoint_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.url, self.valid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
