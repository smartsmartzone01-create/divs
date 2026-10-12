from django.db import migrations, models


def remove_expiry_from_active_invitations(apps, schema_editor):
    OperationsInvitation = apps.get_model("operations", "OperationsInvitation")
    OperationsInvitation.objects.filter(
        used_at__isnull=True,
        revoked_at__isnull=True,
    ).update(expires_at=None)


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
        migrations.RunPython(
            remove_expiry_from_active_invitations,
            migrations.RunPython.noop,
        ),
    ]
