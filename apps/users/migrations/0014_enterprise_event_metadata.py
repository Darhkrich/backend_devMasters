from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0013_enterprise_session_security"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="devicesession",
            options={"ordering": ["-last_used"]},
        ),
        migrations.AlterField(
            model_name="securityevent",
            name="event_type",
            field=models.CharField(
                choices=[
                    ("LOGIN_SUCCESS", "Login Success"),
                    ("LOGIN_FAILED", "Login Failed"),
                    ("PASSWORD_CHANGED", "Password Changed"),
                    ("PASSWORD_RESET_REQUESTED", "Password Reset Requested"),
                    ("PASSWORD_RESET_COMPLETED", "Password Reset Completed"),
                    ("PASSWORD_RESET_FAILED", "Password Reset Failed"),
                    ("EMAIL_CHANGED", "Email Changed"),
                    ("2FA_ENABLED", "2FA Enabled"),
                    ("2FA_DISABLED", "2FA Disabled"),
                    ("2FA_FAILED", "2FA Failed"),
                    ("SESSION_REVOKED", "Session Revoked"),
                    ("TOKEN_REFRESHED", "Token Refreshed"),
                    ("ACCOUNT_LOCKED", "Account Locked"),
                    ("ADMIN_ACCESS", "Admin Access"),
                    ("DATA_EXPORT", "Data Export"),
                    ("DATA_DELETION", "Data Deletion"),
                ],
                max_length=50,
            ),
        ),
    ]
