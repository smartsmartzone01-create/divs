# Generated manually for the initial role-registration schema.
import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DriverRegistration",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("first_name", models.CharField(max_length=100)),
                ("middle_name", models.CharField(blank=True, max_length=100)),
                ("last_name", models.CharField(max_length=100)),
                ("nationality", models.CharField(max_length=100)),
                ("region", models.CharField(max_length=120)),
                ("district", models.CharField(max_length=120)),
                ("current_residential_address", models.TextField()),
                ("driving_experience", models.CharField(choices=[("none", "No professional driving experience"), ("under_1_year", "Less than 1 year"), ("1_to_3_years", "1–3 years"), ("4_to_7_years", "4–7 years"), ("8_plus_years", "8 or more years")], max_length=24)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("account", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="driver_registration", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Driver registration",
                "verbose_name_plural": "Driver registrations",
                "ordering": ["-created_at"],
            },
        ),
    ]
