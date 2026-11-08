from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("verification", "0005_driver_verification_evidence"),
    ]

    operations = [
        migrations.AddField(
            model_name="driververificationevidence",
            name="scan_status",
            field=models.CharField(
                choices=[
                    ("pending", "Quarantined / scan pending"),
                    ("clean", "Scan clean"),
                    ("infected", "Threat detected"),
                    ("error", "Scan failed"),
                ],
                default="pending",
                max_length=12,
            ),
        ),
        migrations.AddField(
            model_name="driververificationevidence",
            name="scan_provider",
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name="driververificationevidence",
            name="scanned_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
