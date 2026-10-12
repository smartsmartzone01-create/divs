from django.test import TestCase
from rest_framework.test import APIRequestFactory

from apps.identity.models import Account
from apps.operations.models import OperationsMembership
from apps.profiles.models import ClientProfile, DriverProfile, OperationsProfile
from apps.registrations.models import ClientRegistration, DriverRegistration
from common.permissions import HasRequiredProfile


class DummyProfileView:
    required_profile_type = None


class SharedRolePermissionTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = HasRequiredProfile()
        self.account = Account.objects.create_user(
            email="driver-client@example.com",
            phone_number="+255700000021",
            password="StrongPassword123!",
        )
        self.driver_registration = DriverRegistration.objects.create(
            account=self.account,
            first_name="Amani",
            middle_name="",
            last_name="Juma",
            nationality="Tanzanian",
            region="Dar es Salaam",
            district="Kinondoni",
            current_residential_address="Mikocheni",
            driving_experience="1_to_3_years",
        )
        self.client_registration = ClientRegistration.objects.create(
            account=self.account,
            client_type=ClientRegistration.ClientType.INDIVIDUAL,
            name="Amani Juma",
            primary_contact="+255700000021",
            email="amani.client@example.com",
            country="Tanzania",
            region="Dar es Salaam",
        )

    def allowed(self, account, profile_type):
        request = self.factory.get("/protected/")
        request.user = account
        view = DummyProfileView()
        view.required_profile_type = profile_type
        return self.permission.has_permission(request, view)

    def test_driver_profile_grants_driver_area_only(self):
        DriverProfile.objects.create(registration=self.driver_registration)

        self.assertTrue(self.allowed(self.account, "driver"))
        self.assertFalse(self.allowed(self.account, "client"))
        self.assertFalse(self.allowed(self.account, "operations"))

    def test_client_profile_grants_client_area_only(self):
        ClientProfile.objects.create(registration=self.client_registration)

        self.assertTrue(self.allowed(self.account, "client"))
        self.assertFalse(self.allowed(self.account, "driver"))
        self.assertFalse(self.allowed(self.account, "operations"))

    def test_account_with_both_profiles_can_access_both_areas(self):
        DriverProfile.objects.create(registration=self.driver_registration)
        ClientProfile.objects.create(registration=self.client_registration)

        self.assertTrue(self.allowed(self.account, "driver"))
        self.assertTrue(self.allowed(self.account, "client"))
        self.assertFalse(self.allowed(self.account, "operations"))

    def test_suspended_profile_does_not_grant_area_access(self):
        DriverProfile.objects.create(
            registration=self.driver_registration,
            status=DriverProfile.Status.SUSPENDED,
        )

        self.assertFalse(self.allowed(self.account, "driver"))

    def test_account_without_profile_cannot_access_profile_area(self):
        self.assertFalse(self.allowed(self.account, "driver"))
        self.assertFalse(self.allowed(self.account, "client"))
        self.assertFalse(self.allowed(self.account, "operations"))

    def test_operations_profile_requires_approved_membership(self):
        approver = Account.objects.create_superuser(
            email="system-root@example.com",
            password="StrongPassword123!",
        )
        membership = OperationsMembership.objects.create(
            account=self.account,
            role=OperationsMembership.Role.OPERATOR,
            approved_by=approver,
        )

        self.assertFalse(self.allowed(self.account, "operations"))
        OperationsProfile.objects.create(membership=membership)
        self.assertTrue(self.allowed(self.account, "operations"))

    def test_system_superuser_can_access_operations_area(self):
        root = Account.objects.create_superuser(
            email="root-access@example.com",
            password="StrongPassword123!",
        )

        self.assertTrue(self.allowed(root, "operations"))
        self.assertFalse(self.allowed(root, "driver"))
        self.assertFalse(self.allowed(root, "client"))

    def test_missing_or_unknown_profile_requirement_fails_closed(self):
        request = self.factory.get("/protected/")
        request.user = self.account

        self.assertFalse(self.permission.has_permission(request, DummyProfileView()))
        view = DummyProfileView()
        view.required_profile_type = "unknown"
        self.assertFalse(self.permission.has_permission(request, view))
