from django.urls import path

from apps.operations.views.applications import OperationsApplicationCreateView
from apps.operations.views.invitations import (
    OperationsInvitationCreateView,
    OperationsInvitationValidateView,
)
from apps.operations.views.reviews import (
    OperationsApplicationPendingListView,
    OperationsApplicationReviewView,
)

app_name = "operations"

urlpatterns = [
    path("invitations/", OperationsInvitationCreateView.as_view(), name="invitation-create"),
    path("invitations/validate/", OperationsInvitationValidateView.as_view(), name="invitation-validate"),
    path("applications/", OperationsApplicationCreateView.as_view(), name="application-create"),
    path("applications/pending/", OperationsApplicationPendingListView.as_view(), name="application-pending"),
    path("applications/<uuid:application_id>/review/", OperationsApplicationReviewView.as_view(), name="application-review"),
]
