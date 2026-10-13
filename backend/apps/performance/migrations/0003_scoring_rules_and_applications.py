# Configurable scoring rules and one-time event score applications.
import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("performance", "0002_appeals_and_availability"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PerformanceScoringRule",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=160)),
                ("category", models.CharField(choices=[("positive", "Positive"), ("negative", "Negative")], max_length=16)),
                ("severity", models.CharField(blank=True, choices=[("", "Not specified"), ("minor", "Minor"), ("serious", "Serious"), ("critical", "Critical")], default="", max_length=16)),
                ("points_delta", models.SmallIntegerField()),
                ("status", models.CharField(choices=[("proposed", "Proposed"), ("approved", "Approved"), ("retired", "Retired")], default="proposed", max_length=12)),
                ("reason", models.TextField()),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("approved_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="approved_performance_scoring_rules", to=settings.AUTH_USER_MODEL)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_performance_scoring_rules", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["category", "severity", "-created_at"],
                "indexes": [
                    models.Index(fields=["category", "severity", "status"], name="perf_rule_lookup_idx"),
                ],
                "constraints": [
                    models.CheckConstraint(condition=models.Q(("points_delta__gte", -100), ("points_delta__lte", 100)), name="perf_rule_delta_range"),
                    models.UniqueConstraint(condition=models.Q(("status", "approved")), fields=("category", "severity"), name="perf_one_approved_rule_match"),
                ],
            },
        ),
        migrations.CreateModel(
            name="PerformanceEventScoreApplication",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("rule_name_snapshot", models.CharField(max_length=160)),
                ("points_delta", models.SmallIntegerField()),
                ("previous_score", models.PositiveSmallIntegerField()),
                ("new_score", models.PositiveSmallIntegerField()),
                ("reason", models.TextField()),
                ("applied_at", models.DateTimeField(auto_now_add=True)),
                ("event", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="score_application", to="performance.performanceevent")),
                ("rule", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="applications", to="performance.performancescoringrule")),
                ("score", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="event_applications", to="performance.driverscore")),
            ],
            options={
                "ordering": ["-applied_at"],
                "indexes": [
                    models.Index(fields=["score", "applied_at"], name="perf_application_score_time_idx"),
                ],
                "constraints": [
                    models.CheckConstraint(condition=models.Q(("previous_score__gte", 0), ("previous_score__lte", 100)), name="perf_application_previous_range"),
                    models.CheckConstraint(condition=models.Q(("new_score__gte", 0), ("new_score__lte", 100)), name="perf_application_new_range"),
                ],
            },
        ),
    ]
