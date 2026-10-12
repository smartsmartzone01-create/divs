from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.identity.models import Account
from apps.operations.models import OperationsMembership
from apps.profiles.models import ClientProfile, DriverProfile, OperationsProfile
from apps.registrations.models import ClientRegistration, DriverRegistration


class RoleProfileModelTests(TestCase):
    def setUp(self):
        self.account = Account.objects.create_user(
            email="multi-role@example.com",
            phone_number="+255700000010",
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
            driving_experience="none",
        )
        self.client_registration = ClientRegistration.objects.create(
            account=self.account,
            client_type=ClientRegistration.ClientType.INDIVIDUAL,
            name="Amani Juma",
            primary_contact="+255700000010",
            email="amani@example.com",
            country="Tanzania",
            region="Dar es Salaam",
        )

    def test_driver_profile_is_separate_and_resolves_shared_account(self):
        profile = DriverProfile.objects.create(registration=self.driver_registration)

        self.assertNotEqual(profile.id, self.driver_registration.id)
        self.assertEqual(profile.account, self.account)
        self.assertEqual(profile.status, DriverProfile.Status.ACTIVE)

    def test_same_account_can_have_driver_and_client_profiles(self):
        driver_profile = DriverProfile.objects.create(registration=self.driver_registration)
        client_profile = ClientProfile.objects.create(registration=self.client_registration)

        self.assertEqual(driver_profile.account, client_profile.account)
        self.assertNotEqual(driver_profile.id, client_profile.id)

    def test_only_one_profile_can_be_created_for_each_registration(self):
        DriverProfile.objects.create(registration=self.driver_registration)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                DriverProfile.objects.create(registration=self.driver_registration)

    def test_operations_profile_is_linked_to_operations_membership(self):
        approver = Account.objects.create_superuser(
            email="system-admin@example.com",
            password="StrongPassword123!",
        )
        operations_account = Account.objects.create_user(
            email="operator@example.com",
            password="StrongPassword123!",
        )
        membership = OperationsMembership.objects.create(
            account=operations_account,
            role=OperationsMembership.Role.OPERATOR,
            approved_by=approver,
        )

        profile = OperationsProfile.objects.create(membership=membership)

        self.assertEqual(profile.account, operations_account)
        self.assertEqual(profile.status, OperationsProfile.Status.ACTIVE)
