from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.identity.models import Account
from apps.registrations.models import ClientRegistration, DriverRegistration


class ClientRegistrationAPITests(APITestCase):
    def setUp(self):
        self.account = Account.objects.create_user(
            email="client@example.com",
            phone_number="+255700000002",
            password="StrongPassword123!",
        )
        self.client.force_authenticate(user=self.account)
        self.url = reverse("registrations:client")
        self.valid_payload = {
            "client_type": "individual",
            "name": "Neema Mushi",
            "primary_contact": "+255700000002",
            "email": "neema@example.com",
            "country": "Tanzania",
            "region": "Dar es Salaam",
            "alternative_contacts": ["+255700000003", "office@example.com"],
        }

    def test_authenticated_account_can_register_as_individual_client(self):
        response = self.client.post(self.url, self.valid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ClientRegistration.objects.count(), 1)
        self.assertEqual(response.data["client_type"], "individual")
        self.assertEqual(response.data["name"], "Neema Mushi")
        self.assertEqual(response.data["alternative_contacts"], self.valid_payload["alternative_contacts"])

    def test_company_client_registration_is_supported(self):
        payload = {
            **self.valid_payload,
            "client_type": "company",
            "name": "Mlimani Transport Ltd",
        }
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["client_type"], "company")
        self.assertEqual(response.data["name"], "Mlimani Transport Ltd")

    def test_required_fields_are_validated(self):
        payload = {**self.valid_payload}
        payload.pop("region")
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("region", response.data)
        self.assertEqual(ClientRegistration.objects.count(), 0)

    def test_invalid_client_type_is_rejected(self):
        payload = {**self.valid_payload, "client_type": "government"}
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_account_cannot_create_two_client_registrations(self):
        self.client.post(self.url, self.valid_payload, format="json")
        response = self.client.post(self.url, self.valid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(ClientRegistration.objects.count(), 1)

    def test_client_can_retrieve_and_update_own_registration(self):
        self.client.post(self.url, self.valid_payload, format="json")
        get_response = self.client.get(self.url)
        patch_response = self.client.patch(
            self.url, {"region": "Arusha"}, format="json"
        )
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_response.data["region"], "Arusha")

    def test_client_registration_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.url, self.valid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_same_account_can_register_as_driver_and_client(self):
        DriverRegistration.objects.create(
            account=self.account,
            first_name="Neema",
            middle_name="",
            last_name="Mushi",
            nationality="Tanzanian",
            region="Dar es Salaam",
            district="Kinondoni",
            current_residential_address="Mikocheni",
            driving_experience="none",
        )
        response = self.client.post(self.url, self.valid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            ClientRegistration.objects.filter(account=self.account).exists()
        )

    def test_alternative_contacts_must_not_be_blank(self):
        payload = {**self.valid_payload, "alternative_contacts": ["", "   "]}
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
