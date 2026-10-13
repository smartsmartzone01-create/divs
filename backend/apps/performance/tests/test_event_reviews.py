from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.identity.models import Account
from apps.operations.models import OperationsMembership
from apps.performance.models import PerformanceEvent, PerformanceEventReview
from apps.performance.services.event_reviews import review_performance_event
from apps.profiles.models import DriverProfile
from apps.registrations.models import DriverRegistration


class PerformanceEventReviewServiceTests(TestCase):
    def setUp(self):
        self.admin = Account.objects.create_user(email="admin-review@example.test", password="safe-test-password")
        OperationsMembership.objects.create(
            account=self.admin,
            role=OperationsMembership.Role.ADMIN,
            approved_by=self.admin,
        )
        self.operator = Account.objects.create_user(email="operator-review@example.test", password="safe-test-password")
        OperationsMembership.objects.create(
            account=self.operator,
            role=OperationsMembership.Role.OPERATOR,
            approved_by=self.admin,
        )
        driver_account = Account.objects.create_user(email="driver-review@example.test", password="safe-test-password")
        registration = DriverRegistration.objects.create(
            account=driver_account,
            first_name="Review",
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
            title="Reported driving incident",
        )

    def test_operator_decision_updates_current_state_and_preserves_review_history(self):
        event, review = review_performance_event(
            event_id=self.event.pk,
            reviewer=self.operator,
            decision=PerformanceEventReview.Decision.MORE_EVIDENCE,
            reason="The current report is incomplete.",
            requested_evidence="Provide the incident date and source reference.",
        )

        self.assertEqual(event.status, PerformanceEvent.Status.MORE_EVIDENCE)
        self.assertEqual(event.reviewed_by, self.operator)
        self.assertEqual(review.reviewer, self.operator)
        self.assertEqual(review.requested_evidence, "Provide the incident date and source reference.")
        self.assertEqual(PerformanceEventReview.objects.count(), 1)

    def test_more_evidence_decision_requires_details(self):
        with self.assertRaises(ValidationError):
            review_performance_event(
                event_id=self.event.pk,
                reviewer=self.operator,
                decision=PerformanceEventReview.Decision.MORE_EVIDENCE,
                reason="More information is needed.",
            )

        self.event.refresh_from_db()
        self.assertEqual(self.event.status, PerformanceEvent.Status.SUBMITTED)
        self.assertEqual(PerformanceEventReview.objects.count(), 0)

    def test_final_event_decision_cannot_be_silently_replaced(self):
        review_performance_event(
            event_id=self.event.pk,
            reviewer=self.admin,
            decision=PerformanceEventReview.Decision.APPROVED,
            reason="Evidence reviewed and event confirmed.",
        )

        with self.assertRaises(ValidationError):
            review_performance_event(
                event_id=self.event.pk,
                reviewer=self.admin,
                decision=PerformanceEventReview.Decision.REJECTED,
                reason="Attempt to replace the original decision.",
            )

        self.assertEqual(PerformanceEventReview.objects.count(), 1)
