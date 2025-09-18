from __future__ import annotations
import logging
import uuid
from typing import Dict, Any, List

from .assistant_index import retrieve

logger = logging.getLogger(__name__)

def answer(q: str, k: int = 5, threshold: float = 0.1) -> Dict[str, Any]:
    trace_id = str(uuid.uuid4())
    hits = retrieve(q, k=k)
    if not hits or (hits and hits[0]["score"] < threshold):
        msg = "Je n'ai pas trouvé d'information fiable dans la base documentaire pour répondre à cette question."
        logger.info("ASSISTANT_ASK trace_id=%s q=%r k=%s hits=0", trace_id, q, k)
        return {"trace_id": trace_id, "answer": msg, "sources": []}
    # réponse extractive très simple: concaténer 1-2 meilleurs snippets
    snippets = [h["text"] for h in hits[:2] if h["text"]]
    answer = " ".join(snippets)[:800]
    sources = [{"id": h["chunk_id"], "score": h["score"], "meta": h["meta"]} for h in hits]
    logger.info("ASSISTANT_ASK trace_id=%s q=%r k=%s top=%s", trace_id, q, k, [(s['id'], s['score']) for s in sources[:3]])
    return {"trace_id": trace_id, "answer": answer, "sources": sources}