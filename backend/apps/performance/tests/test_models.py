from django.test import SimpleTestCase

from apps.performance.models.events import PerformanceEvent
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
