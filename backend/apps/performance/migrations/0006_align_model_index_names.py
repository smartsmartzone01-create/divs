from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("performance", "0005_score_corrections"),
    ]

    operations = [
        migrations.RenameIndex(
            model_name="availabilityrestriction",
            old_name="perf_restrict_driver_status_idx",
            new_name="perf_rest_driver_stat_idx",
        ),
        migrations.RenameIndex(
            model_name="performanceeventscoreapplication",
            old_name="perf_application_score_time_idx",
            new_name="perf_app_score_time_idx",
        ),
    ]
