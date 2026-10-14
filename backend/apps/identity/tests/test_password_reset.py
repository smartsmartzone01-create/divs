from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.identity.models import AuthSession, VerificationCode


Account = get_user_model()


class PasswordResetAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.account = Account.objects.create_user(
            email="reset.person@example.com",
            password="Old-Strong-Password-987!",
            email_verified=True,
        )

    @patch("apps.identity.views.password_reset.issue_verification_code")
    def test_reset_request_uses_generic_response(self, issue_code):
        response = self.client.post(
            "/api/v1/auth/password-reset/request/",
            {"email": self.account.email},
            format="json",
        )
        self.assertEqual(response.status_code, 202)
        issue_code.assert_called_once()

    def test_reset_request_does_not_disclose_unknown_email(self):
        response = self.client.post(
            "/api/v1/auth/password-reset/request/",
            {"email": "unknown@example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, 202)
        self.assertEqual(
            response.data["detail"],
            "If an active account with a verified email or phone exists, reset instructions will be sent.",
        )

    def test_reset_requires_password_reset_purpose_code(self):
        VerificationCode.objects.create(
            account=self.account,
            channel=VerificationCode.Channel.EMAIL,
            purpose=VerificationCode.Purpose.IDENTITY_VERIFICATION,
            target=self.account.email,
            code_hash="unused",
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        response = self.client.post(
            "/api/v1/auth/password-reset/confirm/",
            {
                "email": self.account.email,
                "code": "123456",
                "new_password": "New-Strong-Password-987!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    @patch("apps.identity.views.password_reset.verify_code", return_value=True)
    def test_successful_reset_changes_password_and_revokes_sessions(self, verify):
        session = AuthSession.objects.create(
            account=self.account,
            expires_at=timezone.now() + timedelta(days=7),
        )
        response = self.client.post(
            "/api/v1/auth/password-reset/confirm/",
            {
                "email": self.account.email,
                "code": "123456",
                "new_password": "New-Strong-Password-987!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.account.refresh_from_db()
        session.refresh_from_db()
        self.assertTrue(self.account.check_password("New-Strong-Password-987!"))
        self.assertIsNotNone(session.revoked_at)
        verify.assert_called_once()

    @patch("apps.identity.views.password_reset.issue_verification_code")
    def test_verified_phone_can_request_password_reset(self, issue_code):
        phone_account = Account.objects.create_user(
            phone_number="+255712345678",
            password="Old-Phone-Password-987!",
            phone_verified=True,
        )
        response = self.client.post(
            "/api/v1/auth/password-reset/request/",
            {"phone_number": phone_account.phone_number},
            format="json",
        )
        self.assertEqual(response.status_code, 202)
        issue_code.assert_called_once_with(
            VerificationCode.Channel.PHONE,
            phone_account.phone_number,
            account=phone_account,
            purpose=VerificationCode.Purpose.PASSWORD_RESET,
        )

    @patch("apps.identity.views.password_reset.verify_code", return_value=True)
    def test_verified_phone_can_reset_password(self, verify):
        phone_account = Account.objects.create_user(
            phone_number="+255712345678",
            password="Old-Phone-Password-987!",
            phone_verified=True,
        )
        response = self.client.post(
            "/api/v1/auth/password-reset/confirm/",
            {
                "phone_number": phone_account.phone_number,
                "code": "123456",
                "new_password": "New-Phone-Password-987!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        phone_account.refresh_from_db()
        self.assertTrue(phone_account.check_password("New-Phone-Password-987!"))
        verify.assert_called_once_with(
            VerificationCode.Channel.PHONE,
            phone_account.phone_number,
            "123456",
            purpose=VerificationCode.Purpose.PASSWORD_RESET,
        )
