import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from catalog.models import Order


@pytest.mark.django_db
def test_orders_requires_auth():
    client = APIClient()
    assert client.get("/api/v1/orders/").status_code in (401, 403)


@pytest.mark.django_db
def test_user_sees_only_own_orders():
    u1 = User.objects.create_user("alice", password="x")
    u2 = User.objects.create_user("bob", password="x")
    o1 = Order.objects.create(user=u1)
    Order.objects.create(user=u2)

    client = APIClient()
    client.force_authenticate(user=u1)

    resp = client.get("/api/v1/orders/")
    assert resp.status_code == 200
    ids = [row["id"] for row in resp.json().get("results", [])] if isinstance(resp.json(), dict) else [row["id"] for row in resp.json()]
    assert o1.id in ids and len(ids) == 1


@pytest.mark.django_db
def test_user_cannot_read_others_order():
    u1 = User.objects.create_user("alice", password="x")
    u2 = User.objects.create_user("bob", password="x")
    o2 = Order.objects.create(user=u2)

    client = APIClient()
    client.force_authenticate(user=u1)
    resp = client.get(f"/api/v1/orders/{o2.id}/")
    assert resp.status_code in (403, 404)


@pytest.mark.django_db
def test_user_can_create_own_order():
    u = User.objects.create_user("alice", password="x")
    client = APIClient()
    client.force_authenticate(user=u)
    resp = client.post("/api/v1/orders/", {"status": "pending"}, format="json")
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "pending"
    assert Order.objects.filter(id=data["id"], user=u).exists()
