from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.notifications.models import Notification
from apps.operations.models import OperationsApplication, OperationsMembership
from apps.profiles.models import ClientProfile, DriverProfile, OperationsProfile


ROLE_PROFILE_MODELS = {
    Notification.RecipientRole.DRIVER: (DriverProfile, "registration__account"),
    Notification.RecipientRole.CLIENT: (ClientProfile, "registration__account"),
    Notification.RecipientRole.OPERATIONS: (OperationsProfile, "membership__account"),
}


def create_notification(*, recipient, recipient_role, event_type, title, message):
    """Create a notification for one account and one workspace.

    Operations applicants may receive only their own application outcome before
    they have an active operations profile. The initial system superuser may
    receive operations alerts without an OperationsMembership.
    Never include government-source records or other sensitive payloads.
    """
    if recipient_role not in ROLE_PROFILE_MODELS:
        raise ValidationError({"recipient_role": "Unsupported notification workspace."})

    profile_model, account_lookup = ROLE_PROFILE_MODELS[recipient_role]
    has_active_profile = profile_model.objects.filter(
        **{account_lookup: recipient},
        status="active",
    ).exists()

    is_initial_system_superuser = (
        recipient_role == Notification.RecipientRole.OPERATIONS
        and recipient.is_superuser
        and not OperationsMembership.objects.filter(account=recipient).exists()
    )
    is_application_outcome = (
        recipient_role == Notification.RecipientRole.OPERATIONS
        and event_type in {
            "operations.application.submitted",
            "operations.application.approved",
            "operations.application.rejected",
        }
        and OperationsApplication.objects.filter(account=recipient).exists()
    )
    if not (has_active_profile or is_initial_system_superuser or is_application_outcome):
        raise ValidationError(
            {"recipient_role": "The recipient does not have access to this notification workspace."}
        )

    return Notification.objects.create(
        recipient=recipient,
        recipient_role=recipient_role,
        event_type=event_type,
        title=title,
        message=message,
    )


def notify_active_operations(*, event_type, title, message):
    """Notify each active operations account individually."""
    profiles = OperationsProfile.objects.filter(status="active").select_related("membership__account")
    return [
        create_notification(
            recipient=profile.membership.account,
            recipient_role=Notification.RecipientRole.OPERATIONS,
            event_type=event_type,
            title=title,
            message=message,
        )
        for profile in profiles
    ]


def notify_operations_reviewers(*, event_type, title, message):
    """Notify active operations members and the initial system superuser."""
    notifications = notify_active_operations(
        event_type=event_type,
        title=title,
        message=message,
    )
    from apps.identity.models import Account

    system_root = (
        Account.objects.filter(is_superuser=True, operations_membership__isnull=True)
        .order_by("date_joined")
        .first()
    )
    if system_root:
        notifications.append(
            create_notification(
                recipient=system_root,
                recipient_role=Notification.RecipientRole.OPERATIONS,
                event_type=event_type,
                title=title,
                message=message,
            )
        )
    return notifications


def mark_notification_read(*, notification, recipient):
    """Mark a notification read only when it belongs to the supplied account."""
    if notification.recipient_id != recipient.pk:
        raise Notification.DoesNotExist
    if notification.read_at is None:
        notification.read_at = timezone.now()
        notification.save(update_fields=["read_at"])
    return notification
