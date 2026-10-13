from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from apps.identity.models import Account
from apps.operations.models import OperationsMembership
from apps.performance.models import (
    DriverScore,
    PerformanceEvent,
    PerformanceEventScoreApplication,
    PerformanceScoringRule,
    ScoreHistory,
)
from apps.performance.services.scoring import apply_approved_event_score
from apps.performance.services.scoring_rules import (
    approve_scoring_rule,
    propose_scoring_rule,
)
from apps.profiles.models import DriverProfile
from apps.registrations.models import DriverRegistration


class ScoringEngineTests(TestCase):
    def setUp(self):
        self.admin = Account.objects.create_user(
            email="scoring-admin@example.test",
            password="safe-test-password",
        )
        OperationsMembership.objects.create(
            account=self.admin,
            role=OperationsMembership.Role.ADMIN,
            approved_by=self.admin,
        )
        self.operator = Account.objects.create_user(
            email="scoring-operator@example.test",
            password="safe-test-password",
        )
        OperationsMembership.objects.create(
            account=self.operator,
            role=OperationsMembership.Role.OPERATOR,
            approved_by=self.admin,
        )
        driver_account = Account.objects.create_user(
            email="scoring-driver@example.test",
            password="safe-test-password",
        )
        registration = DriverRegistration.objects.create(
            account=driver_account,
            first_name="Test",
            middle_name="",
            last_name="Driver",
            nationality="Tanzanian",
            region="Dar es Salaam",
            district="Ilala",
            current_residential_address="Test residential area",
            driving_experience=DriverRegistration.ExperienceLevel.ONE_TO_THREE_YEARS,
        )
        self.driver = DriverProfile.objects.create(registration=registration)
        self.score = DriverScore.objects.create(driver=self.driver, calculated_score=80)
        self.event = PerformanceEvent.objects.create(
            driver=self.driver,
            category=PerformanceEvent.Category.NEGATIVE,
            event_code="minor_traffic_violation",
            severity=PerformanceEvent.Severity.MINOR,
            status=PerformanceEvent.Status.APPROVED,
            title="Confirmed minor incident",
        )

    def propose_and_approve(self, *, points_delta=-3, category=PerformanceScoringRule.Category.NEGATIVE):
        rule = propose_scoring_rule(
            actor=self.admin,
            name="Test approved rule",
            category=category,
            event_code="minor_traffic_violation",
            severity=PerformanceEvent.Severity.MINOR,
            points_delta=points_delta,
            reason="Test-only rule for service behavior.",
        )
        self.assertEqual(rule.status, PerformanceScoringRule.Status.PROPOSED)
        self.assertIsNone(apply_approved_event_score(event_id=self.event.pk, actor=self.admin))
        rule = approve_scoring_rule(rule_id=rule.pk, actor=self.admin)
        return rule

    def test_proposed_rule_does_not_change_score_until_approved(self):
        rule = propose_scoring_rule(
            actor=self.admin,
            name="Proposed deduction",
            category=PerformanceScoringRule.Category.NEGATIVE,
            event_code="minor_traffic_violation",
            severity=PerformanceEvent.Severity.MINOR,
            points_delta=-3,
            reason="Not yet approved.",
        )
        self.assertEqual(rule.status, PerformanceScoringRule.Status.PROPOSED)
        self.assertEqual(self.score.calculated_score, 80)
        self.assertEqual(ScoreHistory.objects.count(), 0)

    def test_operator_cannot_propose_scoring_rule(self):
        with self.assertRaises(PermissionDenied):
            propose_scoring_rule(
                actor=self.operator,
                name="Unauthorized rule",
                category=PerformanceScoringRule.Category.NEGATIVE,
                event_code="minor_traffic_violation",
                severity=PerformanceEvent.Severity.MINOR,
                points_delta=-3,
                reason="Should be rejected.",
            )

    def test_rule_points_must_match_category_direction(self):
        with self.assertRaises(ValidationError):
            propose_scoring_rule(
                actor=self.admin,
                name="Wrong sign",
                category=PerformanceScoringRule.Category.NEGATIVE,
                event_code="minor_traffic_violation",
                severity=PerformanceEvent.Severity.MINOR,
                points_delta=3,
                reason="Negative rules must deduct points.",
            )

    def test_approved_event_changes_score_once_and_records_history(self):
        self.propose_and_approve(points_delta=-3)
        application = apply_approved_event_score(event_id=self.event.pk, actor=self.admin)
        self.score.refresh_from_db()

        self.assertEqual(self.score.calculated_score, 77)
        self.assertEqual(application.previous_score, 80)
        self.assertEqual(application.new_score, 77)
        self.assertEqual(application.points_delta, -3)
        self.assertEqual(PerformanceEventScoreApplication.objects.count(), 1)
        self.assertEqual(ScoreHistory.objects.count(), 1)

        repeated = apply_approved_event_score(event_id=self.event.pk, actor=self.admin)
        self.score.refresh_from_db()
        self.assertEqual(repeated.pk, application.pk)
        self.assertEqual(self.score.calculated_score, 77)
        self.assertEqual(ScoreHistory.objects.count(), 1)

    def test_score_is_clamped_at_zero(self):
        self.score.calculated_score = 2
        self.score.save(update_fields=["calculated_score", "updated_at"])
        self.propose_and_approve(points_delta=-10)
        application = apply_approved_event_score(event_id=self.event.pk, actor=self.admin)
        self.score.refresh_from_db()
        self.assertEqual(self.score.calculated_score, 0)
        self.assertEqual(application.new_score, 0)

    def test_no_established_calculated_score_means_no_score_effect(self):
        self.score.calculated_score = None
        self.score.save(update_fields=["calculated_score", "updated_at"])
        self.propose_and_approve(points_delta=-3)
        result = apply_approved_event_score(event_id=self.event.pk, actor=self.admin)
        self.score.refresh_from_db()
        self.assertIsNone(result)
        self.assertIsNone(self.score.calculated_score)
        self.assertEqual(ScoreHistory.objects.count(), 0)

    def test_positive_rule_must_add_points(self):
        with self.assertRaises(ValidationError):
            propose_scoring_rule(
                actor=self.admin,
                name="Invalid positive rule",
                category=PerformanceScoringRule.Category.POSITIVE,
                event_code="minor_traffic_violation",
                severity=PerformanceEvent.Severity.MINOR,
                points_delta=-2,
                reason="A positive event must add points.",
            )
