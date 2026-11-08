import io
from datetime import timedelta
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.identity.models import Account
from apps.notifications.models import Notification
from apps.operations.models import OperationsMembership
from apps.profiles.models import DriverProfile, OperationsProfile
from apps.registrations.models import DriverRegistration
from apps.verification.models import (
    DriverVerification,
    DriverVerificationCheck,
    DriverVerificationEvidence,
    DriverVerificationEvidenceEvent,
    DriverVerificationEvent,
    GovernmentVerificationAttempt,
    VerifiedDriverLicenceClass,
)
from apps.verification.services import (
    record_government_api_result,
    record_verified_licence_classes,
    review_driver_check,
    process_expired_verification_evidence,
)


class DriverVerificationAPITests(APITestCase):
    def setUp(self):
        self.driver = Account.objects.create_user(
            email="driver@example.com", password="StrongPassword123!"
        )
        registration = DriverRegistration.objects.create(
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
        self.profile = DriverProfile.objects.create(registration=registration)
        self.verification = self.profile.verification
        self.url = reverse("verification:driver-me")

    def test_driver_can_read_only_their_check_progress(self):
        self.client.force_authenticate(user=self.driver)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], DriverVerification.Status.PENDING)
        self.assertEqual(len(response.data["checks"]), 4)
        self.assertFalse(response.data["is_discoverable"])
        self.assertNotIn("government_response", response.data)
        self.assertNotIn("national_id_number", response.data)

    def test_driver_endpoint_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_client_cannot_read_driver_verification_endpoint(self):
        client_account = Account.objects.create_user(
            email="client@example.com", password="StrongPassword123!"
        )
        self.client.force_authenticate(user=client_account)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("apps.verification.views.retrieve_verification_evidence")
    @patch("apps.verification.models.DriverVerificationEvidenceEvent.objects.create", side_effect=RuntimeError("audit unavailable"))
    def test_file_is_not_served_when_access_audit_cannot_be_written(self, _audit_create, retrieve):
        check = self.verification.checks.first()
        evidence = DriverVerificationEvidence.objects.create(
            verification_check=check,
            evidence_type=check.check_type,
            source=DriverVerificationEvidence.Source.DRIVER_UPLOAD,
            original_filename="identity.jpg",
            content_type="image/jpeg",
            file_size=4,
            sha256="a" * 64,
            storage_key="verification-evidence/test-object",
            uploaded_by=self.driver,
        )
        body = io.BytesIO(b"private bytes")
        retrieve.return_value = (body, "image/jpeg", "identity.jpg")
        self.client.force_authenticate(user=self.driver)

        response = self.client.get(
            reverse("verification:driver-evidence-file", kwargs={"evidence_id": evidence.id})
        )

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertTrue(body.closed)


    def test_non_operations_user_cannot_access_operations_evidence_file(self):
        check = self.verification.checks.first()
        evidence = DriverVerificationEvidence.objects.create(
            verification_check=check,
            evidence_type=check.check_type,
            source=DriverVerificationEvidence.Source.DRIVER_UPLOAD,
            original_filename="identity.jpg",
            content_type="image/jpeg",
            file_size=4,
            sha256="a" * 64,
            storage_key="verification-evidence/test-object",
            uploaded_by=self.driver,
        )
        self.client.force_authenticate(user=self.driver)

        response = self.client.get(
            reverse("verification:operations-evidence-file", kwargs={"evidence_id": evidence.id})
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    @patch("apps.verification.views.retrieve_verification_evidence")
    def test_driver_file_access_is_recorded_in_evidence_history(self, retrieve):
        check = self.verification.checks.first()
        evidence = DriverVerificationEvidence.objects.create(
            verification_check=check,
            evidence_type=check.check_type,
            source=DriverVerificationEvidence.Source.DRIVER_UPLOAD,
            original_filename="identity.jpg",
            content_type="image/jpeg",
            file_size=4,
            sha256="a" * 64,
            storage_key="verification-evidence/test-object",
            uploaded_by=self.driver,
        )
        retrieve.return_value = (io.BytesIO(b"test"), "image/jpeg", "identity.jpg")
        self.client.force_authenticate(user=self.driver)

        response = self.client.get(
            reverse("verification:driver-evidence-file", kwargs={"evidence_id": evidence.id})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            DriverVerificationEvidenceEvent.objects.filter(
                evidence=evidence,
                actor=self.driver,
                event_type="file_accessed",
            ).exists()
        )
        response.close()

    @patch("apps.verification.views.retrieve_verification_evidence")
    def test_another_driver_cannot_access_evidence_or_create_access_event(self, retrieve):
        check = self.verification.checks.first()
        evidence = DriverVerificationEvidence.objects.create(
            verification_check=check,
            evidence_type=check.check_type,
            source=DriverVerificationEvidence.Source.DRIVER_UPLOAD,
            original_filename="identity.jpg",
            content_type="image/jpeg",
            file_size=4,
            sha256="a" * 64,
            storage_key="verification-evidence/test-object",
            uploaded_by=self.driver,
        )
        other_driver = Account.objects.create_user(
            email="unrelated-driver@example.com",
            password="StrongPassword123!",
        )
        self.client.force_authenticate(user=other_driver)

        response = self.client.get(
            reverse("verification:driver-evidence-file", kwargs={"evidence_id": evidence.id})
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        retrieve.assert_not_called()
        self.assertFalse(
            DriverVerificationEvidenceEvent.objects.filter(
                evidence=evidence,
                event_type="file_accessed",
            ).exists()
        )


class VerificationReviewServiceTests(APITestCase):
    def setUp(self):
        self.reviewer = Account.objects.create_user(
            email="operator@example.com", password="StrongPassword123!"
        )
        self.admin = Account.objects.create_superuser(
            email="system-admin@example.com", password="StrongPassword123!"
        )
        membership = OperationsMembership.objects.create(
            account=self.reviewer,
            role=OperationsMembership.Role.OPERATOR,
            approved_by=self.admin,
        )
        OperationsProfile.objects.create(membership=membership)
        driver = Account.objects.create_user(
            email="another-driver@example.com", password="StrongPassword123!"
        )
        registration = DriverRegistration.objects.create(
            account=driver,
            first_name="Neema",
            middle_name="",
            last_name="Kassim",
            nationality="Tanzanian",
            region="Arusha",
            district="Arusha City",
            current_residential_address="Sakina",
            driving_experience="4_to_7_years",
        )
        profile = DriverProfile.objects.create(registration=registration)
        self.verification = profile.verification
        self.checks = list(self.verification.checks.all())

    def test_operations_user_can_record_minimal_manual_check_outcome(self):
        check = self.checks[0]
        DriverVerificationEvidence.objects.create(
            verification_check=check,
            evidence_type=check.check_type,
            source=DriverVerificationEvidence.Source.DRIVER_UPLOAD,
            status=DriverVerificationEvidence.Status.ACCEPTED,
            scan_status=DriverVerificationEvidence.ScanStatus.CLEAN,
            storage_key="verification-evidence/accepted-test-object",
            uploaded_by=check.verification.profile.registration.account,
            reviewed_by=self.reviewer,
        )
        self.client.force_authenticate(user=self.reviewer)
        url = reverse(
            "verification:operations-check-review",
            kwargs={"check_id": self.checks[0].id},
        )
        response = self.client.post(
            url,
            {"status": "passed", "result_code": "clear"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["method"], "manual")
        self.assertEqual(response.data["status"], "passed")

    @patch("apps.verification.views.retrieve_verification_evidence")
    def test_operations_evidence_file_access_is_recorded(self, retrieve):
        check = self.checks[0]
        evidence = DriverVerificationEvidence.objects.create(
            verification_check=check,
            evidence_type=check.check_type,
            source=DriverVerificationEvidence.Source.DRIVER_UPLOAD,
            original_filename="identity.jpg",
            content_type="image/jpeg",
            file_size=4,
            sha256="a" * 64,
            storage_key="verification-evidence/test-object",
            uploaded_by=check.verification.profile.registration.account,
        )
        retrieve.return_value = (io.BytesIO(b"test"), "image/jpeg", "identity.jpg")
        self.client.force_authenticate(user=self.reviewer)

        response = self.client.get(
            reverse("verification:operations-evidence-file", kwargs={"evidence_id": evidence.id})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            DriverVerificationEvidenceEvent.objects.filter(
                evidence=evidence,
                actor=self.reviewer,
                event_type="file_accessed",
            ).exists()
        )
        response.close()

    def test_manual_check_cannot_pass_without_accepted_evidence(self):
        check = self.checks[0]
        successful_result = {
            DriverVerificationCheck.CheckType.NATIONAL_IDENTITY: DriverVerificationCheck.ResultCode.MATCH,
            DriverVerificationCheck.CheckType.DRIVING_LICENCE: DriverVerificationCheck.ResultCode.VALID,
            DriverVerificationCheck.CheckType.TRAFFIC_RECORDS: DriverVerificationCheck.ResultCode.CLEAR,
            DriverVerificationCheck.CheckType.ACCIDENT_RECORDS: DriverVerificationCheck.ResultCode.CLEAR,
        }[check.check_type]
        with self.assertRaisesMessage(Exception, "matching accepted evidence is valid and available"):
            review_driver_check(
                check_id=check.id,
                reviewer=self.reviewer,
                status=DriverVerificationCheck.Status.PASSED,
                result_code=successful_result,
            )

    def test_expired_accepted_evidence_cannot_pass_a_manual_check(self):
        check = next(
            item for item in self.checks
            if item.check_type == DriverVerificationCheck.CheckType.NATIONAL_IDENTITY
        )
        DriverVerificationEvidence.objects.create(
            verification_check=check,
            evidence_type=check.check_type,
            source=DriverVerificationEvidence.Source.DRIVER_UPLOAD,
            status=DriverVerificationEvidence.Status.ACCEPTED,
            scan_status=DriverVerificationEvidence.ScanStatus.CLEAN,
            storage_key="verification-evidence/expired-object",
            expires_at=timezone.now() - timedelta(seconds=1),
            uploaded_by=check.verification.profile.registration.account,
            reviewed_by=self.reviewer,
        )
        with self.assertRaisesMessage(Exception, "valid and available"):
            review_driver_check(
                check_id=check.id,
                reviewer=self.reviewer,
                status=DriverVerificationCheck.Status.PASSED,
                result_code=DriverVerificationCheck.ResultCode.MATCH,
            )

    def test_unreviewed_licence_class_does_not_qualify_for_discovery(self):
        check = next(
            item for item in self.checks
            if item.check_type == DriverVerificationCheck.CheckType.DRIVING_LICENCE
        )
        DriverVerificationEvidence.objects.create(
            verification_check=check,
            evidence_type=check.check_type,
            source=DriverVerificationEvidence.Source.DRIVER_UPLOAD,
            status=DriverVerificationEvidence.Status.ACCEPTED,
            scan_status=DriverVerificationEvidence.ScanStatus.CLEAN,
            storage_key="verification-evidence/licence-object",
            uploaded_by=check.verification.profile.registration.account,
            reviewed_by=self.reviewer,
        )
        check.status = DriverVerificationCheck.Status.PASSED
        check.method = DriverVerificationCheck.Method.MANUAL
        check.result_code = DriverVerificationCheck.ResultCode.VALID
        check.save(update_fields=["status", "method", "result_code", "updated_at"])
        licence_class = VerifiedDriverLicenceClass.objects.create(
            licence_check=check,
            licence_class="B",
            is_current=True,
            verified_at=timezone.now(),
        )
        self.assertFalse(licence_class.qualifies_for_discovery)

    def test_trusted_government_result_is_recorded_without_source_payload(self):
        check = self.checks[0]
        expected_result = {
            DriverVerificationCheck.CheckType.NATIONAL_IDENTITY: DriverVerificationCheck.ResultCode.MATCH,
            DriverVerificationCheck.CheckType.DRIVING_LICENCE: DriverVerificationCheck.ResultCode.VALID,
            DriverVerificationCheck.CheckType.TRAFFIC_RECORDS: DriverVerificationCheck.ResultCode.CLEAR,
            DriverVerificationCheck.CheckType.ACCIDENT_RECORDS: DriverVerificationCheck.ResultCode.CLEAR,
        }[check.check_type]
        updated = record_government_api_result(
            check_id=check.id,
            provider="authorized-test-provider",
            provider_reference="request-123",
            outcome=GovernmentVerificationAttempt.Outcome.MATCHED,
            result_code=expected_result,
        )
        self.assertEqual(updated.method, DriverVerificationCheck.Method.GOVERNMENT_API)
        self.assertEqual(updated.status, DriverVerificationCheck.Status.PASSED)
        replayed = record_government_api_result(
            check_id=check.id,
            provider="authorized-test-provider",
            provider_reference="request-123",
            outcome=GovernmentVerificationAttempt.Outcome.MATCHED,
            result_code=expected_result,
        )
        self.assertEqual(replayed.id, updated.id)
        attempt = GovernmentVerificationAttempt.objects.get(verification_check=check)
        self.assertEqual(
            GovernmentVerificationAttempt.objects.filter(
                provider="authorized-test-provider",
                provider_reference="request-123",
            ).count(),
            1,
        )
        self.assertEqual(attempt.provider_reference, "request-123")
        self.assertFalse(hasattr(attempt, "response_payload"))
        record_government_api_result(
            check_id=check.id,
            provider="authorized-test-provider",
            provider_reference="request-124",
            outcome=GovernmentVerificationAttempt.Outcome.UNAVAILABLE,
        )
        check.refresh_from_db()
        self.assertEqual(check.status, DriverVerificationCheck.Status.UNAVAILABLE)
        self.assertFalse(check.has_trusted_supporting_record())

    def test_unavailable_government_source_can_fall_back_to_manual_review(self):
        check = self.checks[0]
        record_government_api_result(
            check_id=check.id,
            provider="authorized-test-provider",
            provider_reference="request-unavailable-1",
            outcome=GovernmentVerificationAttempt.Outcome.UNAVAILABLE,
        )
        DriverVerificationEvidence.objects.create(
            verification_check=check,
            evidence_type=check.check_type,
            source=DriverVerificationEvidence.Source.DRIVER_UPLOAD,
            status=DriverVerificationEvidence.Status.ACCEPTED,
            scan_status=DriverVerificationEvidence.ScanStatus.CLEAN,
            storage_key="verification-evidence/manual-fallback",
            uploaded_by=check.verification.profile.registration.account,
            reviewed_by=self.reviewer,
        )
        result_code = {
            DriverVerificationCheck.CheckType.NATIONAL_IDENTITY: DriverVerificationCheck.ResultCode.MATCH,
            DriverVerificationCheck.CheckType.DRIVING_LICENCE: DriverVerificationCheck.ResultCode.VALID,
            DriverVerificationCheck.CheckType.TRAFFIC_RECORDS: DriverVerificationCheck.ResultCode.CLEAR,
            DriverVerificationCheck.CheckType.ACCIDENT_RECORDS: DriverVerificationCheck.ResultCode.CLEAR,
        }[check.check_type]
        updated = review_driver_check(
            check_id=check.id,
            reviewer=self.reviewer,
            status=DriverVerificationCheck.Status.PASSED,
            result_code=result_code,
        )
        self.assertEqual(updated.method, DriverVerificationCheck.Method.MANUAL)
        self.assertEqual(updated.status, DriverVerificationCheck.Status.PASSED)

    def test_operator_cannot_make_final_verification_approval(self):
        self.client.force_authenticate(user=self.reviewer)
        response = self.client.post(
            reverse(
                "verification:operations-verification-approve",
                kwargs={"verification_id": self.verification.id},
            ),
            {},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_operator_cannot_activate_driver_availability(self):
        self._pass_all_checks()
        self.client.force_authenticate(user=self.reviewer)
        response = self.client.post(
            reverse(
                "verification:operations-driver-activate",
                kwargs={"verification_id": self.verification.id},
            ),
            {},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_manual_review_cannot_claim_government_api_method(self):
        check = self.checks[0]
        with self.assertRaisesMessage(Exception, "cannot be recorded through manual review"):
            review_driver_check(
                check_id=check.id,
                reviewer=self.reviewer,
                status=DriverVerificationCheck.Status.NEEDS_REVIEW,
                method=DriverVerificationCheck.Method.GOVERNMENT_API,
            )

    @patch("apps.verification.views.retrieve_verification_evidence")
    def test_operator_can_accept_matching_submitted_evidence(self, retrieve):
        check = self.checks[0]
        evidence = DriverVerificationEvidence.objects.create(
            verification_check=check,
            evidence_type=check.check_type,
            source=DriverVerificationEvidence.Source.DRIVER_UPLOAD,
            scan_status=DriverVerificationEvidence.ScanStatus.CLEAN,
            storage_key="verification-evidence/reviewable-object",
            uploaded_by=check.verification.profile.registration.account,
        )
        retrieve.return_value = (io.BytesIO(b"reviewable evidence"), "image/jpeg", "evidence.jpg")
        self.client.force_authenticate(user=self.reviewer)
        file_response = self.client.get(
            reverse("verification:operations-evidence-file", kwargs={"evidence_id": evidence.id})
        )
        self.assertEqual(file_response.status_code, status.HTTP_200_OK)
        file_response.close()
        response = self.client.post(
            reverse("verification:operations-evidence-review", kwargs={"evidence_id": evidence.id}),
            {"decision": "accepted", "review_notes": "Evidence reviewed."},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        evidence.refresh_from_db()
        self.assertEqual(evidence.status, DriverVerificationEvidence.Status.ACCEPTED)
        self.assertEqual(evidence.reviewed_by, self.reviewer)
        self.assertTrue(
            DriverVerificationEvidenceEvent.objects.filter(
                evidence=evidence,
                actor=self.reviewer,
                event_type="reviewed",
                new_status=DriverVerificationEvidence.Status.ACCEPTED,
            ).exists()
        )

    def _pass_all_checks(self):
        result_codes = {
            DriverVerificationCheck.CheckType.NATIONAL_IDENTITY: DriverVerificationCheck.ResultCode.MATCH,
            DriverVerificationCheck.CheckType.DRIVING_LICENCE: DriverVerificationCheck.ResultCode.VALID,
            DriverVerificationCheck.CheckType.TRAFFIC_RECORDS: DriverVerificationCheck.ResultCode.CLEAR,
            DriverVerificationCheck.CheckType.ACCIDENT_RECORDS: DriverVerificationCheck.ResultCode.CLEAR,
        }
        for check in self.checks:
            DriverVerificationEvidence.objects.create(
                verification_check=check,
                evidence_type=check.check_type,
                source=DriverVerificationEvidence.Source.DRIVER_UPLOAD,
                status=DriverVerificationEvidence.Status.ACCEPTED,
                scan_status=DriverVerificationEvidence.ScanStatus.CLEAN,
                storage_key=f"verification-evidence/accepted-{check.check_type}",
                uploaded_by=check.verification.profile.registration.account,
                reviewed_by=self.reviewer,
            )
            review_driver_check(
                check_id=check.id,
                reviewer=self.reviewer,
                status=DriverVerificationCheck.Status.PASSED,
                result_code=result_codes[check.check_type],
            )

    def _approve_and_activate_driver(self):
        self._pass_all_checks()
        licence_check = next(
            check for check in self.checks
            if check.check_type == DriverVerificationCheck.CheckType.DRIVING_LICENCE
        )
        record_verified_licence_classes(
            check_id=licence_check.id,
            reviewer=self.reviewer,
            licence_classes=["C"],
        )
        self.client.force_authenticate(user=self.admin)
        approval = self.client.post(
            reverse(
                "verification:operations-verification-approve",
                kwargs={"verification_id": self.verification.id},
            ),
            {},
            format="json",
        )
        self.assertEqual(approval.status_code, status.HTTP_200_OK)
        activation = self.client.post(
            reverse(
                "verification:operations-driver-activate",
                kwargs={"verification_id": self.verification.id},
            ),
            {},
            format="json",
        )
        self.assertEqual(activation.status_code, status.HTTP_200_OK)
        self.verification.refresh_from_db()
        self.verification.profile.refresh_from_db()
        self.assertTrue(self.verification.is_discoverable)

    def test_trusted_adverse_api_result_revokes_approved_driver(self):
        self._approve_and_activate_driver()
        licence_check = next(
            check for check in self.checks
            if check.check_type == DriverVerificationCheck.CheckType.DRIVING_LICENCE
        )
        accepted_evidence = licence_check.evidence.get(
            status=DriverVerificationEvidence.Status.ACCEPTED
        )
        licence_classes = list(licence_check.verified_licence_classes.filter(is_current=True))

        updated = record_government_api_result(
            check_id=licence_check.id,
            provider="authorized-test-provider",
            provider_reference="post-approval-adverse-1",
            outcome=GovernmentVerificationAttempt.Outcome.NOT_MATCHED,
            result_code=DriverVerificationCheck.ResultCode.INVALID,
        )

        updated.refresh_from_db()
        accepted_evidence.refresh_from_db()
        self.verification.refresh_from_db()
        self.verification.profile.refresh_from_db()
        self.assertEqual(updated.status, DriverVerificationCheck.Status.FAILED)
        self.assertEqual(updated.method, DriverVerificationCheck.Method.GOVERNMENT_API)
        self.assertEqual(self.verification.status, DriverVerification.Status.IN_REVIEW)
        self.assertIsNone(self.verification.decided_by)
        self.assertIsNone(self.verification.decided_at)
        self.assertEqual(self.verification.profile.status, DriverProfile.Status.PENDING_ACTIVATION)
        self.assertFalse(self.verification.is_discoverable)
        self.assertEqual(accepted_evidence.status, DriverVerificationEvidence.Status.ACCEPTED)
        self.assertTrue(licence_classes)
        for licence_class in licence_classes:
            licence_class.refresh_from_db()
            self.assertFalse(licence_class.is_current)
            self.assertFalse(licence_class.qualifies_for_discovery)
        self.assertTrue(
            DriverVerificationEvent.objects.filter(
                verification=self.verification,
                verification_check=licence_check,
                event_type=DriverVerificationEvent.EventType.CHECK_INVALIDATED,
                new_status=DriverVerificationCheck.Status.FAILED,
            ).exists()
        )
        self.assertTrue(
            DriverVerificationEvent.objects.filter(
                verification=self.verification,
                event_type=DriverVerificationEvent.EventType.VERIFICATION_REOPENED,
                previous_status=DriverVerification.Status.APPROVED,
                new_status=DriverVerification.Status.IN_REVIEW,
            ).exists()
        )
        self.assertTrue(
            DriverVerificationEvent.objects.filter(
                verification=self.verification,
                event_type=DriverVerificationEvent.EventType.AVAILABILITY_DEACTIVATED,
            ).exists()
        )
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.verification.profile.registration.account,
                event_type="driver.verification.revoked",
            ).exists()
        )

    def test_unavailable_and_error_results_cannot_revoke_approved_verification(self):
        self._approve_and_activate_driver()
        check = next(
            item for item in self.checks
            if item.check_type == DriverVerificationCheck.CheckType.NATIONAL_IDENTITY
        )
        for outcome, reference in (
            (GovernmentVerificationAttempt.Outcome.UNAVAILABLE, "post-approval-unavailable"),
            (GovernmentVerificationAttempt.Outcome.ERROR, "post-approval-error"),
        ):
            with self.assertRaisesMessage(Exception, "Only a definitive adverse provider result"):
                record_government_api_result(
                    check_id=check.id,
                    provider="authorized-test-provider",
                    provider_reference=reference,
                    outcome=outcome,
                )
        check.refresh_from_db()
        self.verification.refresh_from_db()
        self.verification.profile.refresh_from_db()
        self.assertEqual(check.status, DriverVerificationCheck.Status.PASSED)
        self.assertEqual(self.verification.status, DriverVerification.Status.APPROVED)
        self.assertEqual(self.verification.profile.status, DriverProfile.Status.ACTIVE)
        self.assertTrue(self.verification.is_discoverable)
        self.assertFalse(
            GovernmentVerificationAttempt.objects.filter(
                provider="authorized-test-provider",
                provider_reference__in=[
                    "post-approval-unavailable", "post-approval-error",
                ],
            ).exists()
        )

    def test_all_checks_admin_approval_and_activation_are_required_for_discovery(self):
        self._pass_all_checks()
        self.verification.refresh_from_db()
        self.assertEqual(self.verification.status, DriverVerification.Status.IN_REVIEW)
        self.assertFalse(self.verification.is_discoverable)

        licence_check = next(
            check for check in self.checks
            if check.check_type == DriverVerificationCheck.CheckType.DRIVING_LICENCE
        )
        record_verified_licence_classes(
            check_id=licence_check.id,
            reviewer=self.reviewer,
            licence_classes=["C", "CE"],
        )

        self.client.force_authenticate(user=self.admin)
        approval = self.client.post(
            reverse(
                "verification:operations-verification-approve",
                kwargs={"verification_id": self.verification.id},
            ),
            {},
            format="json",
        )
        self.assertEqual(approval.status_code, status.HTTP_200_OK)
        self.verification.refresh_from_db()
        self.assertEqual(self.verification.status, DriverVerification.Status.APPROVED)
        self.assertFalse(self.verification.is_discoverable)

        activation = self.client.post(
            reverse(
                "verification:operations-driver-activate",
                kwargs={"verification_id": self.verification.id},
            ),
            {},
            format="json",
        )
        self.assertEqual(activation.status_code, status.HTTP_200_OK)
        self.verification.profile.refresh_from_db()
        self.assertTrue(self.verification.is_discoverable)

    def test_admin_reopening_invalidates_evidence_and_public_availability(self):
        self._pass_all_checks()
        identity_check = next(
            check for check in self.checks
            if check.check_type == DriverVerificationCheck.CheckType.NATIONAL_IDENTITY
        )
        old_evidence = identity_check.evidence.get(status=DriverVerificationEvidence.Status.ACCEPTED)
        licence_check = next(
            check for check in self.checks
            if check.check_type == DriverVerificationCheck.CheckType.DRIVING_LICENCE
        )
        record_verified_licence_classes(
            check_id=licence_check.id,
            reviewer=self.reviewer,
            licence_classes=["C"],
        )
        self.client.force_authenticate(user=self.admin)
        approved = self.client.post(
            reverse("verification:operations-verification-approve", kwargs={"verification_id": self.verification.id}),
            {},
            format="json",
        )
        self.assertEqual(approved.status_code, status.HTTP_200_OK)
        activated = self.client.post(
            reverse("verification:operations-driver-activate", kwargs={"verification_id": self.verification.id}),
            {},
            format="json",
        )
        self.assertEqual(activated.status_code, status.HTTP_200_OK)
        self.verification.refresh_from_db()
        self.verification.profile.refresh_from_db()
        self.assertTrue(self.verification.is_discoverable)

        reopened = self.client.post(
            reverse("verification:operations-check-reopen", kwargs={"check_id": identity_check.id}),
            {"reason": "Identity evidence requires a current replacement."},
            format="json",
        )
        self.assertEqual(reopened.status_code, status.HTTP_200_OK)
        identity_check.refresh_from_db()
        old_evidence.refresh_from_db()
        self.verification.refresh_from_db()
        self.verification.profile.refresh_from_db()
        self.assertEqual(self.verification.status, DriverVerification.Status.IN_REVIEW)
        self.assertEqual(identity_check.status, DriverVerificationCheck.Status.PENDING)
        self.assertEqual(old_evidence.status, DriverVerificationEvidence.Status.SUPERSEDED)
        self.assertEqual(self.verification.profile.status, DriverProfile.Status.PENDING_ACTIVATION)
        self.assertFalse(self.verification.is_discoverable)
        self.assertFalse(self.verification.checks_are_complete)
        self.assertTrue(
            DriverVerificationEvent.objects.filter(
                verification=self.verification,
                verification_check=identity_check,
                actor=self.admin,
                event_type=DriverVerificationEvent.EventType.CHECK_REOPENED,
            ).exists()
        )
        self.assertTrue(
            DriverVerificationEvent.objects.filter(
                verification=self.verification,
                actor=self.admin,
                event_type=DriverVerificationEvent.EventType.VERIFICATION_REOPENED,
                previous_status=DriverVerification.Status.APPROVED,
                new_status=DriverVerification.Status.IN_REVIEW,
            ).exists()
        )
        self.assertTrue(
            DriverVerificationEvent.objects.filter(
                verification=self.verification,
                actor=self.admin,
                event_type=DriverVerificationEvent.EventType.AVAILABILITY_DEACTIVATED,
            ).exists()
        )

    def test_operator_cannot_reopen_a_final_verification(self):
        self._pass_all_checks()
        self.client.force_authenticate(user=self.admin)
        approved = self.client.post(
            reverse("verification:operations-verification-approve", kwargs={"verification_id": self.verification.id}),
            {},
            format="json",
        )
        self.assertEqual(approved.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.reviewer)
        check = self.checks[0]
        response = self.client.post(
            reverse("verification:operations-check-reopen", kwargs={"check_id": check.id}),
            {"reason": "Attempted operator reopening."},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_expiry_processing_reopens_approved_verification_and_deactivates_driver(self):
        self._pass_all_checks()
        licence_check = next(
            check for check in self.checks
            if check.check_type == DriverVerificationCheck.CheckType.DRIVING_LICENCE
        )
        record_verified_licence_classes(
            check_id=licence_check.id,
            reviewer=self.reviewer,
            licence_classes=["C"],
        )
        self.client.force_authenticate(user=self.admin)
        approval = self.client.post(
            reverse(
                "verification:operations-verification-approve",
                kwargs={"verification_id": self.verification.id},
            ),
            {},
            format="json",
        )
        self.assertEqual(approval.status_code, status.HTTP_200_OK)
        activation = self.client.post(
            reverse(
                "verification:operations-driver-activate",
                kwargs={"verification_id": self.verification.id},
            ),
            {},
            format="json",
        )
        self.assertEqual(activation.status_code, status.HTTP_200_OK)

        identity_check = next(
            check for check in self.checks
            if check.check_type == DriverVerificationCheck.CheckType.NATIONAL_IDENTITY
        )
        evidence = identity_check.evidence.get(status=DriverVerificationEvidence.Status.ACCEPTED)
        expired_at = timezone.now() - timedelta(seconds=1)
        evidence.expires_at = expired_at
        evidence.save(update_fields=["expires_at", "updated_at"])

        result = process_expired_verification_evidence(now=timezone.now())

        evidence.refresh_from_db()
        identity_check.refresh_from_db()
        self.verification.refresh_from_db()
        self.verification.profile.refresh_from_db()
        self.assertEqual(result["evidence_expired"], 1)
        self.assertEqual(result["checks_reopened"], 1)
        self.assertEqual(result["verifications_reopened"], 1)
        self.assertEqual(result["profiles_deactivated"], 1)
        self.assertEqual(evidence.status, DriverVerificationEvidence.Status.EXPIRED)
        self.assertEqual(identity_check.status, DriverVerificationCheck.Status.NEEDS_REVIEW)
        self.assertEqual(self.verification.status, DriverVerification.Status.IN_REVIEW)
        self.assertEqual(self.verification.profile.status, DriverProfile.Status.PENDING_ACTIVATION)
        self.assertFalse(self.verification.is_discoverable)
        self.assertTrue(
            DriverVerificationEvidenceEvent.objects.filter(
                evidence=evidence,
                event_type="expired",
                new_status=DriverVerificationEvidence.Status.EXPIRED,
            ).exists()
        )
        self.assertTrue(
            DriverVerificationEvent.objects.filter(
                verification=self.verification,
                verification_check=identity_check,
                event_type=DriverVerificationEvent.EventType.CHECK_INVALIDATED,
            ).exists()
        )
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.verification.profile.registration.account,
                event_type="driver.verification.evidence_expired",
            ).exists()
        )

    def test_expired_evidence_does_not_invalidate_check_with_another_valid_record(self):
        self._pass_all_checks()
        identity_check = next(
            check for check in self.checks
            if check.check_type == DriverVerificationCheck.CheckType.NATIONAL_IDENTITY
        )
        original = identity_check.evidence.get(status=DriverVerificationEvidence.Status.ACCEPTED)
        DriverVerificationEvidence.objects.create(
            verification_check=identity_check,
            evidence_type=identity_check.check_type,
            source=DriverVerificationEvidence.Source.OPERATIONS_UPLOAD,
            status=DriverVerificationEvidence.Status.ACCEPTED,
            scan_status=DriverVerificationEvidence.ScanStatus.CLEAN,
            storage_key="verification-evidence/second-valid-identity",
            uploaded_by=self.verification.profile.registration.account,
            reviewed_by=self.reviewer,
            expires_at=timezone.now() + timedelta(days=30),
        )
        original.expires_at = timezone.now() - timedelta(seconds=1)
        original.save(update_fields=["expires_at", "updated_at"])

        result = process_expired_verification_evidence(now=timezone.now())

        identity_check.refresh_from_db()
        self.assertEqual(result["evidence_expired"], 1)
        self.assertEqual(result["checks_reopened"], 0)
        self.assertEqual(identity_check.status, DriverVerificationCheck.Status.PASSED)
        self.assertTrue(
            identity_check.has_trusted_supporting_record(
                method=DriverVerificationCheck.Method.MANUAL
            )
        )

    def test_expired_licence_evidence_invalidates_current_licence_classes(self):
        self._pass_all_checks()
        licence_check = next(
            check for check in self.checks
            if check.check_type == DriverVerificationCheck.CheckType.DRIVING_LICENCE
        )
        records = record_verified_licence_classes(
            check_id=licence_check.id,
            reviewer=self.reviewer,
            licence_classes=["C", "CE"],
        )
        evidence = licence_check.evidence.get(status=DriverVerificationEvidence.Status.ACCEPTED)
        evidence.expires_at = timezone.now() - timedelta(seconds=1)
        evidence.save(update_fields=["expires_at", "updated_at"])

        process_expired_verification_evidence(now=timezone.now())

        licence_check.refresh_from_db()
        for record in records:
            record.refresh_from_db()
            self.assertFalse(record.is_current)
            self.assertFalse(record.qualifies_for_discovery)
        self.assertEqual(licence_check.status, DriverVerificationCheck.Status.NEEDS_REVIEW)

    def test_expiry_processing_dry_run_makes_no_changes(self):
        self._pass_all_checks()
        identity_check = next(
            check for check in self.checks
            if check.check_type == DriverVerificationCheck.CheckType.NATIONAL_IDENTITY
        )
        evidence = identity_check.evidence.get(status=DriverVerificationEvidence.Status.ACCEPTED)
        evidence.expires_at = timezone.now() - timedelta(seconds=1)
        evidence.save(update_fields=["expires_at", "updated_at"])

        result = process_expired_verification_evidence(
            now=timezone.now(),
            dry_run=True,
        )

        evidence.refresh_from_db()
        identity_check.refresh_from_db()
        self.assertTrue(result["dry_run"])
        self.assertEqual(result["evidence_expired"], 1)
        self.assertEqual(result["checks_to_reopen"], 1)
        self.assertEqual(evidence.status, DriverVerificationEvidence.Status.ACCEPTED)
        self.assertEqual(identity_check.status, DriverVerificationCheck.Status.PASSED)

    def test_expired_evidence_invalidates_verification_completion(self):
        self._pass_all_checks()
        identity_check = next(
            check for check in self.checks
            if check.check_type == DriverVerificationCheck.CheckType.NATIONAL_IDENTITY
        )
        evidence = identity_check.evidence.get(status=DriverVerificationEvidence.Status.ACCEPTED)
        evidence.expires_at = timezone.now() - timedelta(seconds=1)
        evidence.save(update_fields=["expires_at", "updated_at"])
        self.assertFalse(self.verification.checks_are_complete)

    def test_discovery_rechecks_result_codes_even_if_status_says_passed(self):
        self._pass_all_checks()
        licence_check = next(
            check for check in self.checks
            if check.check_type == DriverVerificationCheck.CheckType.DRIVING_LICENCE
        )
        record_verified_licence_classes(
            check_id=licence_check.id,
            reviewer=self.reviewer,
            licence_classes=["C"],
        )
        identity_check = next(
            check for check in self.checks
            if check.check_type == DriverVerificationCheck.CheckType.NATIONAL_IDENTITY
        )
        DriverVerificationCheck.objects.filter(pk=identity_check.pk).update(
            result_code=DriverVerificationCheck.ResultCode.MISMATCH
        )
        self.assertFalse(self.verification.is_discoverable)

    def test_licence_classes_cannot_be_recorded_before_validation(self):
        licence_check = next(
            check for check in self.checks
            if check.check_type == DriverVerificationCheck.CheckType.DRIVING_LICENCE
        )
        with self.assertRaisesMessage(Exception, "only be recorded after"):
            record_verified_licence_classes(
                check_id=licence_check.id,
                reviewer=self.reviewer,
                licence_classes=["C"],
            )

    def test_operations_user_can_record_validated_licence_classes(self):
        self._pass_all_checks()
        licence_check = next(
            check for check in self.checks
            if check.check_type == DriverVerificationCheck.CheckType.DRIVING_LICENCE
        )
        self.client.force_authenticate(user=self.reviewer)
        url = reverse(
            "verification:operations-verified-licence-classes",
            kwargs={"check_id": licence_check.id},
        )
        response = self.client.post(
            url, {"licence_classes": ["C", "CE"]}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [item["licence_class"] for item in response.data], ["C", "CE"]
        )
        self.assertTrue(
            DriverVerificationEvent.objects.filter(
                verification=self.verification,
                verification_check=licence_check,
                actor=self.reviewer,
                event_type=DriverVerificationEvent.EventType.LICENCE_CLASSES_RECORDED,
            ).exists()
        )

    def test_invalid_licence_cannot_be_marked_passed(self):
        licence_check = next(
            check for check in self.checks
            if check.check_type == DriverVerificationCheck.CheckType.DRIVING_LICENCE
        )
        with self.assertRaisesMessage(Exception, "invalid licence result must use the failed status"):
            review_driver_check(
                check_id=licence_check.id,
                reviewer=self.reviewer,
                status=DriverVerificationCheck.Status.PASSED,
                result_code=DriverVerificationCheck.ResultCode.INVALID,
            )

    def test_identity_mismatch_cannot_be_marked_passed(self):
        check = next(
            item for item in self.checks
            if item.check_type == DriverVerificationCheck.CheckType.NATIONAL_IDENTITY
        )
        with self.assertRaisesMessage(Exception, "only pass when its result confirms"):
            review_driver_check(
                check_id=check.id,
                reviewer=self.reviewer,
                status=DriverVerificationCheck.Status.PASSED,
                result_code=DriverVerificationCheck.ResultCode.MISMATCH,
            )

    def test_record_found_cannot_be_marked_passed(self):
        check = next(
            item for item in self.checks
            if item.check_type == DriverVerificationCheck.CheckType.TRAFFIC_RECORDS
        )
        with self.assertRaisesMessage(Exception, "only pass when its result confirms"):
            review_driver_check(
                check_id=check.id,
                reviewer=self.reviewer,
                status=DriverVerificationCheck.Status.PASSED,
                result_code=DriverVerificationCheck.ResultCode.RECORD_FOUND,
            )

    def test_check_cannot_pass_without_a_result(self):
        check = next(
            item for item in self.checks
            if item.check_type == DriverVerificationCheck.CheckType.NATIONAL_IDENTITY
        )
        with self.assertRaisesMessage(Exception, "only pass when its result confirms"):
            review_driver_check(
                check_id=check.id,
                reviewer=self.reviewer,
                status=DriverVerificationCheck.Status.PASSED,
                result_code="",
            )

    def test_inconclusive_result_cannot_be_marked_passed(self):
        check = next(
            item for item in self.checks
            if item.check_type == DriverVerificationCheck.CheckType.NATIONAL_IDENTITY
        )
        with self.assertRaisesMessage(Exception, "inconclusive result requires further review"):
            review_driver_check(
                check_id=check.id,
                reviewer=self.reviewer,
                status=DriverVerificationCheck.Status.PASSED,
                result_code=DriverVerificationCheck.ResultCode.INCONCLUSIVE,
            )

    def test_failed_check_rejects_verification(self):
        review_driver_check(
            check_id=self.checks[0].id,
            reviewer=self.reviewer,
            status=DriverVerificationCheck.Status.FAILED,
            result_code=DriverVerificationCheck.ResultCode.RECORD_FOUND,
        )
        self.verification.refresh_from_db()
        self.assertEqual(self.verification.status, DriverVerification.Status.REJECTED)
        self.assertFalse(self.verification.is_discoverable)
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.verification.profile.registration.account,
                recipient_role=Notification.RecipientRole.DRIVER,
                event_type="driver.verification.rejected",
            ).exists()
        )
