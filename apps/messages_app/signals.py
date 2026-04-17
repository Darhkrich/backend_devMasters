from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Message

from apps.notifications.models import Notification
@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    if not created:
        return
    thread = instance.thread
    if instance.sender_role == 'client':
        # Notify admins (all superusers)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        recipients = User.objects.filter(is_superuser=True)
        for recipient in recipients:
            Notification.objects.create(
                recipient=recipient,
                notification_type='message',
                title=f'New message from {instance.sender_name}',
                message=instance.body[:200],
                link=f'/dashboard-admin/messages/{thread.id}',
                metadata={'thread_id': thread.id, 'sender_role': instance.sender_role}
            )
    else:  # admin sent message -> notify client
        # Find the client user associated with the thread
        client_user = None
        if thread.client and thread.client.email:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                client_user = User.objects.get(email=thread.client.email)
            except User.DoesNotExist:
                pass
        elif thread.order and thread.order.user:
            client_user = thread.order.user
        elif thread.inquiry and thread.inquiry.user:
            client_user = thread.inquiry.user
        if client_user:
            Notification.objects.create(
                recipient=client_user,
                notification_type='message',
                title=f'New message from team',
                message=instance.body[:200],
                link=f'/dashboard/messages/{thread.id}',
                metadata={'thread_id': thread.id, 'sender_role': instance.sender_role}
            )