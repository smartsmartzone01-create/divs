from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("verification", "0006_evidence_scan_quarantine"),
    ]

    operations = [
        migrations.AddField(
            model_name="driververificationevidence",
            name="legal_hold",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="driververificationevidence",
            name="storage_deleted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
