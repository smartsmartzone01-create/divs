from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from apps.identity.models import Account
from apps.operations.models import OperationsMembership
from apps.performance.models import (
    AvailabilityRestriction,
    AvailabilityRestrictionDecision,
    DriverScore,
    PerformanceAppeal,
    PerformanceAppealDecision,
    PerformanceEvent,
)
from apps.performance.services.appeals import (
    decide_performance_appeal,
    submit_performance_appeal,
)
from apps.performance.services.availability import (
    apply_low_score_restriction,
    has_active_performance_restriction,
    place_critical_incident_restriction,
    release_availability_restriction,
)
from apps.profiles.models import DriverProfile
from apps.registrations.models import DriverRegistration


class AppealAndAvailabilityWorkflowTests(TestCase):
    def setUp(self):
        self.admin = Account.objects.create_user(
            email="admin-appeals@example.test",
            password="safe-test-password",
        )
        OperationsMembership.objects.create(
            account=self.admin,
            role=OperationsMembership.Role.ADMIN,
            approved_by=self.admin,
        )
        self.operator = Account.objects.create_user(
            email="operator-appeals@example.test",
            password="safe-test-password",
        )
        OperationsMembership.objects.create(
            account=self.operator,
            role=OperationsMembership.Role.OPERATOR,
            approved_by=self.admin,
        )
        self.driver_account = Account.objects.create_user(
            email="driver-appeals@example.test",
            password="safe-test-password",
        )
        registration = DriverRegistration.objects.create(
            account=self.driver_account,
            first_name="Appeal",
            middle_name="",
            last_name="Driver",
            nationality="Tanzanian",
            region="Dar es Salaam",
            district="Ilala",
            current_residential_address="Test residential area",
            driving_experience=DriverRegistration.ExperienceLevel.ONE_TO_THREE_YEARS,
        )
        self.driver = DriverProfile.objects.create(registration=registration)
        self.event = PerformanceEvent.objects.create(
            driver=self.driver,
            category=PerformanceEvent.Category.NEGATIVE,
            severity=PerformanceEvent.Severity.SERIOUS,
            status=PerformanceEvent.Status.APPROVED,
            title="Confirmed incident",
        )
        self.score = DriverScore.objects.create(driver=self.driver, calculated_score=35)

    def test_pending_appeal_does_not_change_score_or_existing_restriction(self):
        restriction = apply_low_score_restriction(
            score_id=self.score.pk,
            actor=self.operator,
            reason="Effective score is below the agreed threshold.",
        )
        self.assertIsNotNone(restriction)

        appeal = submit_performance_appeal(
            event_id=self.event.pk,
            appellant=self.driver_account,
            reason="I believe the incident decision used incorrect information.",
            evidence_references=["evidence://appeal/123"],
        )

        self.score.refresh_from_db()
        restriction.refresh_from_db()
        self.assertEqual(appeal.status, PerformanceAppeal.Status.PENDING)
        self.assertEqual(self.score.effective_score, 35)
        self.assertEqual(restriction.status, AvailabilityRestriction.Status.ACTIVE)
        self.assertTrue(has_active_performance_restriction(driver_id=self.driver.pk))

    def test_only_driver_account_can_submit_appeal(self):
        with self.assertRaises(PermissionDenied):
            submit_performance_appeal(
                event_id=self.event.pk,
                appellant=self.operator,
                reason="Trying to appeal for another driver.",
            )

    def test_successful_appeal_is_audited_and_flags_correction(self):
        appeal = submit_performance_appeal(
            event_id=self.event.pk,
            appellant=self.driver_account,
            reason="The evidence was incomplete.",
        )
        appeal, history = decide_performance_appeal(
            appeal_id=appeal.pk,
            reviewer=self.admin,
            decision=PerformanceAppeal.Status.UPHELD,
            reason="Appeal upheld after reviewing additional evidence.",
        )

        self.score.refresh_from_db()
        self.assertEqual(appeal.status, PerformanceAppeal.Status.UPHELD)
        self.assertTrue(appeal.correction_required)
        self.assertEqual(history.status, PerformanceAppeal.Status.UPHELD)
        self.assertEqual(PerformanceAppealDecision.objects.count(), 1)
        # The correction engine is not active yet; no score is silently changed.
        self.assertEqual(self.score.calculated_score, 35)

    def test_low_score_restriction_uses_strictly_below_40_threshold(self):
        self.score.calculated_score = 40
        self.score.save(update_fields=["calculated_score", "updated_at"])
        result = apply_low_score_restriction(
            score_id=self.score.pk,
            actor=self.operator,
            reason="Threshold boundary check.",
        )
        self.assertIsNone(result)

        self.score.calculated_score = 39
        self.score.save(update_fields=["calculated_score", "updated_at"])
        result = apply_low_score_restriction(
            score_id=self.score.pk,
            actor=self.operator,
            reason="Score is below threshold.",
        )
        self.assertEqual(result.kind, AvailabilityRestriction.Kind.LOW_SCORE)

    def test_operator_cannot_release_low_score_restriction(self):
        restriction = apply_low_score_restriction(
            score_id=self.score.pk,
            actor=self.operator,
            reason="Score is below threshold.",
        )
        with self.assertRaises(PermissionDenied):
            release_availability_restriction(
                restriction_id=restriction.pk,
                actor=self.operator,
                reason="Operator attempted restoration.",
            )
        restriction.refresh_from_db()
        self.assertEqual(restriction.status, AvailabilityRestriction.Status.ACTIVE)

    def test_critical_incident_places_temporary_restriction_and_review_state(self):
        self.event.severity = PerformanceEvent.Severity.CRITICAL
        self.event.status = PerformanceEvent.Status.SUBMITTED
        self.event.save(update_fields=["severity", "status", "updated_at"])

        restriction = place_critical_incident_restriction(
            event_id=self.event.pk,
            actor=self.operator,
            reason="Credible critical report requires precautionary review.",
        )

        self.event.refresh_from_db()
        self.assertEqual(self.event.status, PerformanceEvent.Status.UNDER_REVIEW)
        self.assertEqual(restriction.kind, AvailabilityRestriction.Kind.CRITICAL_INCIDENT)
        self.assertEqual(restriction.status, AvailabilityRestriction.Status.ACTIVE)
        self.assertEqual(AvailabilityRestrictionDecision.objects.count(), 1)
        self.assertTrue(has_active_performance_restriction(driver_id=self.driver.pk))

    def test_released_restriction_keeps_history_and_no_longer_blocks_availability(self):
        restriction = apply_low_score_restriction(
            score_id=self.score.pk,
            actor=self.operator,
            reason="Score is below threshold.",
        )
        released = release_availability_restriction(
            restriction_id=restriction.pk,
            actor=self.admin,
            reason="Admin reviewed the restriction and approves restoration.",
        )

        self.assertEqual(released.status, AvailabilityRestriction.Status.RELEASED)
        self.assertEqual(AvailabilityRestrictionDecision.objects.count(), 2)
        self.assertFalse(has_active_performance_restriction(driver_id=self.driver.pk))

    def test_second_pending_appeal_for_same_event_is_rejected(self):
        submit_performance_appeal(
            event_id=self.event.pk,
            appellant=self.driver_account,
            reason="First appeal.",
        )
        with self.assertRaises(ValidationError):
            submit_performance_appeal(
                event_id=self.event.pk,
                appellant=self.driver_account,
                reason="Duplicate pending appeal.",
            )
