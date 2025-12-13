import copy

from fastapi.testclient import TestClient
import pytest

from src import app as app_module


@pytest.fixture(autouse=True)
def isolate_activities():
    # Keep a deep copy of the in-memory activities and restore after each test
    original = copy.deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(original)


def test_get_activities_contains_known_activity():
    client = TestClient(app_module.app)
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert "Chess Club" in data


def test_signup_and_unregister_flow():
    client = TestClient(app_module.app)
    activity = "Chess Club"
    email = "teststudent@example.com"

    # Ensure email is not already registered
    resp = client.get("/activities")
    participants = resp.json()[activity]["participants"]
    if email in participants:
        client.post(f"/activities/{activity}/unregister?email={email}")

    # Signup
    resp = client.post(f"/activities/{activity}/signup?email={email}")
    assert resp.status_code == 200
    assert "Signed up" in resp.json().get("message", "")

    # Verify participant present
    resp = client.get("/activities")
    assert email in resp.json()[activity]["participants"]

    # Unregister
    resp = client.post(f"/activities/{activity}/unregister?email={email}")
    assert resp.status_code == 200
    assert "Unregistered" in resp.json().get("message", "")

    # Verify removal
    resp = client.get("/activities")
    assert email not in resp.json()[activity]["participants"]


def test_duplicate_signup_is_rejected():
    client = TestClient(app_module.app)
    activity = "Chess Club"
    email = "duplicate@example.com"

    # Ensure fresh state
    client.post(f"/activities/{activity}/unregister?email={email}")

    # First signup should succeed
    resp = client.post(f"/activities/{activity}/signup?email={email}")
    assert resp.status_code == 200

    # Second signup should fail with 400
    resp = client.post(f"/activities/{activity}/signup?email={email}")
    assert resp.status_code == 400

    # Cleanup
    client.post(f"/activities/{activity}/unregister?email={email}")
