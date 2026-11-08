from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("verification", "0013_verification_reopened_event"),
    ]

    operations = [
        migrations.AlterField(
            model_name="driververificationevent",
            name="event_type",
            field=models.CharField(
                choices=[
                    ("check_reviewed", "Check reviewed"),
                    ("check_reopened", "Verification check reopened"),
                    ("check_invalidated", "Verification check invalidated"),
                    ("verification_reopened", "Verification reopened"),
                    ("availability_deactivated", "Driver availability deactivated"),
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
