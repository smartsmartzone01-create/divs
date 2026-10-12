from django.urls import path

from apps.operations.views.applications import OperationsApplicationCreateView
from apps.operations.views.invitations import (
    OperationsInvitationCreateView,
    OperationsInvitationValidateView,
)

app_name = "operations"

urlpatterns = [
    path("invitations/", OperationsInvitationCreateView.as_view(), name="invitation-create"),
    path("invitations/validate/", OperationsInvitationValidateView.as_view(), name="invitation-validate"),
    path("applications/", OperationsApplicationCreateView.as_view(), name="application-create"),
]
