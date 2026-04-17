import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from ...models import service

class Command(BaseCommand):
    help = 'Export AppService objects to a JSON file matching frontend mockup structure'

    def handle(self, *args, **options):
        services = service.objects.all().order_by('category', 'title')

        output = {
            "APP_SERVICES": [],
            "APP_BLUEPRINTS": []
        }

        for s in services:
            data = {
                "id": s.id,
                "type": s.type,               # list of strings
                "icon": s.icon,
                "title": s.title,
                "description": s.description,
                "meta": s.meta,               # list of objects
                "features": s.features,       # list of strings
                "category": s.category,
            }
            if s.tag:
                data["tag"] = s.tag

            if s.category == "service":
                output["APP_SERVICES"].append(data)
            else:  # blueprint
                output["APP_BLUEPRINTS"].append(data)

        # Save to static folder (adjust path as needed)
        out_dir = os.path.join(settings.BASE_DIR, 'static', 'data')
        os.makedirs(out_dir, exist_ok=True)
        out_file = os.path.join(out_dir, 'services.json')

        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        self.stdout.write(self.style.SUCCESS(
            f'Exported {services.count()} services to {out_file}'
        ))