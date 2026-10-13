from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from apps.identity.models import Account
from apps.operations.models import OperationsMembership
from apps.performance.models import DriverScore, ScoreHistory
from apps.performance.services.baselines import BASELINE_SCORE, establish_driver_baseline
from apps.profiles.models import DriverProfile
from apps.registrations.models import DriverRegistration


class BaselineEstablishmentTests(TestCase):
    def setUp(self):
        self.admin = Account.objects.create_user(email="baseline-admin@example.test", password="safe-test-password")
        OperationsMembership.objects.create(account=self.admin, role=OperationsMembership.Role.ADMIN, approved_by=self.admin)
        self.operator = Account.objects.create_user(email="baseline-operator@example.test", password="safe-test-password")
        OperationsMembership.objects.create(account=self.operator, role=OperationsMembership.Role.OPERATOR, approved_by=self.admin)
        driver_account = Account.objects.create_user(email="baseline-driver@example.test", password="safe-test-password")
        registration = DriverRegistration.objects.create(
            account=driver_account, first_name="Baseline", middle_name="", last_name="Driver",
            nationality="Tanzanian", region="Dar es Salaam", district="Ilala",
            current_residential_address="Test residential area",
            driving_experience=DriverRegistration.ExperienceLevel.ONE_TO_THREE_YEARS,
        )
        self.driver = DriverProfile.objects.create(registration=registration)
        self.score = DriverScore.objects.create(driver=self.driver, calculated_score=None)

    def establish(self, **overrides):
        values = {
            "score_id": self.score.pk, "actor": self.admin,
            "verification_confirmed": True, "history_reviewed": True,
            "applicable_history_found": True,
            "reason": "Verification confirmed and applicable history reviewed by Admin.",
        }
        values.update(overrides)
        return establish_driver_baseline(**values)

    def test_admin_can_establish_baseline_after_required_checks(self):
        score, history = self.establish()
        self.assertEqual(score.calculated_score, BASELINE_SCORE)
        self.assertEqual(history.change_type, ScoreHistory.ChangeType.BASELINE)
        self.assertIsNone(history.previous_score)
        self.assertEqual(history.new_score, 80)
        self.assertEqual(ScoreHistory.objects.count(), 1)

    def test_missing_history_keeps_score_unset_until_policy_is_finalized(self):
        with self.assertRaises(ValidationError):
            self.establish(applicable_history_found=False)
        self.score.refresh_from_db()
        self.assertIsNone(self.score.calculated_score)
        self.assertEqual(ScoreHistory.objects.count(), 0)

    def test_verification_must_be_confirmed(self):
        with self.assertRaises(ValidationError):
            self.establish(verification_confirmed=False)
        self.score.refresh_from_db()
        self.assertIsNone(self.score.calculated_score)

    def test_operator_cannot_establish_baseline(self):
        with self.assertRaises(PermissionDenied):
            self.establish(actor=self.operator)
        self.score.refresh_from_db()
        self.assertIsNone(self.score.calculated_score)

    def test_baseline_cannot_be_established_twice(self):
        self.establish()
        with self.assertRaises(ValidationError):
            self.establish()
        self.assertEqual(ScoreHistory.objects.count(), 1)
