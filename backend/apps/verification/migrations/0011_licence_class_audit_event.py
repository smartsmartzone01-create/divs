from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("verification", "0010_unique_government_provider_reference"),
    ]

    operations = [
        migrations.AlterField(
            model_name="driververificationevent",
            name="event_type",
            field=models.CharField(
                choices=[
                    ("check_reviewed", "Check reviewed"),
                    ("government_api_result", "Government API result recorded"),
                    ("licence_classes_recorded", "Verified licence classes recorded"),
                    ("approved", "Verification approved"),
                    ("rejected", "Verification rejected"),
                    ("availability_activated", "Availability activated"),
                ],
                max_length=32,
            ),
        ),
    ]
