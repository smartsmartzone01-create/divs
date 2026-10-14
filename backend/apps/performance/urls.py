from django.urls import path

from apps.performance.views.events import (
    PerformanceEventListCreateView,
    PerformanceEventReviewView,
)
from apps.performance.views.scoring import (
    ScoringRuleActionView,
    ScoringRuleListCreateView,
    ScoreHistoryListView,
    ScoreOverrideView,
    DriverMyPerformanceView,
)
from apps.performance.views.appeals import (
    AppealCorrectionView,
    AppealReviewView,
    DriverAppealsView,
)

app_name = "performance"

urlpatterns = [
    path("events/", PerformanceEventListCreateView.as_view(), name="event-list-create"),
    path("events/<uuid:event_id>/review/", PerformanceEventReviewView.as_view(), name="event-review"),
    path("rules/", ScoringRuleListCreateView.as_view(), name="scoring-rule-list-create"),
    path("rules/<uuid:rule_id>/<str:action>/", ScoringRuleActionView.as_view(), name="scoring-rule-action"),
    path("driver/me/", DriverMyPerformanceView.as_view(), name="driver-my-performance"),
    path("driver/appeals/", DriverAppealsView.as_view(), name="driver-appeals"),
    path("driver/events/<uuid:event_id>/appeal/", DriverAppealsView.as_view(), name="driver-appeal-create"),
    path("appeals/<uuid:appeal_id>/review/", AppealReviewView.as_view(), name="appeal-review"),
    path("appeals/<uuid:appeal_id>/correct-score/", AppealCorrectionView.as_view(), name="appeal-score-correction"),
    path("scores/<uuid:score_id>/override/", ScoreOverrideView.as_view(), name="score-override"),
    path("scores/<uuid:score_id>/history/", ScoreHistoryListView.as_view(), name="score-history"),
]
