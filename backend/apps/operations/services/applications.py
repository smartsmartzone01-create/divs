from django.contrib.auth.hashers import check_password
from django.db import transaction
from django.utils import timezone

from apps.operations.models import OperationsApplication, OperationsInvitation


class InvalidOperationsInvitation(Exception):
    """The invitation is invalid, expired, revoked, or already used."""


@transaction.atomic
def submit_operations_application(*, account, invitation_id, code, full_name):
    email = (account.email or "").strip().lower()
    if not email:
        raise InvalidOperationsInvitation

    invitation = (
        OperationsInvitation.objects.select_for_update()
        .filter(
            pk=invitation_id,
            email=email,
            used_at__isnull=True,
            revoked_at__isnull=True,
            expires_at__gt=timezone.now(),
        )
        .first()
    )
    if invitation is None or not check_password(code, invitation.code_hash):
        raise InvalidOperationsInvitation

    application = OperationsApplication.objects.create(
        invitation=invitation,
        account=account,
        full_name=full_name.strip(),
    )
    invitation.used_at = timezone.now()
    invitation.save(update_fields=["used_at"])

    # The one-time code was sent to this exact address, so successful submission
    # also establishes control of the account's email address.
    if not account.email_verified:
        account.email_verified = True
        account.save(update_fields=["email_verified", "updated_at"])

    return application
