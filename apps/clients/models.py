from django.db import models


class ClientProfile(models.Model):
    PLAN_CHOICES = [
        ('starter', 'Starter'),
        ('pro', 'Professional'),
        ('enterprise', 'Enterprise'),
    ]

    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=50, blank=True)
    company = models.CharField(max_length=200, blank=True)

    # Subscription / plan
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='starter')
    credits = models.PositiveIntegerField(default=0)
    active_projects = models.PositiveIntegerField(default=0)
    next_billing = models.DateField(null=True, blank=True)

    # Meta
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.email})"
