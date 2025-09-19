
import pytest
from django.conf import settings
from django.test import override_settings

from ml.assistant_index import build_index as build_assistant
from ml.products_index import build_index
from ml.utils import read_manifest


@pytest.mark.django_db
def test_manifests_present_after_build():
    # produits
    build_index(version="test-v")
    m1 = read_manifest("product_index")
    assert m1 and "version" in m1 and m1["version"] in ("test-v", m1["version"])
    # assistant
    build_assistant(version="rag-v")
    m2 = read_manifest("assistant_index")
    assert m2 and "version" in m2 and m2["version"] in ("rag-v", m2["version"])


@pytest.mark.django_db
def test_assistant_api_throttling(client):
    # Baisse le quota assistant pour le test
    rates = dict(settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"])
    rates["assistant"] = "2/min"
    with override_settings(REST_FRAMEWORK={**settings.REST_FRAMEWORK, "DEFAULT_THROTTLE_RATES": rates}):
        # 1er OK
        r1 = client.post("/api/v1/assistant/ask/", data={"q": "politique de retour", "k": 2}, content_type="application/json")
        assert r1.status_code == 200
        # 2e OK
        r2 = client.post("/api/v1/assistant/ask/", data={"q": "politique de retour", "k": 2}, content_type="application/json")
        assert r2.status_code == 200
        # 3e doit être limité
        r3 = client.post("/api/v1/assistant/ask/", data={"q": "politique de retour", "k": 2}, content_type="application/json")
        assert r3.status_code in (429, 403)  # 429 attendu
