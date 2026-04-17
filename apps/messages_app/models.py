from django.db import models

class MessageThread(models.Model):
    client = models.ForeignKey(
        "clients.ClientProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="threads",
    )
    inquiry = models.ForeignKey(
        "inquiries.Inquiry",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="threads",
    )
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="threads",
    )
    subject = models.CharField(max_length=300)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-created_at"]

    def __str__(self):
        return f"Thread #{self.pk}: {self.subject}"

    @property
    def unread_count(self):
        return self.messages.filter(is_read=False, sender_role="client").count()


class Message(models.Model):
    ROLE_CHOICES = [
        ("client", "Client"),
        ("admin", "Admin"),
    ]

    thread = models.ForeignKey(MessageThread, on_delete=models.CASCADE, related_name="messages")
    sender_name = models.CharField(max_length=200)
    sender_role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    
    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=['thread', 'created_at']),
            models.Index(fields=['thread', 'is_read', 'sender_role']),
        ]

    def __str__(self):
        return f"[{self.sender_role}] {self.sender_name} -> Thread #{self.thread_id}"