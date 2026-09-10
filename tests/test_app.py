import copy

import pytest
from fastapi.testclient import TestClient

import app as app_module

client = TestClient(app_module.app)


@pytest.fixture(autouse=True)
def reset_capabilities():
    """Restore the in-memory capabilities dict after each test so tests don't leak state."""
    original = copy.deepcopy(app_module.capabilities)
    yield
    app_module.capabilities.clear()
    app_module.capabilities.update(copy.deepcopy(original))


def test_root_redirects_to_static_index():
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/static/index.html"


def test_get_capabilities_returns_seeded_catalog():
    response = client.get("/capabilities")
    assert response.status_code == 200
    data = response.json()
    assert "Cloud Architecture" in data
    assert data["Cloud Architecture"]["practice_area"] == "Technology"
    assert "alice.smith@slalom.com" in data["Cloud Architecture"]["consultants"]


def test_register_for_capability_success():
    response = client.post(
        "/capabilities/Cloud Architecture/register",
        params={"email": "new.consultant@slalom.com"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "message": "Registered new.consultant@slalom.com for Cloud Architecture"
    }
    assert "new.consultant@slalom.com" in app_module.capabilities["Cloud Architecture"]["consultants"]


def test_register_for_unknown_capability_returns_404():
    response = client.post(
        "/capabilities/Unknown Capability/register",
        params={"email": "someone@slalom.com"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Capability not found"


def test_register_duplicate_consultant_returns_400():
    response = client.post(
        "/capabilities/Cloud Architecture/register",
        params={"email": "alice.smith@slalom.com"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Consultant is already registered for this capability"


def test_unregister_from_capability_success():
    response = client.request(
        "DELETE",
        "/capabilities/Cloud Architecture/unregister",
        params={"email": "alice.smith@slalom.com"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "message": "Unregistered alice.smith@slalom.com from Cloud Architecture"
    }
    assert "alice.smith@slalom.com" not in app_module.capabilities["Cloud Architecture"]["consultants"]


def test_unregister_from_unknown_capability_returns_404():
    response = client.request(
        "DELETE",
        "/capabilities/Unknown Capability/unregister",
        params={"email": "someone@slalom.com"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Capability not found"


def test_unregister_consultant_not_registered_returns_400():
    response = client.request(
        "DELETE",
        "/capabilities/Cloud Architecture/unregister",
        params={"email": "not.registered@slalom.com"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Consultant is not registered for this capability"
