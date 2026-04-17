from django.conf import settings
from django.db import models
import os

class ProjectFile(models.Model):
    REVIEW_STATUS_CHOICES = [
        ("pending_review", "Pending Review"),
        ("in_review", "In Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("changes_requested", "Changes Requested"),
    ]

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="files",
        db_index=True,
    )
    inquiry = models.ForeignKey(
        "inquiries.Inquiry",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="files",
        db_index=True,
    )
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_files",
        verbose_name="Uploader",
    )
    uploader_role = models.CharField(
        max_length=10,
        choices=[("client", "Client"), ("admin", "Admin")],
        default="client",
    )
    file_name = models.CharField(max_length=255)
    file = models.FileField(upload_to="project_files/%Y/%m/", blank=True, null=True)
    file_url = models.URLField(blank=True)
    file_type = models.CharField(max_length=100, blank=True)
    size_bytes = models.PositiveBigIntegerField(default=0)
    description = models.CharField(max_length=500, blank=True)
    review_status = models.CharField(
        max_length=20,
        choices=REVIEW_STATUS_CHOICES,
        default="pending_review",
        db_index=True,
    )
    review_notes = models.CharField(max_length=500, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_project_files",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __init__(self, *args, **kwargs):
        uploaded_by = kwargs.pop("uploaded_by", "")
        super().__init__(*args, **kwargs)
        self.uploaded_by = uploaded_by

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        target = self.order_id or self.inquiry_id or "unlinked"
        return f"{self.file_name} ({target})"

    def save(self, *args, **kwargs):
        # Auto-fill file_name if not provided
        if not self.file_name and self.file:
            self.file_name = os.path.basename(self.file.name)
        # Auto-set file_type from file extension
        if not self.file_type and self.file:
            ext = os.path.splitext(self.file_name)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                self.file_type = 'image'
            elif ext in ['.pdf']:
                self.file_type = 'pdf'
            elif ext in ['.doc', '.docx']:
                self.file_type = 'document'
            elif ext in ['.zip', '.rar', '.7z']:
                self.file_type = 'archive'
            else:
                self.file_type = 'other'
        # Auto-set size_bytes
        if self.file and not self.size_bytes:
            try:
                self.size_bytes = self.file.size
            except (OSError, ValueError):
                pass
        super().save(*args, **kwargs)

    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.file and not self.file_url:
            raise ValidationError("Either a file or a file URL must be provided.")
