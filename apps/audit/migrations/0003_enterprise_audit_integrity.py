from datetime import timedelta
import json

from django.conf import settings
from django.db import migrations, models
from django.utils import timezone
from django.utils.crypto import salted_hmac


def backfill_audit_hashes(apps, schema_editor):
    AuditLog = apps.get_model("audit", "AuditLog")
    previous_hash = ""
    retention_days = getattr(settings, "AUDIT_LOG_RETENTION_DAYS", 365)
    secret = getattr(settings, "AUDIT_LOG_SIGNING_KEY", None) or settings.SECRET_KEY

    for log in AuditLog.objects.order_by("timestamp", "id"):
        timestamp = log.timestamp or timezone.now()
        payload = {
            "user_id": log.user_id,
            "action": log.action,
            "model_name": log.model_name,
            "object_id": log.object_id,
            "ip_address": log.ip_address,
            "method": log.method,
            "path": log.path,
            "status_code": log.status_code,
            "response_time": log.response_time,
            "timestamp": timestamp.isoformat(),
            "previous_hash": previous_hash,
        }
        entry_hash = salted_hmac(
            "audit-log-chain",
            json.dumps(payload, sort_keys=True, default=str),
            secret=secret,
            algorithm="sha256",
        ).hexdigest()
        log.previous_hash = previous_hash
        log.entry_hash = entry_hash
        log.retention_until = timestamp + timedelta(days=retention_days)
        log.save(update_fields=["previous_hash", "entry_hash", "retention_until"])
        previous_hash = entry_hash


def noop(apps, schema_editor):
    return None


class Migration(migrations.Migration):
    dependencies = [
        ("audit", "0002_alter_auditlog_action_alter_auditlog_ip_address_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="auditlog",
            name="entry_hash",
            field=models.CharField(default="", db_index=True, editable=False, max_length=64),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="auditlog",
            name="previous_hash",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="auditlog",
            name="retention_until",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.RunPython(backfill_audit_hashes, noop),
    ]
