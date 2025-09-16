import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from catalog.models import Order


@pytest.mark.django_db
def test_me_export_requires_auth():
    client = APIClient()
    assert client.get("/api/v1/me/export/").status_code in (401, 403)


@pytest.mark.django_db
def test_me_export_returns_only_self_data():
    u1 = User.objects.create_user("alice", password="x", email="a@x.tld")
    u2 = User.objects.create_user("bob", password="x", email="b@x.tld")
    Order.objects.create(user=u1)
    Order.objects.create(user=u2)

    client = APIClient()
    client.force_authenticate(user=u1)
    resp = client.get("/api/v1/me/export/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "alice"
    assert all(o["id"] for o in data["orders"])
    assert len(data["orders"]) == 1


@pytest.mark.django_db
def test_me_erase_disables_user_and_deletes_orders():
    u = User.objects.create_user("alice", password="x", email="a@x.tld")
    o = Order.objects.create(user=u)

    client = APIClient()
    client.force_authenticate(user=u)
    resp = client.post("/api/v1/me/erase/")
    assert resp.status_code in (200, 202)

    u.refresh_from_db()
    assert not u.is_active
    assert Order.objects.filter(pk=o.pk).count() == 0
