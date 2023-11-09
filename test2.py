from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_signup_existing_user():
    response = client.post(
        "/signup",
        json={
            "email": "sample@gmail.com",
            "password": "samplepass123"
        }
    )
    assert response.status_code == 400
    assert "Account already created for the email" in response.text


def test_login_invalid_credentials():
    response = client.post(
        "/login",
        json={
            "email": "nonexistent@gmail.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 400
    assert "Invalid email/password" in response.text
