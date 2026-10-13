from django.core.exceptions import PermissionDenied
from django.test import TestCase

from apps.identity.models import Account
from apps.operations.models import OperationsMembership
from apps.performance.models import (
    AvailabilityRestriction,
    DriverScore,
    PerformanceAppeal,
    PerformanceEvent,
    PerformanceEventScoreApplication,
    PerformanceScoringRule,
    ScoreHistory,
)
from apps.performance.services.appeals import decide_performance_appeal, submit_performance_appeal
from apps.performance.services.availability import apply_low_score_restriction
from apps.performance.services.score_corrections import correct_score_after_upheld_appeal
from apps.profiles.models import DriverProfile
from apps.registrations.models import DriverRegistration


class ScoreCorrectionTests(TestCase):
    def setUp(self):
        self.admin = Account.objects.create_user(
            email="correction-admin@example.test",
            password="safe-test-password",
        )
        OperationsMembership.objects.create(
            account=self.admin,
            role=OperationsMembership.Role.ADMIN,
            approved_by=self.admin,
        )
        self.operator = Account.objects.create_user(
            email="correction-operator@example.test",
            password="safe-test-password",
        )
        OperationsMembership.objects.create(
            account=self.operator,
            role=OperationsMembership.Role.OPERATOR,
            approved_by=self.admin,
        )
        self.driver_account = Account.objects.create_user(
            email="correction-driver@example.test",
            password="safe-test-password",
        )
        registration = DriverRegistration.objects.create(
            account=self.driver_account,
            first_name="Correction",
            middle_name="",
            last_name="Driver",
            nationality="Tanzanian",
            region="Dar es Salaam",
            district="Ilala",
            current_residential_address="Test residential area",
            driving_experience=DriverRegistration.ExperienceLevel.ONE_TO_THREE_YEARS,
        )
        self.driver = DriverProfile.objects.create(registration=registration)
        self.score = DriverScore.objects.create(driver=self.driver, calculated_score=75)
        self.event = PerformanceEvent.objects.create(
            driver=self.driver,
            category=PerformanceEvent.Category.NEGATIVE,
            event_code="minor_traffic_violation",
            severity=PerformanceEvent.Severity.MINOR,
            status=PerformanceEvent.Status.APPROVED,
            title="Incident later overturned on appeal",
        )
        self.rule = PerformanceScoringRule.objects.create(
            name="Minor traffic violation",
            category=PerformanceScoringRule.Category.NEGATIVE,
            event_code="minor_traffic_violation",
            severity=PerformanceEvent.Severity.MINOR,
            points_delta=-5,
            status=PerformanceScoringRule.Status.APPROVED,
            reason="Test fixture rule.",
            created_by=self.admin,
            approved_by=self.admin,
        )
        PerformanceEventScoreApplication.objects.create(
            event=self.event,
            score=self.score,
            rule=self.rule,
            rule_name_snapshot=self.rule.name,
            points_delta=-5,
            previous_score=80,
            new_score=75,
            reason="Applied test rule.",
        )
        ScoreHistory.objects.create(
            score=self.score,
            event=self.event,
            change_type=ScoreHistory.ChangeType.EVENT,
            previous_score=80,
            new_score=75,
            reason="Applied test rule.",
            rule_reference=str(self.rule.pk),
            actor=self.admin,
        )

    def make_upheld_appeal(self):
        appeal = submit_performance_appeal(
            event_id=self.event.pk,
            appellant=self.driver_account,
            reason="The report was found to be incorrect.",
        )
        appeal, _ = decide_performance_appeal(
            appeal_id=appeal.pk,
            reviewer=self.admin,
            decision=PerformanceAppeal.Status.UPHELD,
            reason="Appeal upheld after review.",
        )
        return appeal

    def test_upheld_appeal_recalculates_score_and_preserves_original_application(self):
        appeal = self.make_upheld_appeal()
        original_application = PerformanceEventScoreApplication.objects.get(event=self.event)

        correction = correct_score_after_upheld_appeal(
            appeal_id=appeal.pk,
            actor=self.admin,
            reason="Remove overturned event and replay remaining approved scoring history.",
        )
        self.score.refresh_from_db()
        appeal.refresh_from_db()

        self.assertEqual(self.score.calculated_score, 80)
        self.assertEqual(correction.previous_calculated_score, 75)
        self.assertEqual(correction.new_calculated_score, 80)
        self.assertFalse(appeal.correction_required)
        self.assertEqual(
            PerformanceEventScoreApplication.objects.get(event=self.event).pk,
            original_application.pk,
        )
        self.assertEqual(
            ScoreHistory.objects.filter(change_type=ScoreHistory.ChangeType.CORRECTION).count(),
            1,
        )

    def test_operator_cannot_apply_successful_appeal_correction(self):
        appeal = self.make_upheld_appeal()
        with self.assertRaises(PermissionDenied):
            correct_score_after_upheld_appeal(
                appeal_id=appeal.pk,
                actor=self.operator,
                reason="Operator cannot apply correction.",
            )

    def test_correction_does_not_release_existing_restriction_or_clear_override(self):
        self.score.calculated_score = 35
        self.score.manual_override_score = 38
        self.score.manual_override_reason = "Temporary Admin review override."
        self.score.manual_override_by = self.admin
        self.score.save(update_fields=[
            "calculated_score",
            "manual_override_score",
            "manual_override_reason",
            "manual_override_by",
            "updated_at",
        ])
        restriction = apply_low_score_restriction(
            score_id=self.score.pk,
            actor=self.admin,
            reason="Existing low-score restriction.",
        )
        appeal = self.make_upheld_appeal()

        correct_score_after_upheld_appeal(
            appeal_id=appeal.pk,
            actor=self.admin,
            reason="Correct score after appeal.",
        )
        self.score.refresh_from_db()
        restriction.refresh_from_db()
        self.assertEqual(restriction.status, AvailabilityRestriction.Status.ACTIVE)
        self.assertEqual(self.score.manual_override_score, 38)

    def test_correction_replays_later_event_applications(self):
        later_event = PerformanceEvent.objects.create(
            driver=self.driver,
            category=PerformanceEvent.Category.NEGATIVE,
            event_code="late_delivery",
            severity=PerformanceEvent.Severity.MINOR,
            status=PerformanceEvent.Status.APPROVED,
            title="Later event remains valid",
        )
        later_rule = PerformanceScoringRule.objects.create(
            name="Late delivery",
            category=PerformanceScoringRule.Category.NEGATIVE,
            event_code="late_delivery",
            severity=PerformanceEvent.Severity.MINOR,
            points_delta=-3,
            status=PerformanceScoringRule.Status.APPROVED,
            reason="Test fixture rule.",
            created_by=self.admin,
            approved_by=self.admin,
        )
        PerformanceEventScoreApplication.objects.create(
            event=later_event,
            score=self.score,
            rule=later_rule,
            rule_name_snapshot=later_rule.name,
            points_delta=-3,
            previous_score=72,
            new_score=72,
            reason="Later event application fixture.",
        )
        self.score.calculated_score = 72
        self.score.save(update_fields=["calculated_score", "updated_at"])
        appeal = self.make_upheld_appeal()

        correct_score_after_upheld_appeal(
            appeal_id=appeal.pk,
            actor=self.admin,
            reason="Remove overturned first event and replay the remaining event.",
        )
        self.score.refresh_from_db()
        # Starting from 80, retain the later -3 event but exclude the overturned -5 event.
        self.assertEqual(self.score.calculated_score, 77)
