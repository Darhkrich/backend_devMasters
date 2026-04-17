from django.db import models


class AppService(models.Model):
    CATEGORY_CHOICES = [
        ("service", "Service"),
        ("blueprint", "Blueprint"),
    ]

    id = models.CharField(primary_key=True, max_length=50)

    title = models.CharField(max_length=255)
    description = models.TextField()

    type = models.JSONField()  # ["web", "mobile"]
    icon = models.CharField(max_length=100)

    meta = models.JSONField(default=list)
    features = models.JSONField(default=list)

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)

    tag = models.CharField(max_length=50, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title