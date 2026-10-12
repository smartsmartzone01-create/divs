import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("operations", "0003_membership"),
        ("registrations", "0002_clientregistration"),
    ]

    operations = [
        migrations.CreateModel(
            name="ClientProfile",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("status", models.CharField(choices=[("active", "Active"), ("suspended", "Suspended"), ("closed", "Closed")], default="active", max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("registration", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="profile", to="registrations.clientregistration")),
            ],
            options={
                "verbose_name": "Client profile",
                "verbose_name_plural": "Client profiles",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="DriverProfile",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("status", models.CharField(choices=[("active", "Active"), ("suspended", "Suspended"), ("closed", "Closed")], default="active", max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("registration", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="profile", to="registrations.driverregistration")),
            ],
            options={
                "verbose_name": "Driver profile",
                "verbose_name_plural": "Driver profiles",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="OperationsProfile",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("status", models.CharField(choices=[("active", "Active"), ("suspended", "Suspended"), ("closed", "Closed")], default="active", max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("membership", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="profile", to="operations.operationsmembership")),
            ],
            options={
                "verbose_name": "Operations profile",
                "verbose_name_plural": "Operations profiles",
                "ordering": ["-created_at"],
            },
        ),
    ]
