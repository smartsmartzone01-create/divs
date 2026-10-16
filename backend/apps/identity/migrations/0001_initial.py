# Generated manually to match the identity models.
import uuid

import apps.identity.models.account
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="Account",
            fields=[
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("is_superuser", models.BooleanField(
                    default=False,
                    help_text="Designates that this user has all permissions without explicitly assigning them.",
                    verbose_name="superuser status",
                )),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("email", models.EmailField(blank=True, max_length=254, null=True, unique=True)),
                ("phone_number", models.CharField(blank=True, max_length=32, null=True, unique=True)),
                ("country_code", models.CharField(blank=True, max_length=2)),
                ("email_verified", models.BooleanField(default=False)),
                ("phone_verified", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                ("is_staff", models.BooleanField(default=False)),
                ("date_joined", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("groups", models.ManyToManyField(
                    blank=True,
                    help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                    related_name="user_set",
                    related_query_name="user",
                    to="auth.group",
                    verbose_name="groups",
                )),
                ("user_permissions", models.ManyToManyField(
                    blank=True,
                    help_text="Specific permissions for this user.",
                    related_name="user_set",
                    related_query_name="user",
                    to="auth.permission",
                    verbose_name="user permissions",
                )),
            ],
            options={
                "ordering": ["-date_joined"],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("email__isnull", False), ("phone_number__isnull", False), _connector="OR"),
                        name="account_requires_email_or_phone",
                    ),
                ],
            },
            managers=[
                ("objects", apps.identity.models.account.AccountManager()),
            ],
        ),
        migrations.CreateModel(
            name="AuthSession",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("device_label", models.CharField(blank=True, max_length=120)),
                ("user_agent", models.CharField(blank=True, max_length=512)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("last_seen_at", models.DateTimeField(auto_now=True)),
                ("expires_at", models.DateTimeField()),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("account", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="auth_sessions",
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                "ordering": ["-last_seen_at"],
            },
        ),
        migrations.CreateModel(
            name="ExternalIdentity",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("provider", models.CharField(choices=[("google", "Google")], max_length=32)),
                ("subject", models.CharField(max_length=255)),
                ("provider_email", models.EmailField(blank=True, max_length=254)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("account", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="external_identities",
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
        ),
        migrations.CreateModel(
            name="VerificationCode",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("channel", models.CharField(choices=[("email", "Email"), ("phone", "Phone")], max_length=10)),
                ("target", models.CharField(db_index=True, max_length=254)),
                ("code_hash", models.CharField(max_length=128)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
                ("attempts", models.PositiveSmallIntegerField(default=0)),
                ("consumed_at", models.DateTimeField(blank=True, null=True)),
                ("account", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="verification_codes",
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["channel", "target", "created_at"], name="id_vercode_chan_tgt_created_idx"),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="externalidentity",
            constraint=models.UniqueConstraint(
                fields=("provider", "subject"),
                name="unique_external_provider_subject",
            ),
        ),
    ]
