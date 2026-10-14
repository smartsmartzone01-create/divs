from django.urls import path

from apps.performance.views.events import (
    PerformanceEventListCreateView,
    PerformanceEventReviewView,
)

app_name = "performance"

urlpatterns = [
    path("events/", PerformanceEventListCreateView.as_view(), name="event-list-create"),
    path("events/<uuid:event_id>/review/", PerformanceEventReviewView.as_view(), name="event-review"),
]
