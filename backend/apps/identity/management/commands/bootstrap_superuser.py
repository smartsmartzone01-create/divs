import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create the initial DIVS superuser from temporary environment variables."

    def handle(self, *args, **options):
        User = get_user_model()
        email = os.environ.get("DIVS_SUPERUSER_EMAIL", "").strip().lower()
        password = os.environ.get("DIVS_SUPERUSER_PASSWORD", "")

        if not email or not password:
            raise CommandError(
                "Set DIVS_SUPERUSER_EMAIL and DIVS_SUPERUSER_PASSWORD in the service environment."
            )

        existing = User.objects.filter(email=email).first()
        if existing:
            if existing.is_superuser and existing.is_staff:
                self.stdout.write(self.style.SUCCESS(
                    "The configured superuser already exists; no changes made."
                ))
                return
            raise CommandError(
                "An account with that email already exists but is not a superuser. "
                "No permissions were changed."
            )

        if User.objects.filter(is_superuser=True).exists():
            raise CommandError(
                "A different superuser already exists. No new account was created."
            )

        User.objects.create_superuser(email=email, password=password)
        self.stdout.write(self.style.SUCCESS(
            "Initial DIVS superuser created. Remove the temporary bootstrap environment "
            "variables and disable DIVS_BOOTSTRAP_SUPERUSER now."
        ))
