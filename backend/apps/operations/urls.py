from django.urls import path

from apps.operations.views.invitations import OperationsInvitationCreateView

app_name = "operations"

urlpatterns = [
    path("invitations/", OperationsInvitationCreateView.as_view(), name="invitation-create"),
]
