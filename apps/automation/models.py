from django.db import models

class Automation(models.Model):
    id = models.CharField(primary_key=True, max_length=50)

    title = models.CharField(max_length=255)
    description = models.TextField()

    sector = models.CharField(max_length=100)
    icon = models.CharField(max_length=100)

    features = models.JSONField(default=list)
    integration = models.JSONField(default=list)
    use_cases = models.JSONField(default=list)
    benefits = models.JSONField(default=list)

    price_note = models.CharField(max_length=255)
    delivery_time = models.CharField(max_length=100)

    preview_url = models.URLField(blank=True)
    image = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Bundle(models.Model):
    id = models.CharField(primary_key=True, max_length=50)

    title = models.CharField(max_length=255)
    description = models.TextField()

    tag = models.CharField(max_length=50)

    items = models.JSONField(default=list)
    features = models.JSONField(default=list)
    ideal_for = models.JSONField(default=list)

    price_note = models.CharField(max_length=255)
    delivery_time = models.CharField(max_length=100)

    preview_url = models.URLField(blank=True)
    image = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title