from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("identity", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="verificationcode",
            name="purpose",
            field=models.CharField(
                choices=[
                    ("identity_verification", "Identity verification"),
                    ("password_reset", "Password reset"),
                ],
                default="identity_verification",
                max_length=32,
            ),
        ),
        migrations.AddIndex(
            model_name="verificationcode",
            index=models.Index(
                fields=["channel", "purpose", "target", "created_at"],
                name="id_vercode_purpose_idx",
            ),
        ),
    ]
