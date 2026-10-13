# Match rules to a specific event type, not only category and severity.
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("performance", "0003_scoring_rules_and_applications"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="performancescoringrule",
            name="perf_one_approved_rule_match",
        ),
        migrations.AddField(
            model_name="performanceevent",
            name="event_code",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AddField(
            model_name="performancescoringrule",
            name="event_code",
            field=models.CharField(default="", max_length=64),
            preserve_default=False,
        ),
        migrations.RemoveIndex(
            model_name="performancescoringrule",
            name="perf_rule_lookup_idx",
        ),
        migrations.AddIndex(
            model_name="performancescoringrule",
            index=models.Index(
                fields=["category", "event_code", "severity", "status"],
                name="perf_rule_lookup_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="performancescoringrule",
            constraint=models.UniqueConstraint(
                condition=models.Q(("status", "approved")),
                fields=("category", "event_code", "severity"),
                name="perf_one_approved_rule_match",
            ),
        ),
    ]
