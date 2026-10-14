from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.identity.models import AuthSession, ExternalIdentity


Account = get_user_model()


@override_settings(GOOGLE_OIDC_CLIENT_ID="test-google-client-id")
class GoogleSignInTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/v1/auth/providers/google/sign-in/"

    @patch("apps.identity.views.google.verified_google_claims")
    def test_first_google_sign_in_creates_bare_identity_without_otp(self, verify_claims):
        verify_claims.return_value = ("google-subject-1", "new.person@example.com")

        response = self.client.post(self.url, {"credential": "valid-test-token"}, format="json")

        self.assertEqual(response.status_code, 200)
        account = Account.objects.get(email="new.person@example.com")
        self.assertTrue(account.email_verified)
        self.assertFalse(account.has_usable_password())
        self.assertEqual(account.external_identities.count(), 1)
        self.assertIn("access", response.data)
        self.assertTrue(AuthSession.objects.filter(account=account).exists())

    @patch("apps.identity.views.google.verified_google_claims")
    def test_google_sign_in_does_not_auto_merge_existing_email_account(self, verify_claims):
        existing = Account.objects.create_user(
            email="existing.person@example.com",
            password="Long-Unique-Password-987!",
            email_verified=True,
        )
        verify_claims.return_value = ("google-subject-2", "existing.person@example.com")

        response = self.client.post(self.url, {"credential": "valid-test-token"}, format="json")

        self.assertEqual(response.status_code, 409)
        self.assertTrue(response.data["account_linking_required"])
        self.assertFalse(ExternalIdentity.objects.filter(subject="google-subject-2").exists())
        self.assertEqual(Account.objects.count(), 1)
        self.assertTrue(existing.has_usable_password())

    @patch("apps.identity.views.google.verified_google_claims")
    def test_existing_google_identity_signs_in_to_linked_account(self, verify_claims):
        account = Account.objects.create_user(
            email="linked.person@example.com",
            password=None,
            email_verified=True,
        )
        ExternalIdentity.objects.create(
            account=account,
            provider=ExternalIdentity.Provider.GOOGLE,
            subject="google-subject-3",
            provider_email=account.email,
        )
        verify_claims.return_value = ("google-subject-3", account.email)

        response = self.client.post(self.url, {"credential": "valid-test-token"}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["session_id"], str(AuthSession.objects.get(account=account).id))

    @patch("apps.identity.views.google.verified_google_claims")
    def test_authenticated_account_can_link_a_verified_google_identity(self, verify_claims):
        account = Account.objects.create_user(
            email="person@example.com",
            password="Long-Unique-Password-987!",
            email_verified=True,
        )
        self.client.force_authenticate(user=account)
        verify_claims.return_value = ("google-subject-4", "another.verified@example.com")

        response = self.client.post(self.url, {"credential": "valid-test-token"}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            ExternalIdentity.objects.filter(
                account=account,
                provider=ExternalIdentity.Provider.GOOGLE,
                subject="google-subject-4",
            ).exists()
        )
