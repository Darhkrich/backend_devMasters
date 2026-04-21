from django.conf import settings
from django.core.checks import Error, Tags, Warning, register


@register(Tags.security)
def enterprise_security_checks(app_configs, **kwargs):
    findings = []

    if getattr(settings, "APP_ENV", "development") in {"staging", "production"}:
        if settings.DEBUG:
            findings.append(
                Error(
                    "DEBUG must be disabled in staging/production.",
                    id="core.E001",
                )
            )

    if not getattr(settings, "AUDIT_LOG_SIGNING_KEY", ""):
        findings.append(
            Warning(
                "AUDIT_LOG_SIGNING_KEY is not configured; audit integrity falls back to SECRET_KEY.",
                id="core.W001",
            )
        )

    if not getattr(settings, "CORS_ALLOWED_ORIGINS", []):
        findings.append(
            Warning(
                "CORS_ALLOWED_ORIGINS is empty; browser clients may fail or operators may loosen CORS unsafely later.",
                id="core.W002",
            )
        )

    if getattr(settings, "APP_ENV", "development") in {"staging", "production"}:
        channel_backend = (
            getattr(settings, "CHANNEL_LAYERS", {})
            .get("default", {})
            .get("BACKEND", "")
        )
        if "InMemoryChannelLayer" in channel_backend:
            findings.append(
                Error(
                    "In-memory channel layers are not allowed in staging/production.",
                    id="core.E002",
                )
            )
        elif not channel_backend:
            findings.append(
                Warning(
                    "REDIS_URL is not configured; real-time channel features are disabled in staging/production.",
                    id="core.W005",
                )
            )

        if getattr(settings, "TASK_QUEUE_MODE", "sync") in {"sync", "thread"}:
            findings.append(
                Warning(
                    "TASK_QUEUE_MODE should use the durable worker mode in staging/production.",
                    id="core.W003",
                )
            )

        if not getattr(settings, "METRICS_AUTH_TOKEN", ""):
            findings.append(
                Warning(
                    "METRICS_AUTH_TOKEN is not configured; metrics access should be protected in production.",
                    id="core.W004",
                )
            )

    return findings
