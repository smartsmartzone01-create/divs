from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.identity.models import Account
from apps.operations.models import OperationsMembership
from apps.profiles.models import OperationsProfile


class OperationsProfileAPITests(APITestCase):
    def setUp(self):
        self.approver = Account.objects.create_superuser(
            email="root@example.com",
            password="StrongPassword123!",
        )
        self.account = Account.objects.create_user(
            email="operator@example.com",
            phone_number="+255700000010",
            password="StrongPassword123!",
        )
        self.membership = OperationsMembership.objects.create(
            account=self.account,
            role=OperationsMembership.Role.OPERATOR,
            approved_by=self.approver,
        )
        self.profile = OperationsProfile.objects.create(membership=self.membership)
        self.url = reverse("profiles:operations")
        self.client.force_authenticate(user=self.account)

    def test_operations_member_can_retrieve_own_profile_and_role(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data["id"]), str(self.profile.id))
        self.assertEqual(response.data["status"], OperationsProfile.Status.ACTIVE)
        self.assertEqual(response.data["role"], OperationsMembership.Role.OPERATOR)
        self.assertEqual(response.data["email"], self.account.email)
        self.assertEqual(response.data["phone_number"], self.account.phone_number)
        self.assertIn("approved_at", response.data)
        self.assertIn("created_at", response.data)
        self.assertIn("updated_at", response.data)

    def test_profile_endpoint_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_account_without_operations_profile_is_denied(self):
        account = Account.objects.create_user(
            email="ordinary@example.com",
            password="StrongPassword123!",
        )
        self.client.force_authenticate(user=account)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_suspended_operations_profile_is_denied(self):
        self.profile.status = OperationsProfile.Status.SUSPENDED
        self.profile.save(update_fields=["status", "updated_at"])

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_member_cannot_retrieve_another_members_profile(self):
        other_account = Account.objects.create_user(
            email="other-operator@example.com",
            password="StrongPassword123!",
        )
        other_membership = OperationsMembership.objects.create(
            account=other_account,
            role=OperationsMembership.Role.OPERATOR,
            approved_by=self.approver,
        )
        OperationsProfile.objects.create(membership=other_membership)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data["id"]), str(self.profile.id))
        self.assertEqual(response.data["email"], self.account.email)
        self.assertNotEqual(response.data["email"], other_account.email)

    def test_profile_endpoint_is_read_only(self):
        response = self.client.patch(self.url, {"status": "suspended"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.status, OperationsProfile.Status.ACTIVE)
