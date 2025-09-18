from __future__ import annotations

import logging
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from django.conf import settings
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .text import normalize
from .utils import artifacts_dir, read_manifest, write_manifest

logger = logging.getLogger(__name__)

INDEX_NAME = "assistant_index"
PICKLE_FILE = "assistant_index.pkl"


@dataclass
class AssistantIndex:
    version: str
    ids: list[str]
    chunks: list[str]
    X: Any
    vectorizer: TfidfVectorizer
    meta: dict[str, dict[str, Any]]


def _load_corpus() -> tuple[list[str], list[str], dict[str, dict[str, Any]]]:
    src_dir = Path(settings.ML_ASSISTANT_CORPUS_DIR)
    ids, chunks, meta = [], [], {}
    if not src_dir.exists():
        src_dir.mkdir(parents=True, exist_ok=True)
        return ids, chunks, meta
    for p in src_dir.rglob("*"):
        if p.suffix.lower() not in {".md", ".txt"}:
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        # chunking simple par paragraphes
        parts = [normalize(x) for x in text.split("\n\n") if x.strip()]
        for i, ch in enumerate(parts):
            cid = f"{p.name}:{i}"
            ids.append(cid)
            chunks.append(ch)
            meta[cid] = {"path": str(p), "doc": p.name, "chunk": i}
    return ids, chunks, meta


def build_index(version: str | None = None) -> AssistantIndex:
    ids, chunks, meta = _load_corpus()
    n_docs = max(len(chunks), 1)
    vec = TfidfVectorizer(ngram_range=(1, 2), max_df=(1.0 if n_docs < 2 else 0.9), min_df=1, stop_words=None)
    X = vec.fit_transform(chunks) if chunks else vec.fit_transform(["vide"])
    idx = AssistantIndex(version=version or str(len(ids)), ids=ids, chunks=chunks, X=X, vectorizer=vec, meta=meta)
    save_index(idx)
    return idx


def save_index(idx: AssistantIndex) -> None:
    artifacts = artifacts_dir()
    blob = {"version": idx.version, "ids": idx.ids, "chunks": idx.chunks, "X": idx.X, "vectorizer": idx.vectorizer, "meta": idx.meta}
    with (artifacts / PICKLE_FILE).open("wb") as f:
        pickle.dump(blob, f)
    write_manifest(INDEX_NAME, {"version": idx.version, "count": len(idx.ids), "dim": int(idx.X.shape[1]), "file": PICKLE_FILE})


def load_index() -> AssistantIndex | None:
    artifacts = artifacts_dir()
    p = artifacts / PICKLE_FILE
    if not p.exists():
        return None
    with p.open("rb") as f:
        blob = pickle.load(f)
    return AssistantIndex(
        version=read_manifest(INDEX_NAME)["version"] if read_manifest(INDEX_NAME) else "0",
        ids=blob["ids"],
        chunks=blob["chunks"],
        X=blob["X"],
        vectorizer=blob["vectorizer"],
        meta=blob["meta"],
    )


def load_or_build() -> AssistantIndex:
    idx = load_index()
    if idx is None:
        idx = build_index()
    return idx


def retrieve(q: str, k: int = 5) -> list[dict[str, Any]]:
    idx = load_or_build()
    qv = idx.vectorizer.transform([normalize(q)])
    sims = cosine_similarity(qv, idx.X).ravel()
    order = np.argsort(-sims)[: max(k, 1)]
    out = []
    for i in order:
        cid = idx.ids[i] if i < len(idx.ids) else "N/A"
        out.append({"chunk_id": cid, "score": float(sims[i]), "text": idx.chunks[i] if i < len(idx.chunks) else "", "meta": idx.meta.get(cid, {})})
    return out
