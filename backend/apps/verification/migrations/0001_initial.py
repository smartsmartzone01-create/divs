import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def create_initial_driver_verifications(apps, schema_editor):
    DriverProfile = apps.get_model("profiles", "DriverProfile")
    DriverVerification = apps.get_model("verification", "DriverVerification")
    DriverVerificationCheck = apps.get_model("verification", "DriverVerificationCheck")
    check_types = [
        "national_identity",
        "driving_licence",
        "traffic_records",
        "accident_records",
    ]
    for profile in DriverProfile.objects.all().iterator():
        verification, _ = DriverVerification.objects.get_or_create(
            profile_id=profile.pk,
            defaults={"status": "pending"},
        )
        for check_type in check_types:
            DriverVerificationCheck.objects.get_or_create(
                verification_id=verification.pk,
                check_type=check_type,
                defaults={"status": "pending"},
            )


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("profiles", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DriverVerification",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("in_review", "In review"), ("approved", "Approved"), ("rejected", "Rejected")], default="pending", max_length=16)),
                ("decided_at", models.DateTimeField(blank=True, null=True)),
                ("decision_note", models.CharField(blank=True, max_length=500)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("decided_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="driver_verification_decisions", to=settings.AUTH_USER_MODEL)),
                ("profile", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="verification", to="profiles.driverprofile")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="DriverVerificationCheck",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("check_type", models.CharField(choices=[("national_identity", "National identity"), ("driving_licence", "Driving licence"), ("traffic_records", "Traffic/police records"), ("accident_records", "Accident records")], max_length=32)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("in_review", "In review"), ("passed", "Passed"), ("failed", "Failed"), ("needs_review", "Needs review"), ("unavailable", "Source unavailable")], default="pending", max_length=16)),
                ("method", models.CharField(blank=True, choices=[("government_api", "Government API"), ("manual", "Manual review")], max_length=20)),
                ("result_code", models.CharField(blank=True, choices=[("match", "Information matched"), ("mismatch", "Information mismatch"), ("valid", "Valid"), ("invalid", "Invalid"), ("clear", "No disqualifying record reported"), ("record_found", "Record requires review"), ("inconclusive", "Inconclusive")], max_length=24)),
                ("checked_at", models.DateTimeField(blank=True, null=True)),
                ("review_note", models.CharField(blank=True, max_length=500)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviewed_driver_verification_checks", to=settings.AUTH_USER_MODEL)),
                ("verification", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="checks", to="verification.driververification")),
            ],
            options={"ordering": ["check_type"]},
        ),
        migrations.AddConstraint(
            model_name="driververificationcheck",
            constraint=models.UniqueConstraint(fields=("verification", "check_type"), name="uniq_driver_verification_check"),
        ),
        migrations.AddIndex(
            model_name="driververificationcheck",
            index=models.Index(fields=["status", "check_type"], name="drv_vcheck_status_type_idx"),
        ),
        migrations.RunPython(create_initial_driver_verifications, migrations.RunPython.noop),
    ]
