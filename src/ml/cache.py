from time import time

from django.core.cache import cache


def buster_key() -> str:
    v = cache.get("catalog:buster")
    return str(v or "0")


def bump_buster() -> None:
    cache.set("catalog:buster", int(time()), timeout=None)
