from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from .assistant_index import retrieve
from .utils import read_manifest

logger = logging.getLogger(__name__)


def answer(q: str, k: int = 5, threshold: float = 0.1) -> dict[str, Any]:
    t0 = time.monotonic()
    trace_id = str(uuid.uuid4())
    version = (read_manifest("assistant_index") or {}).get("version", "0")
    hits = retrieve(q, k=k)
    if not hits or (hits and hits[0]["score"] < threshold):
        msg = "Je n'ai pas trouvé d'information fiable dans la base documentaire pour répondre à cette question."
        dt_ms = int((time.monotonic() - t0) * 1000)
        logger.info("ASSISTANT_ASK time_ms=%s trace_id=%s q_len=%s k=%s hits=0 version=%s", dt_ms, trace_id, len(q), k, version)
        return {"trace_id": trace_id, "version": version, "answer": msg, "sources": []}
    snippets = [h["text"] for h in hits[:2] if h["text"]]
    answer = " ".join(snippets)[:800]
    sources = [{"id": h["chunk_id"], "score": h["score"], "meta": h["meta"]} for h in hits]
    dt_ms = int((time.monotonic() - t0) * 1000)
    logger.info("ASSISTANT_ASK time_ms=%s trace_id=%s q_len=%s k=%s version=%s top=%s", dt_ms, trace_id, len(q), k, version, [(s["id"], s["score"]) for s in sources[:3]])
    return {"trace_id": trace_id, "version": version, "answer": answer, "sources": sources}
