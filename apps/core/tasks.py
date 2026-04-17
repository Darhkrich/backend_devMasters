import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Lock

from django.conf import settings
from django.db import transaction
from django.utils import timezone


_TASKS = {}
_EXECUTOR = None
_EXECUTOR_LOCK = Lock()
logger = logging.getLogger("backend.task_worker")


def register_task(name):
    def decorator(func):
        _TASKS[name] = func
        return func

    return decorator


def _get_executor():
    global _EXECUTOR
    if _EXECUTOR is None:
        with _EXECUTOR_LOCK:
            if _EXECUTOR is None:
                _EXECUTOR = ThreadPoolExecutor(
                    max_workers=getattr(settings, "TASK_QUEUE_WORKERS", 4)
                )
    return _EXECUTOR


def run_registered_task(name, **payload):
    task = _TASKS[name]
    return task(**payload)


def _enqueue_durable_task(name, payload):
    from apps.core.models import TaskJob

    return TaskJob.objects.create(name=name, payload=payload)


def enqueue_task(name, **payload):
    if name not in _TASKS:
        raise KeyError(f"Task '{name}' is not registered.")

    mode = getattr(settings, "TASK_QUEUE_MODE", "sync")

    if mode in {"worker", "durable", "db"}:
        return _enqueue_durable_task(name, payload)

    if mode == "thread":
        _get_executor().submit(run_registered_task, name, **payload)
        return None

    run_registered_task(name, **payload)
    return None


def claim_next_task(worker_name):
    from apps.core.models import TaskJob

    now = timezone.now()
    with transaction.atomic():
        task = (
            TaskJob.objects.select_for_update()
            .filter(status=TaskJob.STATUS_PENDING, available_at__lte=now)
            .order_by("available_at", "created_at")
            .first()
        )
        if not task:
            return None

        task.status = TaskJob.STATUS_RUNNING
        task.locked_at = now
        task.locked_by = worker_name
        task.attempts += 1
        task.last_error = ""
        task.save()
        return task


def complete_task(task):
    from apps.core.models import TaskJob

    if task.status != TaskJob.STATUS_RUNNING:
        return task

    task.status = TaskJob.STATUS_COMPLETED
    task.completed_at = timezone.now()
    task.locked_at = None
    task.locked_by = ""
    task.save()
    logger.info("Task completed: %s", task.name)
    return task


def fail_task(task, exc):
    from apps.core.models import TaskJob

    task.locked_at = None
    task.locked_by = ""
    task.last_error = str(exc)

    if task.attempts >= task.max_attempts:
        task.status = TaskJob.STATUS_FAILED
        task.failed_at = timezone.now()
        logger.error("Task failed permanently: %s", task.name)
    else:
        delay_seconds = min(300, 2 ** max(task.attempts, 1))
        task.status = TaskJob.STATUS_PENDING
        task.available_at = timezone.now() + timedelta(seconds=delay_seconds)
        logger.warning("Task scheduled for retry: %s", task.name)

    task.save()
    return task


def process_task(task):
    try:
        run_registered_task(task.name, **task.payload)
    except Exception as exc:
        fail_task(task, exc)
        raise

    complete_task(task)
    return task


def run_worker_cycle(worker_name):
    task = claim_next_task(worker_name)
    if not task:
        return False

    try:
        process_task(task)
    except Exception:
        logger.exception("Task execution failed for %s", task.name)
    return True
