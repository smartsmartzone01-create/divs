from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.identity.models import Account
from apps.operations.models import OperationsApplication, OperationsInvitation


class OperationsApplicationMyStatusTests(APITestCase):
    def setUp(self):
        self.applicant = Account.objects.create_user(
            email="applicant@example.com",
            password="StrongPassword123!",
        )
        self.other_applicant = Account.objects.create_user(
            email="other@example.com",
            password="StrongPassword123!",
        )
        self.root = Account.objects.create_superuser(
            email="root@example.com",
            password="StrongPassword123!",
        )
        self.url = reverse("operations:application-my-status")

    def create_application(self, account, email, status_value=OperationsApplication.Status.PENDING):
        invitation = OperationsInvitation.objects.create(
            email=email,
            role=OperationsInvitation.Role.OPERATOR,
            code_hash="not-used-by-status-endpoint",
            invited_by=self.root,
            expires_at=timezone.now() + timedelta(hours=24),
        )
        return OperationsApplication.objects.create(
            invitation=invitation,
            account=account,
            full_name="Applicant Example",
            status=status_value,
        )

    def test_applicant_can_check_own_pending_application(self):
        application = self.create_application(self.applicant, self.applicant.email)
        self.client.force_authenticate(user=self.applicant)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["has_application"])
        self.assertEqual(response.data["id"], str(application.id))
        self.assertEqual(response.data["status"], OperationsApplication.Status.PENDING)
        self.assertEqual(response.data["role_applied_for"], OperationsInvitation.Role.OPERATOR)
        self.assertNotIn("review_note", response.data)
        self.assertNotIn("reviewed_by", response.data)

    def test_applicant_can_check_latest_decision_without_getting_workspace_access(self):
        self.create_application(
            self.applicant,
            self.applicant.email,
            status_value=OperationsApplication.Status.REJECTED,
        )
        self.client.force_authenticate(user=self.applicant)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], OperationsApplication.Status.REJECTED)
        self.assertFalse(hasattr(self.applicant, "operations_membership"))

    def test_account_cannot_read_another_applicants_application(self):
        self.create_application(self.other_applicant, self.other_applicant.email)
        self.client.force_authenticate(user=self.applicant)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["has_application"])
        self.assertNotIn("id", response.data)

    def test_unauthenticated_account_cannot_check_application_status(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_latest_application_is_returned_when_applicant_has_multiple(self):
        older = self.create_application(
            self.applicant,
            "old-invitation@example.com",
            status_value=OperationsApplication.Status.REJECTED,
        )
        newer = self.create_application(
            self.applicant,
            "new-invitation@example.com",
            status_value=OperationsApplication.Status.PENDING,
        )
        # Keep ordering deterministic without relying on database timestamp precision.
        OperationsApplication.objects.filter(pk=older.pk).update(
            submitted_at=timezone.now() - timedelta(minutes=5)
        )
        OperationsApplication.objects.filter(pk=newer.pk).update(
            submitted_at=timezone.now()
        )
        self.client.force_authenticate(user=self.applicant)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(newer.id))
        self.assertEqual(response.data["status"], OperationsApplication.Status.PENDING)
