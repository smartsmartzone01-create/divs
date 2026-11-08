import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("verification", "0002_verified_licence_classes"),
        ("profiles", "0002_driver_availability_activation"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="driververification",
            name="decision_reason",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="driververificationcheck",
            name="review_notes",
            field=models.TextField(blank=True),
        ),
        migrations.CreateModel(
            name="DriverVerificationEvent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("event_type", models.CharField(
                    choices=[
                        ("check_reviewed", "Check reviewed"),
                        ("approved", "Verification approved"),
                        ("rejected", "Verification rejected"),
                        ("availability_activated", "Availability activated"),
                    ], max_length=32,
                )),
                ("previous_status", models.CharField(blank=True, max_length=16)),
                ("new_status", models.CharField(blank=True, max_length=24)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name="driver_verification_events", to=settings.AUTH_USER_MODEL,
                )),
                ("check", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name="events", to="verification.driververificationcheck",
                )),
                ("verification", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="events", to="verification.driververification",
                )),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
