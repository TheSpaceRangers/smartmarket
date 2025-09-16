from decimal import Decimal

import pytest
from django.urls import reverse

from catalog.models import Category, Product


@pytest.mark.django_db
def test_product_list_view(client):
    assert client.get(reverse("catalog:product_list")).status_code == 200


@pytest.mark.django_db
def test_product_detail_view(client):
    c = Category.objects.create(name="Livres", slug="livres")
    p = Product.objects.create(category=c, name="A", slug="a", price=Decimal("1.00"))
    resp = client.get(reverse("catalog:product_detail", kwargs={"slug": p.slug}))
    assert resp.status_code == 200
