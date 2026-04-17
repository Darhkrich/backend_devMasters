from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Inquiry(models.Model):
    STATUS_NEW = "new"
    STATUS_REVIEWED = "reviewed"
    STATUS_RESOLVED = "resolved"
    STATUS_CHOICES = [
        (STATUS_NEW, "New"),
        (STATUS_REVIEWED, "Reviewed"),
        (STATUS_RESOLVED, "Resolved"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inquiries",
    )
    client = models.ForeignKey(
        "clients.ClientProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inquiries",
    )

    name = models.CharField(max_length=200)
    email = models.EmailField()
    company = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=50, blank=True)

    subject = models.CharField(max_length=255, blank=True)
    service_category = models.CharField(max_length=100, blank=True)
    timeline = models.CharField(max_length=100, blank=True)
    budget = models.CharField(max_length=100, blank=True)
    message = models.TextField(blank=True)
    project_details = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)
    admin_reply = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Inquiries"

    def __str__(self):
        return f"Inquiry #{self.pk} - {self.name}"

    def save(self, *args, **kwargs):
        if self.project_details and not self.message:
            self.message = self.project_details
        if self.message and not self.project_details:
            self.project_details = self.message
        if not self.subject:
            if self.service_category:
                self.subject = f"{self.service_category.title()} inquiry"
            else:
                self.subject = f"Inquiry from {self.name}"
        super().save(*args, **kwargs)

    @property
    def estimated_total(self):
        total = Decimal("0.00")
        for item in self.items.all():
            if item.price is not None:
                total += item.price * item.quantity
        return total


class InquiryItem(models.Model):
    ITEM_TYPE_CHOICES = [
        ("service", "Service"),
        ("template", "Template"),
        ("package", "Package"),
        ("ai", "AI Automation"),
        ("bundle", "Bundle"),
        ("custom", "Custom"),
    ]
    PRICE_TYPE_CHOICES = [
        ("one_time", "One Time"),
        ("monthly", "Monthly"),
        ("custom", "Custom"),
    ]

    inquiry = models.ForeignKey(
        Inquiry,
        on_delete=models.CASCADE,
        related_name="items",
    )
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES, default="custom")
    item_id = models.CharField(max_length=100, blank=True)
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True)
    source = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_type = models.CharField(
        max_length=20,
        choices=PRICE_TYPE_CHOICES,
        default="one_time",
    )
    quantity = models.PositiveIntegerField(default=1)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.title} (Inquiry #{self.inquiry_id})"
