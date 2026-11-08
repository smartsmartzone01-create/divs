from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("verification", "0009_government_api_event_type"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="governmentverificationattempt",
            constraint=models.UniqueConstraint(
                fields=("provider", "provider_reference"),
                name="uniq_gov_provider_ref",
            ),
        ),
    ]
