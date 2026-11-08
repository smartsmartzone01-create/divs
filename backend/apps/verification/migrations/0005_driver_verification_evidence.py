import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("verification", "0004_rename_event_check_field"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DriverVerificationEvidence",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("evidence_type", models.CharField(choices=[("national_identity", "National identity"), ("driving_licence", "Driving licence"), ("traffic_records", "Traffic/police records"), ("accident_records", "Accident records")], max_length=32)),
                ("source", models.CharField(choices=[("driver_upload", "Driver upload"), ("operations_upload", "Operations upload"), ("physical_inspection", "Physical inspection"), ("government_api", "Government API")], max_length=24)),
                ("status", models.CharField(choices=[("submitted", "Submitted"), ("under_review", "Under review"), ("accepted", "Accepted"), ("rejected", "Rejected"), ("expired", "Expired"), ("superseded", "Superseded")], default="submitted", max_length=16)),
                ("original_filename", models.CharField(blank=True, max_length=255)),
                ("content_type", models.CharField(blank=True, max_length=120)),
                ("file_size", models.PositiveBigIntegerField(blank=True, null=True)),
                ("sha256", models.CharField(blank=True, max_length=64)),
                ("storage_key", models.CharField(blank=True, max_length=512)),
                ("source_reference", models.CharField(blank=True, max_length=255)),
                ("submitted_at", models.DateTimeField(auto_now_add=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("review_notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviewed_driver_verification_evidence", to=settings.AUTH_USER_MODEL)),
                ("uploaded_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="uploaded_driver_verification_evidence", to=settings.AUTH_USER_MODEL)),
                ("verification_check", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="evidence", to="verification.driververificationcheck")),
            ],
            options={"ordering": ["-submitted_at"]},
        ),
        migrations.AddIndex(
            model_name="driververificationevidence",
            index=models.Index(fields=["verification_check", "status"], name="drv_evidence_check_status_idx"),
        ),
        migrations.AddIndex(
            model_name="driververificationevidence",
            index=models.Index(fields=["evidence_type", "source"], name="drv_evidence_type_source_idx"),
        ),
        migrations.CreateModel(
            name="DriverVerificationEvidenceEvent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("event_type", models.CharField(max_length=32)),
                ("previous_status", models.CharField(blank=True, max_length=16)),
                ("new_status", models.CharField(blank=True, max_length=16)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="driver_verification_evidence_events", to=settings.AUTH_USER_MODEL)),
                ("evidence", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="events", to="verification.driververificationevidence")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
