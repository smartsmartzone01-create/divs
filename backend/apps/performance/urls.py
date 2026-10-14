from django.urls import path

from apps.performance.views import (
    DriverMyPerformanceView,
    PerformanceAppealListCreateView,
    PerformanceAppealReviewView,
    PerformanceEventListCreateView,
    PerformanceEventReviewView,
    ScoreCorrectionView,
    ScoreHistoryListView,
    ScoreOverrideView,
    ScoringRuleActionView,
    ScoringRuleListCreateView,
)

app_name = "performance"

urlpatterns = [
    path("events/", PerformanceEventListCreateView.as_view(), name="event-list-create"),
    path("events/<uuid:event_id>/review/", PerformanceEventReviewView.as_view(), name="event-review"),
    path("rules/", ScoringRuleListCreateView.as_view(), name="scoring-rule-list-create"),
    path("rules/<uuid:rule_id>/<str:action>/", ScoringRuleActionView.as_view(), name="scoring-rule-action"),
    path("driver/me/", DriverMyPerformanceView.as_view(), name="driver-my-performance"),
    path("driver/appeals/", PerformanceAppealListCreateView.as_view(), name="appeal-list"),
    path("driver/events/<uuid:event_id>/appeal/", PerformanceAppealListCreateView.as_view(), name="appeal-create"),
    path("appeals/<uuid:appeal_id>/review/", PerformanceAppealReviewView.as_view(), name="appeal-review"),
    path("appeals/<uuid:appeal_id>/correct-score/", ScoreCorrectionView.as_view(), name="appeal-score-correction"),
    path("scores/<uuid:score_id>/override/", ScoreOverrideView.as_view(), name="score-override"),
    path("scores/<uuid:score_id>/history/", ScoreHistoryListView.as_view(), name="score-history"),
]
