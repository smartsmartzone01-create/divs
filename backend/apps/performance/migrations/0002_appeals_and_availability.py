# Appeals and availability restriction workflows.
import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("performance", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PerformanceAppeal",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("reason", models.TextField()),
                ("evidence_references", models.JSONField(blank=True, default=list)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("upheld", "Appeal successful"), ("denied", "Appeal unsuccessful"), ("withdrawn", "Withdrawn")], default="pending", max_length=16)),
                ("decided_at", models.DateTimeField(blank=True, null=True)),
                ("decision_reason", models.TextField(blank=True)),
                ("correction_required", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("appellant", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="performance_appeals", to=settings.AUTH_USER_MODEL)),
                ("decided_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="decided_performance_appeals", to=settings.AUTH_USER_MODEL)),
                ("event", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="appeals", to="performance.performanceevent")),
            ],
            options={
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["status", "created_at"], name="perf_appeal_status_time_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(condition=models.Q(("status", "pending")), fields=("event",), name="perf_one_pending_appeal_event"),
                ],
            },
        ),
        migrations.CreateModel(
            name="PerformanceAppealDecision",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("upheld", "Appeal successful"), ("denied", "Appeal unsuccessful"), ("withdrawn", "Withdrawn")], max_length=16)),
                ("reason", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("appeal", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="decision_history", to="performance.performanceappeal")),
                ("reviewer", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="performance_appeal_decisions", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["appeal", "created_at"], name="perf_appeal_decision_time_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="AvailabilityRestriction",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("kind", models.CharField(choices=[("critical_incident", "Critical incident review"), ("low_score", "Low performance score")], max_length=24)),
                ("status", models.CharField(choices=[("active", "Active"), ("released", "Released")], default="active", max_length=12)),
                ("reason", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("released_at", models.DateTimeField(blank=True, null=True)),
                ("release_reason", models.TextField(blank=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="created_availability_restrictions", to=settings.AUTH_USER_MODEL)),
                ("driver", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="availability_restrictions", to="profiles.driverprofile")),
                ("released_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="released_availability_restrictions", to=settings.AUTH_USER_MODEL)),
                ("source_event", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="availability_restrictions", to="performance.performanceevent")),
                ("source_score", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="availability_restrictions", to="performance.driverscore")),
            ],
            options={
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["driver", "status"], name="perf_restrict_driver_status_idx"),
                    models.Index(fields=["kind", "status"], name="perf_restrict_kind_status_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(condition=models.Q(("source_event__isnull", False), ("status", "active")), fields=("source_event", "kind"), name="perf_one_active_event_restriction"),
                    models.UniqueConstraint(condition=models.Q(("source_score__isnull", False), ("status", "active")), fields=("source_score", "kind"), name="perf_one_active_score_restriction"),
                ],
            },
        ),
        migrations.CreateModel(
            name="AvailabilityRestrictionDecision",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("action", models.CharField(choices=[("placed", "Restriction placed"), ("released", "Restriction released")], max_length=12)),
                ("reason", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="availability_restriction_decisions", to=settings.AUTH_USER_MODEL)),
                ("restriction", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="decision_history", to="performance.availabilityrestriction")),
            ],
            options={
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["restriction", "created_at"], name="perf_restrict_decision_time_idx"),
                ],
            },
        ),
    ]
