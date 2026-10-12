from django.db import transaction
from django.utils import timezone

from apps.notifications.models import Notification
from apps.notifications.services import create_notification
from apps.operations.models import OperationsApplication, OperationsMembership
from apps.profiles.models import OperationsProfile


class ApplicationReviewError(Exception):
    """Raised when an application cannot be reviewed in its current state."""


@transaction.atomic
def review_operations_application(*, application_id, reviewer, decision, review_note=""):
    application = (
        OperationsApplication.objects.select_for_update()
        .select_related("account", "invitation")
        .filter(pk=application_id)
        .first()
    )
    if application is None or application.status != OperationsApplication.Status.PENDING:
        raise ApplicationReviewError

    if application.account_id == reviewer.pk:
        raise ApplicationReviewError

    if (
        decision == OperationsApplication.Status.APPROVED
        and OperationsMembership.objects.filter(account=application.account).exists()
    ):
        raise ApplicationReviewError

    now = timezone.now()
    application.status = decision
    application.reviewed_by = reviewer
    application.reviewed_at = now
    application.review_note = review_note.strip()
    application.save(update_fields=["status", "reviewed_by", "reviewed_at", "review_note"])

    if decision == OperationsApplication.Status.APPROVED:
        membership = OperationsMembership.objects.create(
            account=application.account,
            role=application.invitation.role,
            approved_by=reviewer,
        )
        OperationsProfile.objects.create(membership=membership)
        if membership.role == OperationsMembership.Role.ADMIN:
            account = application.account
            account.is_staff = True
            account.is_superuser = True
            account.save(update_fields=["is_staff", "is_superuser", "updated_at"])

    is_approved = decision == OperationsApplication.Status.APPROVED
    create_notification(
        recipient=application.account,
        recipient_role=Notification.RecipientRole.OPERATIONS,
        event_type=(
            "operations.application.approved"
            if is_approved
            else "operations.application.rejected"
        ),
        title=(
            "Operations application approved"
            if is_approved
            else "Operations application not approved"
        ),
        message=(
            "Your operations application was approved. Your assigned workspace access is active."
            if is_approved
            else "Your operations application was rejected. You do not have operations workspace access."
        ),
    )

    return application
