import re
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.identity.models import ExternalIdentity, VerificationCode

Account = get_user_model()
PASSWORD = "Long-Unique-Password-987!"


class IdentityFoundationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_account_can_use_email_without_username(self):
        account = Account.objects.create_user(
            email="Person@Example.com",
            password=PASSWORD,
        )
        self.assertEqual(account.email, "person@example.com")
        self.assertIsNone(account.phone_number)
        self.assertFalse(account.email_verified)

    def test_account_can_use_phone_without_email(self):
        account = Account.objects.create_user(
            phone_number="+255712345678",
            password=PASSWORD,
        )
        self.assertIsNone(account.email)
        self.assertEqual(account.phone_number, "+255712345678")
        self.assertFalse(account.phone_verified)

    def test_account_requires_email_or_phone(self):
        with self.assertRaises(ValueError):
            Account.objects.create_user(password=PASSWORD)

    def test_email_login_requires_verified_email(self):
        account = Account.objects.create_user(
            email="person@example.com",
            password=PASSWORD,
            email_verified=False,
        )
        response = self.client.post(
            "/api/v1/auth/token/",
            {"identifier": account.email, "password": PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_verified_email_password_login_returns_jwt(self):
        account = Account.objects.create_user(
            email="person@example.com",
            password=PASSWORD,
            email_verified=True,
        )
        response = self.client.post(
            "/api/v1/auth/token/",
            {"identifier": account.email, "password": PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_verified_phone_password_login_returns_jwt(self):
        account = Account.objects.create_user(
            phone_number="+255712345678",
            password=PASSWORD,
            phone_verified=True,
        )
        response = self.client.post(
            "/api/v1/auth/token/",
            {"identifier": account.phone_number, "password": PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)

    def test_unverified_phone_cannot_login(self):
        account = Account.objects.create_user(
            phone_number="+255712345678",
            password=PASSWORD,
            phone_verified=False,
        )
        response = self.client.post(
            "/api/v1/auth/token/",
            {"identifier": account.phone_number, "password": PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_account_uses_uuid_primary_key(self):
        account = Account.objects.create_user(
            email="uuid@example.com",
            password=PASSWORD,
        )
        self.assertEqual(account.id.version, 4)

    def test_google_identity_subject_is_unique_per_provider(self):
        account = Account.objects.create_user(email="google@example.com", password=PASSWORD)
        ExternalIdentity.objects.create(
            account=account,
            provider=ExternalIdentity.Provider.GOOGLE,
            subject="google-subject-123",
            provider_email="google@example.com",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ExternalIdentity.objects.create(
                    account=account,
                    provider=ExternalIdentity.Provider.GOOGLE,
                    subject="google-subject-123",
                    provider_email="google@example.com",
                )

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_email_verification_code_is_sent_and_can_be_confirmed(self):
        account = Account.objects.create_user(email="verify@example.com", password=PASSWORD)
        response = self.client.post(
            "/api/v1/auth/verification/request/",
            {"channel": "email", "email": account.email},
            format="json",
        )
        self.assertEqual(response.status_code, 202)
        self.assertEqual(len(mail.outbox), 1)
        code = re.search(r"\b(\d{6})\b", mail.outbox[0].body).group(1)

        response = self.client.post(
            "/api/v1/auth/verification/confirm/",
            {"channel": "email", "email": account.email, "code": code},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        account.refresh_from_db()
        self.assertTrue(account.email_verified)

    def test_wrong_verification_code_counts_toward_attempt_limit(self):
        record = VerificationCode.objects.create(
            channel=VerificationCode.Channel.EMAIL,
            target="attempts@example.com",
            code_hash=make_password("654321"),
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        for _ in range(5):
            response = self.client.post(
                "/api/v1/auth/verification/confirm/",
                {"channel": "email", "email": record.target, "code": "123456"},
                format="json",
            )
            self.assertEqual(response.status_code, 400)
        record.refresh_from_db()
        self.assertEqual(record.attempts, 5)
