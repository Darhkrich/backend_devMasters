from django.db import transaction

from apps.clients.services import sync_client_metrics, upsert_client_profile
from apps.core.sanitization import sanitize_text
from apps.messages_app.models import Message, MessageThread
from apps.orders.models import Order, OrderActivity, OrderItem


@transaction.atomic
def convert_inquiry_to_order(inquiry, actor=None, admin_notes="", initial_message=""):
    admin_notes = sanitize_text(admin_notes, multiline=True)
    initial_message = sanitize_text(initial_message, multiline=True)

    existing_order = getattr(inquiry, "order", None)
    if existing_order is not None:
        return existing_order, False

    client = inquiry.client or upsert_client_profile(
        name=inquiry.name,
        email=inquiry.email,
        phone=inquiry.phone,
        company=inquiry.company,
    )

    order = Order.objects.create(
        user=inquiry.user,
        client=client,
        inquiry=inquiry,
        client_name=inquiry.name,
        client_email=inquiry.email,
        client_company=inquiry.company,
        project_details=inquiry.project_details or inquiry.message,
        timeline=inquiry.timeline,
        total_amount=inquiry.estimated_total or None,
        notes=inquiry.message,
        admin_notes=admin_notes,
        metadata=inquiry.metadata,
    )

    for item in inquiry.items.all():
        OrderItem.objects.create(
            order=order,
            item_type=item.item_type,
            item_id=item.item_id,
            title=item.title,
            price=item.price,
            quantity=item.quantity,
            metadata=item.metadata,
        )

    OrderActivity.objects.create(
        order=order,
        message=f"Order created from inquiry #{inquiry.pk}",
        created_by=actor,
    )

    inquiry.client = client
    inquiry.status = inquiry.STATUS_RESOLVED
    if admin_notes and not inquiry.admin_reply:
        inquiry.admin_reply = admin_notes
    inquiry.save(update_fields=["client", "status", "admin_reply", "updated_at"])

    thread = MessageThread.objects.filter(order=order).first()
    if thread is None:
        thread = MessageThread.objects.create(
            client=client,
            inquiry=inquiry,
            order=order,
            subject=f"Order {order.reference}",
        )
        Message.objects.create(
            thread=thread,
            sender_name=(
                actor.get_full_name().strip() if actor and actor.get_full_name().strip() else "Admin Team"
            ),
            sender_role="admin",
            body=initial_message or "Your inquiry has been converted into an active order.",
        )

    sync_client_metrics(client)
    return order, True
