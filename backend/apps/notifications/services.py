from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.notifications.models import Notification
from apps.profiles.models import ClientProfile, DriverProfile, OperationsProfile


ROLE_PROFILE_MODELS = {
    Notification.RecipientRole.DRIVER: (DriverProfile, "registration__account"),
    Notification.RecipientRole.CLIENT: (ClientProfile, "registration__account"),
    Notification.RecipientRole.OPERATIONS: (OperationsProfile, "membership__account"),
}


def create_notification(*, recipient, recipient_role, event_type, title, message):
    """Create an in-app notification only for an account with that active role.

    Notifications are targeted to an account UUID and a single workspace role.
    Do not put government-source records, identity numbers, credentials, or other
    sensitive payloads into notification titles/messages.
    """
    if recipient_role not in ROLE_PROFILE_MODELS:
        raise ValidationError({"recipient_role": "Unsupported notification workspace."})

    profile_model, account_lookup = ROLE_PROFILE_MODELS[recipient_role]
    if not profile_model.objects.filter(
        **{account_lookup: recipient},
        status="active",
    ).exists():
        raise ValidationError(
            {"recipient_role": "The recipient does not have an active profile for this workspace."}
        )

    return Notification.objects.create(
        recipient=recipient,
        recipient_role=recipient_role,
        event_type=event_type,
        title=title,
        message=message,
    )


def mark_notification_read(*, notification, recipient):
    """Mark a notification read only when it belongs to the supplied account."""
    if notification.recipient_id != recipient.pk:
        raise Notification.DoesNotExist
    if notification.read_at is None:
        notification.read_at = timezone.now()
        notification.save(update_fields=["read_at"])
    return notification
