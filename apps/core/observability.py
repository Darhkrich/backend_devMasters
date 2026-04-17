import contextvars
import json
import logging
import time
import uuid

from django.conf import settings
from django.core.cache import cache


request_id_var = contextvars.ContextVar("request_id", default="-")
trace_id_var = contextvars.ContextVar("trace_id", default="-")

logger = logging.getLogger("backend.request")


def set_request_context(request_id, trace_id):
    request_id_var.set(request_id)
    trace_id_var.set(trace_id)


def clear_request_context():
    request_id_var.set("-")
    trace_id_var.set("-")


class RequestContextFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get()
        record.trace_id = trace_id_var.get()
        return True


class StructuredFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
            "trace_id": getattr(record, "trace_id", "-"),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def new_request_context(request):
    incoming_request_id = request.headers.get("X-Request-ID")
    incoming_trace_id = request.headers.get("X-Trace-ID")
    request_id = incoming_request_id or str(uuid.uuid4())
    trace_id = incoming_trace_id or request_id
    set_request_context(request_id, trace_id)
    request.request_id = request_id
    request.trace_id = trace_id
    request._request_started_at = time.perf_counter()
    return request_id, trace_id


def record_request_metrics(request, response):
    started_at = getattr(request, "_request_started_at", None)
    if started_at is None:
        return 0

    duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
    total_key = "metrics:requests:total"
    status_key = f"metrics:requests:status:{response.status_code}"
    path_key = f"metrics:requests:path:{request.path}"
    slow_key = "metrics:requests:slow"

    for key, increment in ((total_key, 1), (status_key, 1), (path_key, 1)):
        try:
            cache.incr(key, increment)
        except ValueError:
            cache.set(key, increment, None)

    slow_threshold = getattr(settings, "REQUEST_SLOW_THRESHOLD_MS", 500)
    if duration_ms >= slow_threshold:
        try:
            cache.incr(slow_key, 1)
        except ValueError:
            cache.set(slow_key, 1, None)

    return duration_ms


def metrics_snapshot():
    total = cache.get("metrics:requests:total", 0)
    slow = cache.get("metrics:requests:slow", 0)
    statuses = {}
    for status_code in (200, 201, 204, 400, 401, 403, 404, 429, 500):
        statuses[str(status_code)] = cache.get(f"metrics:requests:status:{status_code}", 0)

    return {
        "requests_total": total,
        "slow_requests_total": slow,
        "status_counts": statuses,
    }


def log_request_completed(request, response, duration_ms):
    payload = {
        "method": request.method,
        "path": request.path,
        "status_code": response.status_code,
        "duration_ms": duration_ms,
        "user_id": getattr(getattr(request, "user", None), "id", None),
        "version": getattr(request, "version", None),
    }

    level = logging.INFO
    if response.status_code >= 500:
        level = logging.ERROR
    elif duration_ms >= getattr(settings, "REQUEST_SLOW_THRESHOLD_MS", 500):
        level = logging.WARNING

    logger.log(level, json.dumps(payload, default=str))
