import hashlib
import json

from django.core.cache import cache


def build_cache_key(prefix, **parts):
    serialized = json.dumps(parts, sort_keys=True, default=str)
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return f"{prefix}:{digest}"


def cache_get_or_set(prefix, *, timeout, builder, **parts):
    key = build_cache_key(prefix, **parts)
    value = cache.get(key)
    if value is not None:
        return value

    value = builder()
    cache.set(key, value, timeout)
    return value
