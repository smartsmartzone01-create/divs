# Generated manually for the initial client registration schema.
import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("registrations", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ClientRegistration",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("client_type", models.CharField(choices=[("individual", "Individual"), ("company", "Company")], max_length=16)),
                ("name", models.CharField(max_length=200)),
                ("primary_contact", models.CharField(max_length=40)),
                ("email", models.EmailField(max_length=254)),
                ("country", models.CharField(max_length=100)),
                ("region", models.CharField(max_length=120)),
                ("alternative_contacts", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("account", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="client_registration", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Client registration",
                "verbose_name_plural": "Client registrations",
                "ordering": ["-created_at"],
            },
        ),
    ]
