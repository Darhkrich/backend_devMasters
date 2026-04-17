from .models import AuditLog


def log_action(
    user=None,
    action="OTHER",
    model_name=None,
    object_id=None,
    request=None,
    status_code=200,
    response_time=0,
):

    ip = None
    method = None
    path = None

    if request:
        ip = request.META.get("HTTP_X_FORWARDED_FOR")
        if ip:
            ip = ip.split(",")[0].strip()
        else:            
            ip = request.META.get("REMOTE_ADDR")
        method = request.method
        path = request.path

    AuditLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=object_id,
        ip_address=ip,
        method=method,
        path=path,
        status_code=status_code,
        response_time=response_time,
    )
