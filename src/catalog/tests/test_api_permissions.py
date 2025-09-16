import pytest
from django.contrib.auth.models import Group, User
from rest_framework.test import APIClient

from catalog.models import Category


@pytest.mark.django_db
def test_anonymous_cannot_create_product():
    client = APIClient()
    payload = {"name": "X", "slug": "x", "price": "9.99", "category": None}
    resp = client.post("/api/v1/products/", payload, format="json")
    assert resp.status_code in (401, 403)


@pytest.mark.django_db
def test_manager_can_crud_product():
    manager = User.objects.create_user(username="m1", password="manager", is_staff=True)
    manager.groups.add(Group.objects.get_or_create(name="manager")[0])

    c = Category.objects.create(name="Livres", slug="livres")

    client = APIClient()
    client.force_authenticate(user=manager)

    resp = client.post(
        "/api/v1/products/",
        {
            "name": "Livre X",
            "slug": "livre-x",
            "price": "12.50",
            "stock": 5,
            "is_active": True,
            "category": c.id,
        },
        format="json",
    )
    assert resp.status_code == 201, resp.content

    resp = client.patch("/api/v1/products/livre-x/", {"price": "14.00"}, format="json")
    assert resp.status_code == 200
    assert resp.json()["price"] == "14.00"

    resp = client.delete("/api/v1/products/livre-x/")
    assert resp.status_code in (204, 200)
