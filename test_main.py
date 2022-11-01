from fastapi.testclient import TestClient
from firebase_admin import auth

from main import app

client = TestClient(app)


def test_successful_login():
    response = client.post(
        "/login", json={"email": "admin2@test.io", "password": "test123"})
    assert bool(response.json()["token"])


def test_successful_signup():
    try:
        # If user already signed up then do nothing.
        auth.get_user_by_email("new@test.io")
    except Exception:
        response = client.post(
            "/signup", json={"email": "new@test.io", "password": "test123"})
        assert response.json()["message"] == "User successfully created."
