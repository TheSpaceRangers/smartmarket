import time
from hashlib import sha1

from django.core.cache import cache


def buster_key() -> str:
    v = cache.get("catalog:buster")
    return str(v or "0")


def bump_buster() -> None:
    cache.set("catalog:buster", int(time.time()), timeout=None)


def make_key(prefix: str, *parts: object) -> str:
    tokens = []
    for p in parts:
        s = str(p)
        # hash si espace, non-ASCII ou trop long
        if any(c.isspace() for c in s) or not s.isascii() or len(s) > 80:
            s = sha1(s.encode("utf-8")).hexdigest()
        s = s.replace(":", "_")
        tokens.append(s)
    return f"{prefix}:" + ":".join(tokens)
