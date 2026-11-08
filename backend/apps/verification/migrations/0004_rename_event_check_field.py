from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("verification", "0003_verification_decisions_and_audit"),
    ]

    operations = [
        migrations.RenameField(
            model_name="driververificationevent",
            old_name="check",
            new_name="verification_check",
        ),
    ]
