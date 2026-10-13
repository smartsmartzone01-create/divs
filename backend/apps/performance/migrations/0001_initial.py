# Initial migration for the Performance & Scoring model foundation.
import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("profiles", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PerformanceEvent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("category", models.CharField(choices=[("positive", "Positive"), ("negative", "Negative"), ("correction", "Correction")], max_length=16)),
                ("severity", models.CharField(blank=True, choices=[("minor", "Minor"), ("serious", "Serious"), ("critical", "Critical")], max_length=16)),
                ("status", models.CharField(choices=[("submitted", "Submitted"), ("under_review", "Under review"), ("more_evidence", "More evidence requested"), ("approved", "Approved"), ("rejected", "Rejected")], default="submitted", max_length=20)),
                ("title", models.CharField(max_length=160)),
                ("description", models.TextField(blank=True)),
                ("occurred_at", models.DateTimeField(blank=True, null=True)),
                ("source_type", models.CharField(choices=[("operations", "Operations entry"), ("client", "Client submission"), ("trusted_integration", "Trusted integration"), ("other", "Other authorized source")], default="operations", max_length=24)),
                ("source_reference", models.CharField(blank=True, max_length=160)),
                ("idempotency_key", models.CharField(blank=True, max_length=160, null=True, unique=True)),
                ("evidence_references", models.JSONField(blank=True, default=list)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("decision_reason", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("driver", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="performance_events", to="profiles.driverprofile")),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="reviewed_performance_events", to=settings.AUTH_USER_MODEL)),
                ("submitted_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="submitted_performance_events", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["driver", "status"], name="performance_driver_status_idx"),
                    models.Index(fields=["category", "status"], name="performance_category_status_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="DriverScore",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("calculated_score", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("manual_override_score", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("manual_override_reason", models.TextField(blank=True)),
                ("manual_override_at", models.DateTimeField(blank=True, null=True)),
                ("calculation_updated_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("driver", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="performance_score", to="profiles.driverprofile")),
                ("manual_override_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="performance_score_overrides", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Driver performance score",
                "verbose_name_plural": "Driver performance scores",
                "constraints": [
                    models.CheckConstraint(condition=models.Q(("calculated_score__isnull", True)) | models.Q(("calculated_score__gte", 0), ("calculated_score__lte", 100)), name="performance_score_between_0_and_100"),
                    models.CheckConstraint(condition=models.Q(("manual_override_score__isnull", True)) | models.Q(("manual_override_score__gte", 0), ("manual_override_score__lte", 100)), name="performance_override_score_between_0_and_100"),
                ],
            },
        ),
        migrations.CreateModel(
            name="ScoreHistory",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("change_type", models.CharField(choices=[("baseline", "Baseline established"), ("event", "Approved performance event"), ("manual_override", "Admin manual override"), ("correction", "Correction"), ("recalculation", "Recalculation")], max_length=24)),
                ("previous_score", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("new_score", models.PositiveSmallIntegerField()),
                ("reason", models.TextField()),
                ("rule_reference", models.CharField(blank=True, max_length=120)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="performance_score_history_actions", to=settings.AUTH_USER_MODEL)),
                ("event", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="score_history_entries", to="performance.performanceevent")),
                ("score", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="history_entries", to="performance.driverscore")),
            ],
            options={
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["score", "created_at"], name="perf_score_history_time_idx"),
                    models.Index(fields=["event", "created_at"], name="perf_event_history_time_idx"),
                ],
                "constraints": [
                    models.CheckConstraint(condition=models.Q(("new_score__gte", 0), ("new_score__lte", 100)), name="perf_history_new_score_range"),
                    models.CheckConstraint(condition=models.Q(("previous_score__isnull", True)) | models.Q(("previous_score__gte", 0), ("previous_score__lte", 100)), name="perf_history_previous_score_range"),
                ],
            },
        ),
        migrations.CreateModel(
            name="PerformanceEventReview",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("decision", models.CharField(choices=[("approved", "Approved"), ("rejected", "Rejected"), ("more_evidence", "More evidence requested")], max_length=20)),
                ("reason", models.TextField()),
                ("requested_evidence", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("event", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="review_history", to="performance.performanceevent")),
                ("reviewer", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="performance_event_reviews", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["event", "created_at"], name="perf_review_event_time_idx"),
                ],
            },
        ),
    ]
