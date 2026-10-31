import os

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create one ordinary, email-verified DIVS test account from environment variables."

    def handle(self, *args, **options):
        User = get_user_model()
        email = os.environ.get("DIVS_TEST_USER_EMAIL", "").strip().lower()
        password = os.environ.get("DIVS_TEST_USER_PASSWORD", "")

        if not email or not password:
            raise CommandError(
                "Set DIVS_TEST_USER_EMAIL and DIVS_TEST_USER_PASSWORD in the service environment."
            )

        existing = User.objects.filter(email__iexact=email).first()
        if existing:
            raise CommandError(
                "An account with this email already exists. No account or permissions were changed."
            )

        try:
            validate_password(password)
        except ValidationError as exc:
            raise CommandError("; ".join(exc.messages)) from exc

        account = User.objects.create_user(email=email, password=password)
        account.email_verified = True
        account.save(update_fields=["email_verified", "updated_at"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Ordinary verified test account created: {account.email}. "
                "No driver/client profile or operations permissions were created."
            )
        )
