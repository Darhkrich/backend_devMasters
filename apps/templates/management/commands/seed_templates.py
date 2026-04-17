from django.core.management.base import BaseCommand
from apps.templates.models import Template
import json


class Command(BaseCommand):
    help = "Seed templates data"

    def handle(self, *args, **kwargs):
        with open("templates_data.json") as f:
            data = json.load(f)

        for item in data:
            Template.objects.update_or_create(
                id=item.get("id"),
                defaults={
                    "name": item.get("name"),
                    "short_name": item.get("shortName"),
                    "category": item.get("category", []),
                    "type": item.get("type", "ready"),
                    "preview_url": item.get("previewUrl"),
                    "image": item.get("image"),
                    "description": item.get("description", ""),
                    "price": item.get("price"),  # ✅ IMPORTANT
                    "price_note": item.get("priceNote", ""),
                    "tags": item.get("tags", []),
                    "icons": item.get("icons", []),
                    "badge": item.get("badge", ""),
                    "badge_class": item.get("badgeClass", ""),

                    # ✅ THIS FIXES YOUR EMPTY API
                    "is_active": True,
                    "is_draft": False,
                },
            )

        self.stdout.write(self.style.SUCCESS("Templates seeded successfully"))