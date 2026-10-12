from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.identity.models import Account
from apps.profiles.models import ClientProfile
from apps.registrations.models import ClientRegistration


class ClientProfileAPITests(APITestCase):
    def setUp(self):
        self.account = Account.objects.create_user(
            email="client@example.com",
            phone_number="+255700000030",
            password="StrongPassword123!",
        )
        self.registration = ClientRegistration.objects.create(
            account=self.account,
            client_type=ClientRegistration.ClientType.COMPANY,
            name="Mwangaza Transport Ltd",
            primary_contact="+255700000031",
            email="office@mwangaza.example",
            country="Tanzania",
            region="Dar es Salaam",
            alternative_contacts=["+255700000032", "fleet@mwangaza.example"],
        )
        self.profile = ClientProfile.objects.create(registration=self.registration)
        self.url = reverse("profiles:client")
        self.client.force_authenticate(user=self.account)

    def test_client_can_retrieve_profile_with_registration_details(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data["id"]), str(self.profile.id))
        self.assertEqual(response.data["status"], ClientProfile.Status.ACTIVE)
        self.assertEqual(response.data["registration"]["client_type"], "company")
        self.assertEqual(response.data["registration"]["name"], "Mwangaza Transport Ltd")
        self.assertEqual(response.data["registration"]["primary_contact"], "+255700000031")
        self.assertEqual(response.data["registration"]["email"], "office@mwangaza.example")
        self.assertEqual(response.data["registration"]["country"], "Tanzania")
        self.assertEqual(response.data["registration"]["region"], "Dar es Salaam")
        self.assertEqual(
            response.data["registration"]["alternative_contacts"],
            ["+255700000032", "fleet@mwangaza.example"],
        )
        self.assertIn("created_at", response.data["registration"])
        self.assertIn("updated_at", response.data["registration"])
        self.assertIn("created_at", response.data)
        self.assertIn("updated_at", response.data)
        self.assertNotIn("verification_status", response.data)

    def test_profile_endpoint_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_account_without_client_profile_is_denied(self):
        account = Account.objects.create_user(
            email="ordinary@example.com",
            password="StrongPassword123!",
        )
        self.client.force_authenticate(user=account)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_suspended_client_profile_is_denied(self):
        self.profile.status = ClientProfile.Status.SUSPENDED
        self.profile.save(update_fields=["status", "updated_at"])

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_account_only_receives_its_own_profile(self):
        other_account = Account.objects.create_user(
            email="other-client@example.com",
            password="StrongPassword123!",
        )
        other_registration = ClientRegistration.objects.create(
            account=other_account,
            client_type=ClientRegistration.ClientType.INDIVIDUAL,
            name="Neema Kassim",
            primary_contact="+255700000040",
            email="neema@example.com",
            country="Tanzania",
            region="Arusha",
        )
        ClientProfile.objects.create(registration=other_registration)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data["id"]), str(self.profile.id))
        self.assertEqual(
            response.data["registration"]["name"],
            "Mwangaza Transport Ltd",
        )
        self.assertNotEqual(
            response.data["registration"]["name"],
            "Neema Kassim",
        )

    def test_profile_endpoint_is_read_only(self):
        response = self.client.patch(self.url, {"status": "suspended"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.status, ClientProfile.Status.ACTIVE)
