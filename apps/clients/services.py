from apps.clients.models import ClientProfile


def upsert_client_profile(*, name, email, phone="", company=""):
    normalized_email = (email or "").strip().lower()
    if not normalized_email:
        return None

    defaults = {
        "name": name or normalized_email,
        "phone": phone or "",
        "company": company or "",
    }
    client, _ = ClientProfile.objects.get_or_create(
        email=normalized_email,
        defaults=defaults,
    )

    updated_fields = []
    for field, value in defaults.items():
        if value and getattr(client, field) != value:
            setattr(client, field, value)
            updated_fields.append(field)

    if updated_fields:
        client.save(update_fields=updated_fields + ["updated_at"])

    return client


def sync_client_metrics(client):
    if client is None:
        return None

    from apps.orders.models import Order

    active_statuses = [
        Order.STATUS_PENDING,
        Order.STATUS_REVIEWED,
        Order.STATUS_IN_PROGRESS,
        Order.STATUS_AWAITING_CLIENT,
    ]
    active_projects = client.orders.filter(status__in=active_statuses).count()
    if client.active_projects != active_projects:
        client.active_projects = active_projects
        client.save(update_fields=["active_projects", "updated_at"])

    return client


def client_has_business_records(client):
    return any(
        (
            client.orders.exists(),
            client.inquiries.exists(),
            client.threads.exists(),
            client.tickets.exists(),
        )
    )
