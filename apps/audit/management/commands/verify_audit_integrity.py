from django.core.management.base import BaseCommand, CommandError

from apps.audit.models import AuditLog


class Command(BaseCommand):
    help = "Verify the tamper-evident audit log hash chain."

    def handle(self, *args, **options):
        previous_hash = ""
        checked = 0

        for log in AuditLog.objects.order_by("timestamp", "id"):
            expected_previous = previous_hash
            if log.previous_hash != expected_previous:
                raise CommandError(
                    f"Audit chain broken at log {log.id}: expected previous_hash "
                    f"{expected_previous!r}, got {log.previous_hash!r}"
                )

            calculated_hash = log._calculate_entry_hash()
            if log.entry_hash != calculated_hash:
                raise CommandError(
                    f"Audit hash mismatch at log {log.id}: stored {log.entry_hash!r}, "
                    f"calculated {calculated_hash!r}"
                )

            previous_hash = log.entry_hash
            checked += 1

        self.stdout.write(self.style.SUCCESS(f"Verified {checked} audit log entries."))
