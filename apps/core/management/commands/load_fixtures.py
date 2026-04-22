from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import IntegrityError

class Command(BaseCommand):
    help = 'Load all fixtures safely (skip existing data)'

    def handle(self, *args, **options):
        fixtures = [
            'packages.json',
            'services_data.json',
            'templates_data.json',
            'builder_options.json',
            'builder_priorities.json',
            'automation.json',
            'bundles.json',
        ]
        for fixture in fixtures:
            try:
                call_command('loaddata', fixture)
                self.stdout.write(self.style.SUCCESS(f'Loaded {fixture}'))
            except IntegrityError:
                self.stdout.write(self.style.WARNING(f'{fixture} already loaded, skipping.'))