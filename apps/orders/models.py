from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class Order(models.Model):
    STATUS_PENDING = "pending"
    STATUS_REVIEWED = "reviewed"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_AWAITING_CLIENT = "awaiting_client"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_REVIEWED, "Reviewed"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_AWAITING_CLIENT, "Awaiting Client"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    client = models.ForeignKey(
        "clients.ClientProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    inquiry = models.OneToOneField(
        "inquiries.Inquiry",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order",
    )

    reference = models.CharField(max_length=32, unique=True, blank=True)

    client_name = models.CharField(max_length=200)
    client_email = models.EmailField()
    client_company = models.CharField(max_length=200, blank=True)

    project_details = models.TextField(blank=True)
    timeline = models.CharField(max_length=100, blank=True)
    budget_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    budget_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, default="USD")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    notes = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.reference} - {self.client_name} ({self.status})"

    @classmethod
    def generate_reference(cls):
        prefix = f"DevMasters-{timezone.localdate():%Y%m%d}"
        latest_reference = (
            cls.objects.filter(reference__startswith=prefix)
            .order_by("-reference")
            .values_list("reference", flat=True)
            .first()
        )

        sequence = 1
        if latest_reference:
            try:
                sequence = int(latest_reference.rsplit("-", 1)[-1]) + 1
            except (TypeError, ValueError):
                sequence = cls.objects.filter(reference__startswith=prefix).count() + 1

        return f"{prefix}-{sequence:03d}"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self.generate_reference()
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    ITEM_TYPE_CHOICES = [
        ("service", "Service"),
        ("template", "Template"),
        ("package", "Package"),
        ("ai", "AI Automation"),
        ("bundle", "Bundle"),
        ("custom", "Custom"),
    ]

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES, default="custom")
    item_id = models.CharField(max_length=100, blank=True)
    title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.title} (Order #{self.order.reference})"


class OrderActivity(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="activities",
    )
    message = models.CharField(max_length=255)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.message} ({self.order.reference})"


class OrderFile(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    file = models.FileField(upload_to="orders/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
