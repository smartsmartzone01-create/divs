import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("verification", "0007_evidence_retention_controls"),
    ]

    operations = [
        migrations.CreateModel(
            name="GovernmentVerificationAttempt",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        default=uuid.uuid4,
                        editable=False,
                        serialize=False,
                    ),
                ),
                (
                    "provider",
                    models.CharField(max_length=80),
                ),
                (
                    "provider_reference",
                    models.CharField(max_length=255),
                ),
                (
                    "outcome",
                    models.CharField(
                        choices=[
                            ("matched", "Matched / valid / clear"),
                            ("not_matched", "Mismatch / invalid / record found"),
                            ("inconclusive", "Inconclusive"),
                            ("unavailable", "Source unavailable"),
                            ("error", "Integration error"),
                        ],
                        max_length=16,
                    ),
                ),
                (
                    "result_code",
                    models.CharField(blank=True, max_length=24),
                ),
                (
                    "response_fingerprint",
                    models.CharField(blank=True, max_length=64),
                ),
                (
                    "completed_at",
                    models.DateTimeField(),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "verification_check",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="government_attempts",
                        to="verification.driververificationcheck",
                    ),
                ),
            ],
            options={
                "ordering": ["-completed_at"],
                "indexes": [
                    models.Index(
                        fields=["verification_check", "completed_at"],
                        name="gov_attempt_check_time_idx",
                    ),
                ],
            },
        ),
    ]
