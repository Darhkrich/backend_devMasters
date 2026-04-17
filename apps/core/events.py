from collections import defaultdict

from django.db import transaction


_EVENT_HANDLERS = defaultdict(list)


def register_event_handler(event_name):
    def decorator(func):
        if func not in _EVENT_HANDLERS[event_name]:
            _EVENT_HANDLERS[event_name].append(func)
        return func

    return decorator


def publish_event(event_name, *, payload=None, on_commit=True):
    payload = payload or {}

    def dispatch():
        for handler in _EVENT_HANDLERS.get(event_name, []):
            handler(payload)

    if on_commit:
        transaction.on_commit(dispatch)
    else:
        dispatch()
