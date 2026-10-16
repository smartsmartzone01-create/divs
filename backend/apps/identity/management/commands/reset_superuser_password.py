import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Reset the password for an existing DIVS superuser using temporary environment variables."

    def handle(self, *args, **options):
        email = os.environ.get("DIVS_SUPERUSER_EMAIL", "").strip().lower()
        password = os.environ.get("DIVS_SUPERUSER_PASSWORD", "")

        if not email or not password:
            raise CommandError(
                "Set DIVS_SUPERUSER_EMAIL and DIVS_SUPERUSER_PASSWORD temporarily."
            )

        User = get_user_model()
        user = User.objects.filter(email=email).first()

        if user is None:
            raise CommandError("No account with the configured email exists. No changes made.")

        if not user.is_superuser or not user.is_staff:
            raise CommandError(
                "The matching account is not a superuser. No permissions were changed."
            )

        user.set_password(password)
        # The DIVS authentication backend requires a verified email even for admin login.
        # This command is restricted to an existing staff superuser, whose email is the
        # configured bootstrap/admin identity.
        user.email_verified = True
        user.save(update_fields=["password", "email_verified"])

        self.stdout.write(self.style.SUCCESS(
            "Superuser password reset successfully and email verified. Remove the temporary "
            "environment variables and disable DIVS_RESET_SUPERUSER_PASSWORD now."
        ))
