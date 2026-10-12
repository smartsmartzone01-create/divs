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
from apps.operations.services.invitations import issue_operations_invitation


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class OperationsInvitationAPITests(APITestCase):
    def setUp(self):
        self.superuser = Account.objects.create_superuser(
            email="root@example.com",
            password="StrongPassword123!",
        )
        self.url = reverse("operations:invitation-create")
        self.validate_url = reverse("operations:invitation-validate")
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
        raw_code = mail.outbox[0].body.split("Invitation code: ", 1)[1].splitlines()[0]
        self.assertTrue(check_password(raw_code, invitation.code_hash))
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

    def test_invitation_code_can_be_validated_without_consuming_it(self):
        invitation = issue_operations_invitation(
            inviter=self.superuser,
            email="new.operator@example.com",
            role=OperationsInvitation.Role.OPERATOR,
        )
        raw_code = mail.outbox[-1].body.split("Invitation code: ", 1)[1].splitlines()[0]

        response = self.client.post(
            self.validate_url,
            {"email": "NEW.OPERATOR@example.com", "code": raw_code},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["valid"])
        self.assertEqual(response.data["invitation_id"], str(invitation.id))
        invitation.refresh_from_db()
        self.assertIsNone(invitation.used_at)

    def test_wrong_code_is_rejected(self):
        issue_operations_invitation(
            inviter=self.superuser,
            email="new.operator@example.com",
            role=OperationsInvitation.Role.OPERATOR,
        )

        response = self.client.post(
            self.validate_url,
            {"email": "new.operator@example.com", "code": "wrong-code"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_expired_invitation_code_is_rejected(self):
        invitation = issue_operations_invitation(
            inviter=self.superuser,
            email="new.operator@example.com",
            role=OperationsInvitation.Role.OPERATOR,
        )
        raw_code = mail.outbox[-1].body.split("Invitation code: ", 1)[1].splitlines()[0]
        invitation.expires_at = timezone.now() - timedelta(seconds=1)
        invitation.save(update_fields=["expires_at"])

        response = self.client.post(
            self.validate_url,
            {"email": "new.operator@example.com", "code": raw_code},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
