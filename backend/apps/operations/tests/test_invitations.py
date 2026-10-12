from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.hashers import check_password
from django.core import mail
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.identity.models import Account
from apps.operations.models import OperationsInvitation


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class OperationsInvitationAPITests(APITestCase):
    def setUp(self):
        self.superuser = Account.objects.create_superuser(
            email="root@example.com",
            password="StrongPassword123!",
        )
        self.url = reverse("operations:invitation-create")
        self.payload = {
            "email": "new.operator@example.com",
            "role": OperationsInvitation.Role.OPERATOR,
        }

    def test_superuser_can_issue_email_bound_invitation(self):
        self.client.force_authenticate(user=self.superuser)

        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        invitation = OperationsInvitation.objects.get()
        self.assertEqual(invitation.email, "new.operator@example.com")
        self.assertEqual(invitation.role, OperationsInvitation.Role.OPERATOR)
        self.assertEqual(invitation.invited_by, self.superuser)
        expected_expiry = timezone.now() + timedelta(hours=24)
        self.assertLess(abs(invitation.expires_at - expected_expiry), timedelta(seconds=10))
        self.assertTrue(check_password(
            mail.outbox[0].body.split("Invitation code: ", 1)[1].splitlines()[0],
            invitation.code_hash,
        ))
        self.assertNotIn("code", response.data)

    def test_regular_account_cannot_issue_invitation(self):
        account = Account.objects.create_user(
            email="driver@example.com",
            password="StrongPassword123!",
        )
        self.client.force_authenticate(user=account)

        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(OperationsInvitation.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_unauthenticated_request_cannot_issue_invitation(self):
        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(OperationsInvitation.objects.count(), 0)

    def test_invalid_role_is_rejected(self):
        self.client.force_authenticate(user=self.superuser)

        response = self.client.post(
            self.url,
            {"email": "person@example.com", "role": "driver"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(OperationsInvitation.objects.count(), 0)

    @patch("apps.operations.services.invitations.send_mail", return_value=0)
    def test_failed_delivery_does_not_leave_invitation(self, mock_send_mail):
        self.client.force_authenticate(user=self.superuser)

        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(OperationsInvitation.objects.count(), 0)
