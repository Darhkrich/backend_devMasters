import uuid
from datetime import datetime, timezone as dt_timezone

from django.db import migrations, models
from django.utils.crypto import salted_hmac


def backfill_device_session_tokens(apps, schema_editor):
    DeviceSession = apps.get_model("users", "DeviceSession")

    for session in DeviceSession.objects.exclude(refresh_token=""):
        token = session.refresh_token or ""
        if not token:
            continue

        session.refresh_token_hash = salted_hmac(
            "device-session-refresh-token",
            token,
            algorithm="sha256",
        ).hexdigest()
        session.refresh_token_last4 = token[-4:]

        try:
            payload = token.split(".")
            if len(payload) == 3:
                import base64
                import json

                normalized = payload[1] + "=" * (-len(payload[1]) % 4)
                body = json.loads(base64.urlsafe_b64decode(normalized.encode()).decode())
                exp = body.get("exp")
                if exp:
                    session.expires_at = datetime.fromtimestamp(exp, tz=dt_timezone.utc)
        except Exception:
            session.expires_at = None

        session.refresh_token = ""
        session.save(
            update_fields=["refresh_token", "refresh_token_hash", "refresh_token_last4", "expires_at"]
        )


def noop(apps, schema_editor):
    return None


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0012_alter_devicesession_user"),
    ]

    operations = [
        migrations.AlterField(
            model_name="devicesession",
            name="user",
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE,
                related_name="device_sessions",
                to="users.user",
            ),
        ),
        migrations.AlterField(
            model_name="devicesession",
            name="refresh_token",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="devicesession",
            name="expires_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="devicesession",
            name="last_rotated_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="devicesession",
            name="refresh_token_hash",
            field=models.CharField(blank=True, db_index=True, max_length=64),
        ),
        migrations.AddField(
            model_name="devicesession",
            name="refresh_token_last4",
            field=models.CharField(blank=True, max_length=4),
        ),
        migrations.AddField(
            model_name="devicesession",
            name="revoked_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="devicesession",
            name="revoked_reason",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="devicesession",
            name="token_family",
            field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False),
        ),
        migrations.AddField(
            model_name="devicesession",
            name="trusted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="devicesession",
            name="trusted_until",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(backfill_device_session_tokens, noop),
    ]
