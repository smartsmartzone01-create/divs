from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.identity.models import ExternalIdentity

Account = get_user_model()


class IdentityFoundationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_registration_normalizes_email_and_does_not_mark_it_verified(self):
        response = self.client.post(
            "/api/v1/auth/register/",
            {
                "email": "Driver.Example@Example.com",
                "username": "driver_example",
                "password": "Long-Unique-Password-987!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        account = Account.objects.get(username="driver_example")
        self.assertEqual(account.email, "driver.example@example.com")
        self.assertFalse(account.email_verified)

    def test_email_password_login_returns_jwt(self):
        Account.objects.create_user(
            email="person@example.com",
            username="person",
            password="Long-Unique-Password-987!",
        )
        response = self.client.post(
            "/api/v1/auth/token/",
            {"email": "person@example.com", "password": "Long-Unique-Password-987!"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_account_uses_uuid_primary_key(self):
        account = Account.objects.create_user(
            email="uuid@example.com",
            username="uuid_person",
            password="Long-Unique-Password-987!",
        )
        self.assertEqual(account.id.version, 4)

    def test_google_identity_subject_is_unique_per_provider(self):
        account = Account.objects.create_user(
            email="google@example.com",
            username="google_person",
            password="Long-Unique-Password-987!",
        )
        ExternalIdentity.objects.create(
            account=account,
            provider=ExternalIdentity.Provider.GOOGLE,
            subject="google-subject-123",
            provider_email="google@example.com",
        )
        self.assertEqual(
            ExternalIdentity.objects.filter(
                provider=ExternalIdentity.Provider.GOOGLE,
                subject="google-subject-123",
            ).count(),
            1,
        )
