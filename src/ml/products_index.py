from __future__ import annotations

import logging
import pickle
from dataclasses import dataclass
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from catalog.models import Product

from .text import normalize
from .utils import artifacts_dir, read_manifest, write_manifest

logger = logging.getLogger(__name__)

INDEX_NAME = "product_index"
PICKLE_FILE = "product_index.pkl"


@dataclass
class ProductIndex:
    version: str
    ids: np.ndarray
    X: Any  # scipy sparse
    vectorizer: TfidfVectorizer


def _product_doc(p: Product) -> str:
    parts = [p.name, p.description or "", getattr(p.category, "name", "")]
    return normalize(" ".join(parts))


def _build_corpus() -> tuple[list[int], list[str]]:
    qs = Product.objects.all().select_related("category").only("id", "name", "description", "category__name")
    ids, docs = [], []
    for p in qs:
        ids.append(p.id)
        docs.append(_product_doc(p))
    return ids, docs


def build_index(version: str | None = None) -> ProductIndex:
    ids, docs = _build_corpus()
    n_docs = len(docs)
    vec = TfidfVectorizer(ngram_range=(1, 2), max_df=(1.0 if n_docs < 2 else 0.9), min_df=1, stop_words=None)
    if n_docs == 0:
        vec.fit(["vide"])
        from scipy.sparse import csr_matrix

        X = csr_matrix((0, len(vec.vocabulary_)))
        ids_arr = np.array([], dtype=int)
    else:
        X = vec.fit_transform(docs)
        ids_arr = np.array(ids)
    idx = ProductIndex(version=version or str(len(ids)), ids=ids_arr, X=X, vectorizer=vec)
    save_index(idx)
    return idx


def save_index(idx: ProductIndex) -> None:
    artifacts = artifacts_dir()
    blob = {
        "version": idx.version,
        "ids": idx.ids,
        "X": idx.X,
        "vectorizer": idx.vectorizer,
    }
    with (artifacts / PICKLE_FILE).open("wb") as f:
        pickle.dump(blob, f)
    write_manifest(
        INDEX_NAME,
        {
            "version": idx.version,
            "count": int(idx.ids.size),
            "dim": int(idx.X.shape[1]),
            "file": PICKLE_FILE,
            "vectorizer": "tfidf(1,2)-fr",
        },
    )
    logger.info("PRODUCT_INDEX_SAVED version=%s count=%s dim=%s", idx.version, idx.ids.size, idx.X.shape[1])


def load_index() -> ProductIndex | None:
    artifacts = artifacts_dir()
    p = artifacts / PICKLE_FILE
    if not p.exists():
        return None
    with p.open("rb") as f:
        blob = pickle.load(f)
    return ProductIndex(
        version=read_manifest(INDEX_NAME)["version"] if read_manifest(INDEX_NAME) else "0",
        ids=blob["ids"],
        X=blob["X"],
        vectorizer=blob["vectorizer"],
    )


def load_or_build() -> ProductIndex:
    idx = load_index()
    if idx is None:
        idx = build_index()
    return idx


def _top_terms(vec, vocab, topk=5) -> list[str]:
    arr = vec.toarray().ravel()
    if arr.size == 0:
        return []
    nz = arr.nonzero()[0]
    pairs = sorted(((arr[i], i) for i in nz), reverse=True)[:topk]
    inv_vocab = {v: k for k, v in vocab.items()}
    return [inv_vocab[i] for _, i in pairs if i in inv_vocab]


def search(q: str, k: int = 10) -> list[dict[str, Any]]:
    idx = load_or_build()
    if idx.ids.size == 0:
        return []
    qn = normalize(q)
    qv = idx.vectorizer.transform([qn])
    sims = cosine_similarity(qv, idx.X).ravel()
    order = np.argsort(-sims)[: max(k, 1)]
    ids = idx.ids[order]
    results = []
    for pid, s in zip(ids, sims[order], strict=False):
        results.append({"product_id": int(pid), "score": float(s), "reason": f"Correspondance sur caractéristiques: {', '.join(_top_terms(qv, idx.vectorizer.vocabulary_))}"})
    return results


def recommend(product_id: int, k: int = 10, exclude_self: bool = True, ensure_diversity: bool = True) -> list[dict[str, Any]]:
    idx = load_or_build()
    if idx.ids.size == 0:
        return []
    try:
        pos = int(np.where(idx.ids == product_id)[0][0])
    except IndexError:
        return []
    pv = idx.X[pos]
    sims = cosine_similarity(pv, idx.X).ravel()
    # Exclure soi-même
    if exclude_self:
        sims[pos] = -1.0
    order = np.argsort(-sims)
    # Filtrage: actifs, stock > 0
    candidates = []
    qs = Product.objects.filter(id__in=list(idx.ids)).select_related("category").only("id", "is_active", "stock", "category__name", "name", "description")
    flags = {p.id: (p.is_active and p.stock > 0) for p in qs}
    cats = {p.id: getattr(p.category, "name", "") for p in qs}
    for i in order:
        pid = int(idx.ids[i])
        if not flags.get(pid, True):
            continue
        candidates.append((pid, float(sims[i])))
    # Diversité minimale (catégories différentes si possible)
    if ensure_diversity and candidates:
        selected, seen = [], set()
        for pid, sc in candidates:
            c = cats.get(pid, "")
            if c not in seen or len(selected) < max(2, k // 2):
                selected.append((pid, sc))
                seen.add(c)
            if len(selected) >= k:
                break
        if len(selected) < k:
            selected.extend(candidates[len(selected) : k])
    else:
        selected = candidates[:k]
    # Raisons: termes proches du produit source
    vocab = idx.vectorizer.vocabulary_
    reasons = ", ".join(_top_terms(pv, vocab))
    return [{"product_id": pid, "score": sc, "reason": f"Produits similaires (caractéristiques communes: {reasons})"} for pid, sc in selected]


def recommend_mmr(product_id: int, k: int = 10, mmr_lambda: float = 0.7) -> list[dict[str, Any]]:
    """Maximal Marginal Relevance pour diversifier les recommandations.

    mmr_lambda proche de 1 privilégie la similarité à la requête; proche de 0 privilégie la diversité.
    """
    idx = load_or_build()
    if idx.ids.size == 0:
        return []
    try:
        pos = int(np.where(idx.ids == product_id)[0][0])
    except IndexError:
        return []
    pv = idx.X[pos]
    sims_to_q = cosine_similarity(pv, idx.X).ravel()
    sims_to_q[pos] = -1.0  # exclure soi-même

    candidates = np.argsort(-sims_to_q).tolist()
    selected: list[int] = []
    selected_scores: list[float] = []

    while len(selected) < k and candidates:
        best_i, best_score = None, -1e9
        for i in candidates:
            if selected:
                sims_to_sel = cosine_similarity(idx.X[i], idx.X[selected]).ravel()
                redundancy = float(np.max(sims_to_sel))
            else:
                redundancy = 0.0
            score = mmr_lambda * float(sims_to_q[i]) - (1.0 - mmr_lambda) * redundancy
            if score > best_score:
                best_i, best_score = i, score
        selected.append(best_i)
        selected_scores.append(float(sims_to_q[best_i]))
        candidates.remove(best_i)

    vocab = idx.vectorizer.vocabulary_
    reasons = ", ".join(_top_terms(pv, vocab))
    return [{"product_id": int(idx.ids[i]), "score": sc, "reason": f"Diversification MMR (caractéristiques: {reasons})"} for i, sc in zip(selected, selected_scores, strict=False)]


# (supprimé doublon)
