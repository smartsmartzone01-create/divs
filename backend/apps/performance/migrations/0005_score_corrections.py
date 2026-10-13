# Auditable corrections following successful performance appeals.
import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("performance", "0004_event_codes_for_scoring"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PerformanceScoreCorrection",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("previous_calculated_score", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("new_calculated_score", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("removed_points_delta", models.SmallIntegerField(blank=True, null=True)),
                ("reason", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="performance_score_corrections", to=settings.AUTH_USER_MODEL)),
                ("appeal", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="score_correction", to="performance.performanceappeal")),
                ("event", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="score_corrections", to="performance.performanceevent")),
                ("score", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="corrections", to="performance.driverscore")),
            ],
            options={
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["score", "created_at"], name="perf_correction_score_time_idx"),
                ],
                "constraints": [
                    models.CheckConstraint(condition=models.Q(("previous_calculated_score__isnull", True), ("previous_calculated_score__gte", 0), ("previous_calculated_score__lte", 100), _connector="OR"), name="perf_correction_previous_range"),
                    models.CheckConstraint(condition=models.Q(("new_calculated_score__isnull", True), ("new_calculated_score__gte", 0), ("new_calculated_score__lte", 100), _connector="OR"), name="perf_correction_new_range"),
                ],
            },
        ),
    ]
