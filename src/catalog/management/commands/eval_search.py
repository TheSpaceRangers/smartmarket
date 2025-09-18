import json
import time
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from catalog.models import Product
from ml.products_index import load_or_build, search as search_products, read_manifest
from ml.utils import artifacts_dir

def _p_at_k(found_ids, expected_ids, k):
    if k <= 0:
        return 0.0
    hits = sum(1 for pid in found_ids[:k] if pid in expected_ids)
    return hits / float(k)

class Command(BaseCommand):
    help = "Évalue la recherche produits (P@K) à partir d'un fichier JSON de paires requête→slugs attendus."

    def add_arguments(self, parser):
        parser.add_argument("--file", type=str, default="src/ml/eval/queries_demo.json")
        parser.add_argument("--k", type=int, default=10)

    def handle(self, *args, **opts):
        path = Path(opts["file"])
        k = int(opts["k"])
        if not path.exists():
            self.stderr.write(self.style.ERROR(f"Fichier introuvable: {path}"))
            return 1

        queries = json.loads(path.read_text(encoding="utf-8"))
        idx = load_or_build()
        manifest = read_manifest("product_index") or {"version": "0"}

        # Résoudre slugs -> ids
        needed_slugs = {s for q in queries for s in q.get("expected_slugs", [])}
        slug_map = {p.slug: p.id for p in Product.objects.filter(slug__in=list(needed_slugs)).only("id", "slug")}

        results = []
        scores = []
        for q in queries:
            text = q["q"]
            expected_ids = [slug_map[s] for s in q.get("expected_slugs", []) if s in slug_map]
            hits = search_products(text, k=k)
            found_ids = [h["product_id"] for h in hits]
            p_at_k = _p_at_k(found_ids, expected_ids, k)
            scores.append(p_at_k)
            results.append({
                "q": text,
                "expected_slugs": q.get("expected_slugs", []),
                "found_ids": found_ids,
                "p_at_k": round(p_at_k, 4),
            })

        macro = round(sum(scores) / len(scores), 4) if scores else 0.0
        report = {
            "index_version": manifest.get("version", "0"),
            "k": k,
            "count": len(queries),
            "macro_P@K": macro,
            "results": results,
            "timestamp": int(time.time()),
        }

        out_dir = artifacts_dir()
        ts = int(time.time())
        (out_dir / f"search_eval_{ts}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        (out_dir / "search_eval_latest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        self.stdout.write(self.style.SUCCESS(f"P@{k} macro={macro} sur {len(queries)} requêtes (version={report['index_version']})."))
        self.stdout.write(self.style.SUCCESS(f"Rapport: {out_dir / 'search_eval_latest.json'}"))