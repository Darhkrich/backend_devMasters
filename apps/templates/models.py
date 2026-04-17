from email.policy import default
import uuid
from django.db import models


class Template(models.Model):
    TYPE_CHOICES = [
        ("ready", "Ready-Made"),
        ("custom", "Customizable"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=100)

    category = models.JSONField(default=list)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    preview_url = models.URLField(blank=True)
    image = models.FileField(upload_to="templates/", blank=True, null=True)

    description = models.TextField()

    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_note = models.CharField(max_length=255, blank=True)

    badge = models.CharField(max_length=50, blank=True)
    badge_class = models.CharField(max_length=100, blank=True)

    # ✅ ADD THESE (this fixes your error)
    tags = models.JSONField(default=list, blank=True)
    icons = models.JSONField(default=list, blank=True)
    template_file = models.FileField(upload_to="templates/files/", blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_draft = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
