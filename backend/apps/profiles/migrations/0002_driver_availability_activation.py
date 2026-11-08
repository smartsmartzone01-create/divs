from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("profiles", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="driverprofile",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending_activation", "Pending activation"),
                    ("active", "Active"),
                    ("suspended", "Suspended"),
                    ("closed", "Closed"),
                ],
                default="pending_activation",
                max_length=24,
            ),
        ),
        migrations.AddField(
            model_name="driverprofile",
            name="availability_activated_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="driverprofile",
            name="availability_activated_by",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name="activated_driver_profiles", to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
