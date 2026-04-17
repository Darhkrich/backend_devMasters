from django.core.management.base import BaseCommand
from apps.services.models import AppService
import json


class Command(BaseCommand):
    help = "Seed app services"

    def handle(self, *args, **kwargs):
        with open("services_data.json") as f:
            data = json.load(f)

        for item in data:
            AppService.objects.update_or_create(
                id=item["id"],
                defaults={
                    "title": item["title"],
                    "description": item["description"],
                    "type": item.get("type", []),
                    "icon": item.get("icon", ""),
                    "meta": item.get("meta", []),
                    "features": item.get("features", []),
                    "category": item.get("category", "service"),
                    "tag": item.get("tag"),
                },
            )

        self.stdout.write(self.style.SUCCESS("Services seeded successfully"))