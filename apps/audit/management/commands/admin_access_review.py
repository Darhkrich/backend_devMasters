import json
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.audit.models import AuditLog


class Command(BaseCommand):
    help = "Generate a summary of recent privileged/admin access for access reviews."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=30)

    def handle(self, *args, **options):
        since = timezone.now() - timedelta(days=options["days"])
        prefixes = tuple(getattr(settings, "SENSITIVE_ADMIN_PATH_PREFIXES", []))
        queryset = AuditLog.objects.select_related("user").filter(timestamp__gte=since)
        queryset = queryset.filter(user__isnull=False)
        queryset = [
            log
            for log in queryset
            if log.user.is_staff or any(log.path.startswith(prefix) for prefix in prefixes)
        ]

        summary = {}
        for log in queryset:
            key = log.user.email
            summary.setdefault(
                key,
                {"count": 0, "paths": {}, "last_seen": None},
            )
            summary[key]["count"] += 1
            summary[key]["paths"][log.path] = summary[key]["paths"].get(log.path, 0) + 1
            summary[key]["last_seen"] = log.timestamp.isoformat()

        self.stdout.write(json.dumps(summary, indent=2, sort_keys=True))
