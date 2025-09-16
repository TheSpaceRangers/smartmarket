import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_rgpd_throttle_429():
    u = User.objects.create_user("alice", password="x")
    c = APIClient()
    c.force_authenticate(user=u)
    for _ in range(10):
        assert c.get("/api/v1/me/export/").status_code == 200
    assert c.get("/api/v1/me/export/").status_code == 429
