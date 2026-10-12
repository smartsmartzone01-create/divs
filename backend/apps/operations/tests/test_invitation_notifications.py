from datetime import timedelta

from django.core import mail
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.identity.models import Account
from apps.notifications.models import Notification
from apps.operations.models import OperationsInvitation
from apps.operations.services.invitations import issue_operations_invitation


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class OperationsInvitationNotificationTests(APITestCase):
    def setUp(self):
        self.root = Account.objects.create_superuser(
            email="root@example.com",
            password="StrongPassword123!",
        )
        self.client.force_authenticate(user=self.root)

    def test_invitation_creation_notifies_operations_reviewers_after_commit(self):
        with self.captureOnCommitCallbacks(execute=True):
            invitation = issue_operations_invitation(
                inviter=self.root,
                email="invitee@example.com",
                role=OperationsInvitation.Role.OPERATOR,
            )

        self.assertIsNone(invitation.expires_at)
        notification = Notification.objects.get(
            recipient=self.root,
            event_type="operations.invitation.created",
        )
        self.assertEqual(notification.recipient_role, Notification.RecipientRole.OPERATIONS)

    def test_invitation_revocation_notifies_operations_reviewers_after_commit(self):
        invitation = OperationsInvitation.objects.create(
            email="invitee@example.com",
            role=OperationsInvitation.Role.OPERATOR,
            code_hash="hashed-code",
            invited_by=self.root,
            expires_at=None,
        )
        url = reverse("operations:invitation-revoke", kwargs={"invitation_id": invitation.id})

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.root,
                event_type="operations.invitation.revoked",
            ).exists()
        )
        invitation.refresh_from_db()
        self.assertIsNotNone(invitation.revoked_at)
