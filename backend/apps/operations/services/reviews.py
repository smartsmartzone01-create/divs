from django.db import transaction
from django.utils import timezone

from apps.identity.models import Account
from apps.operations.models import OperationsApplication, OperationsMembership


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
        if membership.role == OperationsMembership.Role.ADMIN:
            account = application.account
            account.is_staff = True
            account.is_superuser = True
            account.save(update_fields=["is_staff", "is_superuser", "updated_at"])

    return application
