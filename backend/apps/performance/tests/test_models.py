from django.test import SimpleTestCase

from apps.performance.models.events import PerformanceEvent
from apps.performance.models.history import ScoreHistory
from apps.performance.models.scores import DriverScore


class PerformanceModelDefinitionTests(SimpleTestCase):
    def test_event_categories_do_not_include_allegation_as_a_decision(self):
        self.assertEqual(
            {value for value, _label in PerformanceEvent.Category.choices},
            {"positive", "negative", "correction"},
        )
        self.assertIn(PerformanceEvent.Status.SUBMITTED, PerformanceEvent.Status.values)
        self.assertIn(PerformanceEvent.Status.APPROVED, PerformanceEvent.Status.values)

    def test_score_is_unset_until_baseline_eligibility_is_decided(self):
        field = DriverScore._meta.get_field("calculated_score")
        self.assertTrue(field.null)
        self.assertTrue(field.blank)

    def test_manual_override_does_not_replace_calculated_score(self):
        score = DriverScore(calculated_score=80, manual_override_score=55)
        self.assertEqual(score.calculated_score, 80)
        self.assertEqual(score.effective_score, 55)

    def test_calculated_score_is_effective_when_no_override_exists(self):
        score = DriverScore(calculated_score=80)
        self.assertEqual(score.effective_score, 80)

    def test_history_change_amount_is_signed_and_baseline_has_no_delta(self):
        deduction = ScoreHistory(previous_score=80, new_score=73)
        improvement = ScoreHistory(previous_score=73, new_score=78)
        baseline = ScoreHistory(previous_score=None, new_score=80)

        self.assertEqual(deduction.change_amount, -7)
        self.assertEqual(improvement.change_amount, 5)
        self.assertIsNone(baseline.change_amount)
