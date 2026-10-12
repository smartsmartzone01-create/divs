from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.identity.models import Account
from apps.notifications.models import Notification
from apps.notifications.services import create_notification, notify_operations_reviewers
from apps.operations.models import OperationsApplication, OperationsInvitation, OperationsMembership
from apps.operations.services.reviews import review_operations_application
from apps.profiles.models import ClientProfile, DriverProfile, OperationsProfile
from apps.registrations.models import ClientRegistration, DriverRegistration
from django.utils import timezone
from datetime import timedelta


class NotificationAPITests(APITestCase):
    def setUp(self):
        self.driver = Account.objects.create_user(
            email="driver@example.com", password="StrongPassword123!"
        )
        driver_registration = DriverRegistration.objects.create(
            account=self.driver,
            first_name="Amani",
            middle_name="",
            last_name="Juma",
            nationality="Tanzanian",
            region="Dar es Salaam",
            district="Kinondoni",
            current_residential_address="Mikocheni",
            driving_experience="1_to_3_years",
        )
        DriverProfile.objects.create(registration=driver_registration)

        self.client_account = Account.objects.create_user(
            email="client@example.com", password="StrongPassword123!"
        )
        client_registration = ClientRegistration.objects.create(
            account=self.client_account,
            client_type=ClientRegistration.ClientType.INDIVIDUAL,
            name="Neema Kassim",
            primary_contact="+255700000040",
            email="neema@example.com",
            country="Tanzania",
            region="Arusha",
        )
        ClientProfile.objects.create(registration=client_registration)

        admin = Account.objects.create_superuser(
            email="system-admin@example.com", password="StrongPassword123!"
        )
        self.operator = Account.objects.create_user(
            email="operator@example.com", password="StrongPassword123!"
        )
        membership = OperationsMembership.objects.create(
            account=self.operator,
            role=OperationsMembership.Role.OPERATOR,
            approved_by=admin,
        )
        OperationsProfile.objects.create(membership=membership)

    def test_account_receives_only_notifications_for_requested_workspace(self):
        driver_note = create_notification(
            recipient=self.driver,
            recipient_role=Notification.RecipientRole.DRIVER,
            event_type="driver.requested",
            title="New driver request",
            message="A client has sent you a driver request.",
        )
        create_notification(
            recipient=self.client_account,
            recipient_role=Notification.RecipientRole.CLIENT,
            event_type="request.updated",
            title="Request updated",
            message="Your driver request was updated.",
        )
        self.client.force_authenticate(user=self.driver)

        response = self.client.get(reverse("notifications:driver-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["unread_count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(str(response.data["results"][0]["id"]), str(driver_note.id))
        self.assertEqual(response.data["results"][0]["recipient_role"], "driver")

    def test_notification_read_route_cannot_read_another_accounts_notification(self):
        note = create_notification(
            recipient=self.client_account,
            recipient_role=Notification.RecipientRole.CLIENT,
            event_type="request.updated",
            title="Request updated",
            message="Your driver request was updated.",
        )
        self.client.force_authenticate(user=self.driver)

        response = self.client.post(
            reverse("notifications:driver-read", kwargs={"notification_id": note.id})
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        note.refresh_from_db()
        self.assertIsNone(note.read_at)

    def test_recipient_can_mark_their_own_workspace_notification_read(self):
        note = create_notification(
            recipient=self.driver,
            recipient_role=Notification.RecipientRole.DRIVER,
            event_type="driver.requested",
            title="New driver request",
            message="A client has sent you a driver request.",
        )
        self.client.force_authenticate(user=self.driver)

        response = self.client.post(
            reverse("notifications:driver-read", kwargs={"notification_id": note.id})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_read"])
        note.refresh_from_db()
        self.assertIsNotNone(note.read_at)

    def test_workspace_endpoint_requires_matching_active_profile(self):
        account = Account.objects.create_user(
            email="no-profile@example.com", password="StrongPassword123!"
        )
        self.client.force_authenticate(user=account)

        response = self.client.get(reverse("notifications:driver-list"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_notifications_for_same_account_are_separated_by_role(self):
        # The model/service allows multiple role profiles to share one account.
        dual_role_account = Account.objects.create_user(
            email="dual@example.com", password="StrongPassword123!"
        )
        driver_registration = DriverRegistration.objects.create(
            account=dual_role_account,
            first_name="Juma",
            middle_name="",
            last_name="Kassim",
            nationality="Tanzanian",
            region="Arusha",
            district="Arusha City",
            current_residential_address="Sakina",
            driving_experience="4_to_7_years",
        )
        DriverProfile.objects.create(registration=driver_registration)
        client_registration = ClientRegistration.objects.create(
            account=dual_role_account,
            client_type=ClientRegistration.ClientType.INDIVIDUAL,
            name="Juma Kassim",
            primary_contact="+255700000041",
            email="dual@example.com",
            country="Tanzania",
            region="Arusha",
        )
        ClientProfile.objects.create(registration=client_registration)
        create_notification(
            recipient=dual_role_account,
            recipient_role=Notification.RecipientRole.DRIVER,
            event_type="job.completed",
            title="Job completed",
            message="Your recorded job was marked complete.",
        )
        create_notification(
            recipient=dual_role_account,
            recipient_role=Notification.RecipientRole.CLIENT,
            event_type="request.updated",
            title="Request updated",
            message="Your request status has changed.",
        )

        self.client.force_authenticate(user=dual_role_account)
        driver_response = self.client.get(reverse("notifications:driver-list"))
        client_response = self.client.get(reverse("notifications:client-list"))

        self.assertEqual(len(driver_response.data["results"]), 1)
        self.assertEqual(driver_response.data["results"][0]["recipient_role"], "driver")
        self.assertEqual(len(client_response.data["results"]), 1)
        self.assertEqual(client_response.data["results"][0]["recipient_role"], "client")

    def test_service_rejects_inactive_or_missing_role_profile(self):
        account = Account.objects.create_user(
            email="unregistered@example.com", password="StrongPassword123!"
        )
        with self.assertRaises(ValidationError):
            create_notification(
                recipient=account,
                recipient_role=Notification.RecipientRole.DRIVER,
                event_type="driver.requested",
                title="New driver request",
                message="A client has sent you a driver request.",
            )

    def test_driver_registration_event_notifies_operations_accounts_individually(self):
        notify_operations_reviewers(
            event_type="driver.registration.submitted",
            title="New driver registration",
            message="A driver has registered and their verification checks are awaiting review.",
        )

        self.client.force_authenticate(user=self.operator)
        operator_response = self.client.get(reverse("notifications:operations-list"))
        self.client.force_authenticate(user=Account.objects.get(email="system-admin@example.com"))
        root_response = self.client.get(reverse("notifications:operations-list"))

        self.assertEqual(operator_response.status_code, status.HTTP_200_OK)
        self.assertEqual(root_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            operator_response.data["results"][0]["event_type"],
            "driver.registration.submitted",
        )
        self.assertEqual(
            root_response.data["results"][0]["event_type"],
            "driver.registration.submitted",
        )
        self.assertEqual(len(operator_response.data["results"]), 1)
        self.assertEqual(len(root_response.data["results"]), 1)

    def test_rejected_operations_applicant_receives_only_application_notification(self):
        system_root = Account.objects.create_superuser(
            email="root-for-review@example.com",
            password="StrongPassword123!",
        )
        applicant = Account.objects.create_user(
            email="applicant@example.com",
            password="StrongPassword123!",
        )
        invitation = OperationsInvitation.objects.create(
            email=applicant.email,
            role=OperationsInvitation.Role.OPERATOR,
            code_hash="already-hashed",
            invited_by=system_root,
            expires_at=timezone.now() + timedelta(days=1),
        )
        application = OperationsApplication.objects.create(
            invitation=invitation,
            account=applicant,
            full_name="Applicant Person",
        )

        review_operations_application(
            application_id=application.id,
            reviewer=system_root,
            decision=OperationsApplication.Status.REJECTED,
        )
        self.client.force_authenticate(user=applicant)
        response = self.client.get(reverse("notifications:operations-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(
            response.data["results"][0]["event_type"],
            "operations.application.rejected",
        )
        self.assertEqual(response.data["results"][0]["recipient_role"], "operations")

    def test_endpoint_requires_authentication(self):
        response = self.client.get(reverse("notifications:driver-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
