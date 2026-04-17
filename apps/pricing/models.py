from django.db import models

class Package(models.Model):
    CATEGORY_CHOICES = [
        ("websites", "Websites"),
        ("apps", "Apps"),
        ("ai", "AI"),
    ]

    SUBCATEGORY_CHOICES = [
        ("ready-made", "Ready Made"),
        ("custom", "Custom"),
        ("apps", "Apps"),
        ("ai", "AI"),
    ]

    id = models.CharField(primary_key=True, max_length=50)

    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    subcategory = models.CharField(max_length=50, choices=SUBCATEGORY_CHOICES)

    tier = models.CharField(max_length=50)

    title = models.CharField(max_length=255)
    subtitle = models.TextField(blank=True)

    billing_one_time = models.DecimalField(max_digits=10, decimal_places=2)
    billing_monthly = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    features = models.JSONField(default=list)

    popular = models.BooleanField(default=False)
    best_value = models.BooleanField(default=False)

    footnote = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class BuilderOption(models.Model):
    TYPE_CHOICES = [
        ("web", "Web"),
        ("app", "App"),
        ("ai", "AI"),
    ]

    OPTION_TYPE = [
        ("base", "Base"),
        ("extra", "Extra"),
    ]

    id = models.AutoField(primary_key=True)

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    option_type = models.CharField(max_length=10, choices=OPTION_TYPE)

    value = models.CharField(max_length=50)
    label = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.type} - {self.label}"


class BuilderPriority(models.Model):
    value = models.CharField(max_length=50)
    label = models.CharField(max_length=100)
    multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=1.00)

    def __str__(self):
        return self.label