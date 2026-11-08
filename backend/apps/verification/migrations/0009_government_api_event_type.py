from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("verification", "0008_government_verification_attempts"),
    ]

    operations = [
        migrations.AlterField(
            model_name="driververificationevent",
            name="event_type",
            field=models.CharField(
                choices=[
                    ("check_reviewed", "Check reviewed"),
                    ("government_api_result", "Government API result recorded"),
                    ("approved", "Verification approved"),
                    ("rejected", "Verification rejected"),
                    ("availability_activated", "Availability activated"),
                ],
                max_length=32,
            ),
        ),
    ]
