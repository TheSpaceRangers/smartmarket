from decimal import Decimal

import pytest

from catalog.models import Category, Product


@pytest.mark.django_db
def test_api_product_list_ok(client):
    c = Category.objects.create(name="Livres", slug="livres")
    Product.objects.create(category=c, name="A", slug="a", price=Decimal("1.00"))
    resp = client.get("/api/v1/products/")
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert any(p["slug"] == "a" for p in data["results"])


@pytest.mark.django_db
def test_api_product_detail_ok(client):
    c = Category.objects.create(name="Livres", slug="livres")
    Product.objects.create(category=c, name="A", slug="a", price=Decimal("1.00"))
    resp = client.get("/api/v1/products/a/")
    assert resp.status_code == 200
    assert resp.json()["slug"] == "a"


@pytest.mark.django_db
def test_api_product_post_forbidden_anonymous(client):
    resp = client.post("/api/v1/products/", json={"name": "X"})
    assert resp.status_code in (401, 403)
