from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.identity.models import Account


class AccountRegistrationAPITests(APITestCase):
    def setUp(self):
        self.url = reverse("identity:register")

    def test_account_can_register_with_email_and_password(self):
        response = self.client.post(
            self.url,
            {
                "email": "person@example.com",
                "password": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        account = Account.objects.get(email="person@example.com")
        self.assertEqual(response.data["id"], str(account.id))
        self.assertFalse(account.email_verified)
        self.assertNotIn("password", response.data)

    def test_account_can_register_with_phone_and_password(self):
        response = self.client.post(
            self.url,
            {
                "phone_number": "+255700000010",
                "password": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Account.objects.filter(phone_number="+255700000010").exists())

    def test_registration_requires_email_or_phone(self):
        response = self.client.post(
            self.url,
            {"password": "StrongPassword123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Account.objects.count(), 0)

    def test_duplicate_email_is_rejected(self):
        Account.objects.create_user(
            email="person@example.com",
            password="StrongPassword123!",
        )

        response = self.client.post(
            self.url,
            {
                "email": "person@example.com",
                "password": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Account.objects.count(), 1)
