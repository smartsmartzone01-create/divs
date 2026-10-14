# Generated manually for validated driver licence classes.
import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("verification", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="VerifiedDriverLicenceClass",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("licence_class", models.CharField(max_length=12)),
                ("is_current", models.BooleanField(default=True)),
                ("verified_at", models.DateTimeField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("licence_check", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="verified_licence_classes", to="verification.driververificationcheck")),
                ("verified_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="verified_driver_licence_classes", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["licence_class"]},
        ),
        migrations.AddConstraint(
            model_name="verifieddriverlicenceclass",
            constraint=models.UniqueConstraint(fields=("licence_check", "licence_class"), name="uniq_verified_licence_class_per_check"),
        ),
        migrations.AddIndex(
            model_name="verifieddriverlicenceclass",
            index=models.Index(fields=["licence_class", "is_current"], name="verified_lic_class_current_idx"),
        ),
    ]
