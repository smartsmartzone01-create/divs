# Add operations applications, keeping them separate from driver registrations.
import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("operations", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="OperationsApplication",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("full_name", models.CharField(max_length=200)),
                ("status", models.CharField(
                    choices=[("pending", "Pending review"), ("approved", "Approved"), ("rejected", "Rejected")],
                    default="pending",
                    max_length=16,
                )),
                ("submitted_at", models.DateTimeField(auto_now_add=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("review_note", models.TextField(blank=True)),
                ("account", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="operations_applications",
                    to=settings.AUTH_USER_MODEL,
                )),
                ("invitation", models.OneToOneField(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="application",
                    to="operations.operationsinvitation",
                )),
                ("reviewed_by", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="reviewed_operations_applications",
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                "ordering": ["-submitted_at"],
                "indexes": [
                    models.Index(fields=["status", "submitted_at"], name="ops_app_status_submitted_idx"),
                ],
            },
        ),
    ]
