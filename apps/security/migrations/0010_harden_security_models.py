from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("security", "0009_rename_expires_at_blockedip_blocked_until_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="blockedip",
            name="attempts",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="blockedip",
            name="block_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="blockedip",
            name="reason",
            field=models.CharField(default="Suspicious activity detected", max_length=255),
        ),
        migrations.AddField(
            model_name="securityalert",
            name="ip_address",
            field=models.GenericIPAddressField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="suspiciousip",
            name="block_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="suspiciousip",
            name="last_success",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="suspiciousip",
            name="risk_score",
            field=models.FloatField(default=0),
        ),
    ]
