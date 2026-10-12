# Add approved operations memberships.
import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("operations", "0002_application"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="OperationsMembership",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("role", models.CharField(choices=[("admin", "Admin"), ("operator", "Operator")], max_length=16)),
                ("approved_at", models.DateTimeField(auto_now_add=True)),
                ("account", models.OneToOneField(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="operations_membership",
                    to=settings.AUTH_USER_MODEL,
                )),
                ("approved_by", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="approved_operations_memberships",
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={"ordering": ["-approved_at"]},
        ),
    ]
