from django.test import TestCase
from rest_framework.test import APIRequestFactory

from apps.identity.models import Account
from apps.operations.models import OperationsMembership
from apps.operations.permissions import (
    ROLE_CAPABILITIES,
    SystemSuperuserOnly,
    capabilities_for,
)
from apps.profiles.models import OperationsProfile


class OperationsPermissionPolicyTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.system_root = Account.objects.create_superuser(
            email="system-root@example.com",
            password="StrongPassword123!",
        )

    def test_operator_gets_daily_capabilities_but_not_invitation_management(self):
        operator = Account.objects.create_user(
            email="operator@example.com",
            password="StrongPassword123!",
        )
        membership = OperationsMembership.objects.create(
            account=operator,
            role=OperationsMembership.Role.OPERATOR,
            approved_by=self.system_root,
        )
        OperationsProfile.objects.create(membership=membership)

        capabilities = capabilities_for(operator)

        self.assertIn("view_operations_workspace", capabilities)
        self.assertIn("review_driver_verification", capabilities)
        self.assertNotIn("manage_invitations", capabilities)

    def test_admin_gets_invitation_capability_but_cannot_approve_applications(self):
        admin = Account.objects.create_superuser(
            email="approved-admin@example.com",
            password="StrongPassword123!",
        )
        membership = OperationsMembership.objects.create(
            account=admin,
            role=OperationsMembership.Role.ADMIN,
            approved_by=self.system_root,
        )
        OperationsProfile.objects.create(membership=membership)

        self.assertIn("manage_invitations", capabilities_for(admin))
        request = self.factory.post("/api/v1/operations/applications/example/review/")
        request.user = admin
        self.assertFalse(SystemSuperuserOnly().has_permission(request, object()))

    def test_suspended_operations_member_has_no_capabilities(self):
        operator = Account.objects.create_user(
            email="suspended-operator@example.com",
            password="StrongPassword123!",
        )
        membership = OperationsMembership.objects.create(
            account=operator,
            role=OperationsMembership.Role.OPERATOR,
            approved_by=self.system_root,
        )
        OperationsProfile.objects.create(
            membership=membership,
            status=OperationsProfile.Status.SUSPENDED,
        )

        self.assertEqual(capabilities_for(operator), frozenset())

    def test_initial_system_superuser_has_admin_capabilities_and_can_approve(self):
        self.assertEqual(
            capabilities_for(self.system_root),
            ROLE_CAPABILITIES[OperationsMembership.Role.ADMIN],
        )
        request = self.factory.post("/api/v1/operations/applications/example/review/")
        request.user = self.system_root
        self.assertTrue(SystemSuperuserOnly().has_permission(request, object()))
