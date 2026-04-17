import time

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.core.tasks import run_worker_cycle


class Command(BaseCommand):
    help = "Runs the durable background task worker."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Process at most one task.")
        parser.add_argument(
            "--sleep",
            type=float,
            default=getattr(settings, "WORKER_POLL_INTERVAL_SECONDS", 5),
            help="Seconds to wait between polling cycles.",
        )
        parser.add_argument(
            "--worker-name",
            default="worker-1",
            help="Identifier recorded against claimed tasks.",
        )

    def handle(self, *args, **options):
        once = options["once"]
        sleep_seconds = options["sleep"]
        worker_name = options["worker_name"]

        while True:
            processed = run_worker_cycle(worker_name)
            if once:
                return

            if not processed:
                time.sleep(sleep_seconds)
