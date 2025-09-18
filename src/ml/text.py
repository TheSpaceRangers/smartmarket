from re import U, compile, sub

_ws = compile(r"\s+")


def normalize(s: str) -> str:
    s = (s or "").strip().lower()
    s = sub(r"[^\w\s-]", " ", s, flags=U)
    s = _ws.sub(" ", s)
    return s
