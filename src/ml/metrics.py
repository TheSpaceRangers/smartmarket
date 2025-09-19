from __future__ import annotations

import json

from django.core.cache import cache

MAX_SAMPLES = 200


def _list_key(name: str) -> str:
    return f"metrics:list:{name}"


def _counter_key(name: str) -> str:
    return f"metrics:counter:{name}"


def record_duration(name: str, ms: int) -> None:
    key = _list_key(name)
    raw = cache.get(key)
    arr: list[int] = json.loads(raw) if isinstance(raw, str) else (raw or [])
    arr.append(int(ms))
    if len(arr) > MAX_SAMPLES:
        arr = arr[-MAX_SAMPLES:]
    cache.set(key, json.dumps(arr), timeout=None)


def p95(name: str) -> int:
    raw = cache.get(_list_key(name))
    arr: list[int] = json.loads(raw) if isinstance(raw, str) else (raw or [])
    if not arr:
        return 0
    arr2 = sorted(arr)
    idx = int(0.95 * (len(arr2) - 1))
    return int(arr2[idx])


def incr_counter(name: str, delta: int = 1) -> None:
    key = _counter_key(name)
    cache.set(key, int(cache.get(key, 0)) + int(delta), timeout=None)


def get_counter(name: str) -> int:
    return int(cache.get(_counter_key(name), 0))
