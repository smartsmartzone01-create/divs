from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("operations", "0003_membership"),
    ]

    operations = [
        migrations.AlterField(
            model_name="operationsinvitation",
            name="expires_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
