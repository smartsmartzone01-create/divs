from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer
from apps.notifications.services import mark_notification_read
from common.views import RoleProtectedAPIView


class WorkspaceNotificationListView(RoleProtectedAPIView):
    """List notifications only for the signed-in account and required workspace."""

    required_profile_type = None
    recipient_role = None

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user,
            recipient_role=self.recipient_role,
        ).order_by("-created_at")

    def get(self, request):
        notifications = self.get_queryset()
        unread_count = notifications.filter(read_at__isnull=True).count()
        return Response({
            "unread_count": unread_count,
            "results": NotificationSerializer(notifications, many=True).data,
        })


class WorkspaceNotificationReadView(RoleProtectedAPIView):
    """Mark one notification read, scoped to account and workspace."""

    required_profile_type = None
    recipient_role = None

    def post(self, request, notification_id):
        notification = get_object_or_404(
            Notification.objects.filter(
                recipient=request.user,
                recipient_role=self.recipient_role,
            ),
            pk=notification_id,
        )
        mark_notification_read(notification=notification, recipient=request.user)
        return Response(NotificationSerializer(notification).data, status=status.HTTP_200_OK)


class DriverNotificationListView(WorkspaceNotificationListView):
    required_profile_type = "driver"
    recipient_role = Notification.RecipientRole.DRIVER


class ClientNotificationListView(WorkspaceNotificationListView):
    required_profile_type = "client"
    recipient_role = Notification.RecipientRole.CLIENT


class OperationsNotificationListView(WorkspaceNotificationListView):
    required_profile_type = "operations"
    recipient_role = Notification.RecipientRole.OPERATIONS


class DriverNotificationReadView(WorkspaceNotificationReadView):
    required_profile_type = "driver"
    recipient_role = Notification.RecipientRole.DRIVER


class ClientNotificationReadView(WorkspaceNotificationReadView):
    required_profile_type = "client"
    recipient_role = Notification.RecipientRole.CLIENT


class OperationsNotificationReadView(WorkspaceNotificationReadView):
    required_profile_type = "operations"
    recipient_role = Notification.RecipientRole.OPERATIONS
