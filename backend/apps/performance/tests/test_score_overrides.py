from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from apps.identity.models import Account
from apps.operations.models import OperationsMembership
from apps.performance.models import DriverScore, ScoreHistory
from apps.performance.services.score_overrides import override_driver_score
from apps.profiles.models import DriverProfile
from apps.registrations.models import DriverRegistration


class ScoreOverrideServiceTests(TestCase):
    def setUp(self):
        self.admin = Account.objects.create_user(email="admin@example.test", password="safe-test-password")
        OperationsMembership.objects.create(
            account=self.admin,
            role=OperationsMembership.Role.ADMIN,
            approved_by=self.admin,
        )
        account = Account.objects.create_user(email="driver@example.test", password="safe-test-password")
        registration = DriverRegistration.objects.create(
            account=account,
            first_name="Test",
            middle_name="",
            last_name="Driver",
            nationality="Tanzanian",
            region="Dar es Salaam",
            district="Ilala",
            current_residential_address="Test residential area",
            driving_experience=DriverRegistration.ExperienceLevel.ONE_TO_THREE_YEARS,
        )
        driver = DriverProfile.objects.create(registration=registration)
        self.score = DriverScore.objects.create(driver=driver, calculated_score=80)

    def test_admin_override_preserves_calculated_score_and_creates_history(self):
        score, history = override_driver_score(
            score_id=self.score.pk,
            actor=self.admin,
            new_score=61,
            reason="Documented administrative review.",
        )

        self.assertEqual(score.calculated_score, 80)
        self.assertEqual(score.manual_override_score, 61)
        self.assertEqual(score.effective_score, 61)
        self.assertEqual(history.previous_score, 80)
        self.assertEqual(history.new_score, 61)
        self.assertEqual(history.change_amount, -19)
        self.assertEqual(history.actor, self.admin)
        self.assertEqual(ScoreHistory.objects.count(), 1)

    def test_operator_cannot_override_score(self):
        operator = Account.objects.create_user(email="operator@example.test", password="safe-test-password")
        OperationsMembership.objects.create(
            account=operator,
            role=OperationsMembership.Role.OPERATOR,
            approved_by=self.admin,
        )

        with self.assertRaises(PermissionDenied):
            override_driver_score(
                score_id=self.score.pk,
                actor=operator,
                new_score=50,
                reason="Operator attempted override.",
            )

        self.score.refresh_from_db()
        self.assertEqual(self.score.calculated_score, 80)
        self.assertIsNone(self.score.manual_override_score)
        self.assertEqual(ScoreHistory.objects.count(), 0)

    def test_override_requires_valid_score_and_reason(self):
        with self.assertRaises(ValidationError):
            override_driver_score(
                score_id=self.score.pk,
                actor=self.admin,
                new_score=101,
                reason="Out of range.",
            )
        with self.assertRaises(ValidationError):
            override_driver_score(
                score_id=self.score.pk,
                actor=self.admin,
                new_score=70,
                reason="   ",
            )

        self.assertEqual(ScoreHistory.objects.count(), 0)
