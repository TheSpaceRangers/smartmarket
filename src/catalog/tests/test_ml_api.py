from decimal import Decimal
import pytest
from django.conf import settings
from catalog.models import Category, Product
from ml.products_index import build_index, recommend, search as search_products
from ml.assistant import answer

@pytest.mark.django_db
def test_similarity_self_max():
    c = Category.objects.create(name="Livres", slug="livres")
    a = Product.objects.create(category=c, name="Python avancé", slug="py-adv", price=Decimal("10.00"), description="Livre Python pour experts", stock=5)
    Product.objects.create(category=c, name="Cuisine facile", slug="cook", price=Decimal("5.00"), description="Recettes", stock=3)
    build_index()
    # la similarité propre devrait être max si non exclue
    recs = recommend(a.id, k=1, exclude_self=False)
    assert recs and recs[0]["product_id"] == a.id

@pytest.mark.django_db
def test_search_api(client):
    c = Category.objects.create(name="Informatique", slug="info")
    p = Product.objects.create(category=c, name="Clavier mécanique", slug="kb", price=Decimal("49.00"), description="Switchs bleus", stock=10)
    build_index()
    resp = client.get("/api/v1/search/?q=clavier&k=5")
    assert resp.status_code == 200
    data = resp.json()
    assert any(r["slug"] == "kb" for r in data["results"])

@pytest.mark.django_db
def test_recommendations_api(client):
    c = Category.objects.create(name="Audio", slug="audio")
    p1 = Product.objects.create(category=c, name="Casque HiFi", slug="hifi", price=Decimal("99.00"), description="Hi-Res audio", stock=10)
    p2 = Product.objects.create(category=c, name="Casque Sport", slug="sport", price=Decimal("59.00"), description="Résistant à la sueur", stock=10)
    build_index()
    resp = client.get(f"/api/v1/products/{p1.id}/recommendations/?k=5")
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data and len(data["results"]) >= 1
    assert "reason" in data["results"][0]

def test_assistant_guardrails(tmp_path, monkeypatch):
    # garde-fous: hors corpus -> refus
    out = answer("question sans rapport", k=3)
    assert "trace_id" in out and isinstance(out["sources"], list)
    # si pas de source pertinente, doit l’indiquer
    assert "pas trouvé" in out["answer"] or "introuvable" in out["answer"]