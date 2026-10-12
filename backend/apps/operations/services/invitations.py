import secrets
from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.operations.models import OperationsInvitation
from apps.notifications.services import notify_operations_reviewers


INVITATION_TTL_HOURS = 24


class InvitationDeliveryError(Exception):
    """Raised when the invitation email could not be delivered."""


@transaction.atomic
def issue_operations_invitation(*, inviter, email, role):
    normalized_email = email.strip().lower()
    raw_code = secrets.token_urlsafe(32)
    now = timezone.now()

    invitation = OperationsInvitation.objects.create(
        email=normalized_email,
        role=role,
        code_hash=make_password(raw_code),
        invited_by=inviter,
        expires_at=now + timedelta(hours=INVITATION_TTL_HOURS),
    )

    try:
        sent = send_mail(
            subject="Your DIVS operations invitation",
            message=(
                f"You have been invited to apply for the DIVS {invitation.get_role_display()} role.\n\n"
                f"Invitation code: {raw_code}\n\n"
                f"This code is tied to {normalized_email}, can be used once, and expires in "
                f"{INVITATION_TTL_HOURS} hours. Enter it on the DIVS operations invitation page. "
                "The invitation allows you to apply; it does not grant operations permissions. "
                "If you were not expecting this invitation, you can ignore this email."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[normalized_email],
            fail_silently=False,
        )
    except Exception as exc:
        invitation.delete()
        raise InvitationDeliveryError("Invitation email delivery is unavailable.") from exc

    if sent != 1:
        invitation.delete()
        raise InvitationDeliveryError("Invitation email delivery did not accept the message.")

    # Only replace prior invitations after the new email has been accepted for delivery.
    OperationsInvitation.objects.filter(
        email=normalized_email,
        used_at__isnull=True,
        revoked_at__isnull=True,
        expires_at__gt=now,
    ).exclude(pk=invitation.pk).update(revoked_at=now)

    transaction.on_commit(
        lambda: notify_operations_reviewers(
            event_type="operations.invitation.created",
            title="Operations invitation issued",
            message=f"An operations invitation for the {invitation.get_role_display()} role was issued.",
        ),
        robust=True,
    )
    return invitation
