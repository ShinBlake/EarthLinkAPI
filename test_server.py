from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# Tests for creating account
def test_create_account_success():
    # Replace with appropriate test data
    response = client.post("/signup", json={"email": "newuser@example.com", "password": "password123"})
    assert response.status_code == 201
    assert "User account created successfully" in response.json()["message"]

def test_create_account_existing_email():
    # This should be an email that already exists in your Firebase project
    response = client.post("/signup", json={"email": "existinguser@example.com", "password": "password123"})
    assert response.status_code == 400
    assert "Account already created for the email" in response.json()["detail"]

def test_create_account_invalid_data():
    # Sending invalid email format
    response = client.post("/signup", json={"email": "invalidemail", "password": "password123"})
    # Assuming your endpoint handles validation and returns 422 for invalid data
    assert response.status_code == 422
    # Further assertions can be added based on your error handling


#tests for login
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

def test_login_success():
    # Replace with valid test credentials
    response = client.post("/login", json={"email": "validuser@example.com", "password": "validpassword"})
    assert response.status_code == 200
    assert "token" in response.json()

def test_login_invalid_credentials():
    # Use invalid credentials for this test
    response = client.post("/login", json={"email": "invalid@example.com", "password": "wrongpassword"})
    assert response.status_code == 400
    assert "Invalid email/password" in response.json()["detail"]


#testig ping
def test_validate_token():
    # Assuming you have a way to get or mock a valid token
    valid_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjlhNTE5MDc0NmU5M2JhZTI0OWIyYWE3YzJhYTRlMzA2M2UzNDFlYzciLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vZWFydGhsaW5rcy03YzQ5MSIsImF1ZCI6ImVhcnRobGlua3MtN2M0OTEiLCJhdXRoX3RpbWUiOjE2OTYxNzc0OTAsInVzZXJfaWQiOiJzd2xmS09wa3V1UTRGQmc1ZmNHU3Fucmd2MzEyIiwic3ViIjoic3dsZktPcGt1dVE0RkJnNWZjR1NxbnJndjMxMiIsImlhdCI6MTY5NjE3NzQ5MCwiZXhwIjoxNjk2MTgxMDkwLCJlbWFpbCI6InNhbXBsZUBzYW1wbGUuY29tIiwiZW1haWxfdmVyaWZpZWQiOmZhbHNlLCJmaXJlYmFzZSI6eyJpZGVudGl0aWVzIjp7ImVtYWlsIjpbInNhbXBsZUBzYW1wbGUuY29tIl19LCJzaWduX2luX3Byb3ZpZGVyIjoicGFzc3dvcmQifX0.LGhIMaQledbGbUEMG0Ls3n1c9Y_nJZyWOHDs1n72qA8Xm3ydtORPtHwAzgPD3-LhBsGf4P4btbKpPWRn2yrXYaoMzDcpqax1XGQM0xefflWScUHtZFIx24isuFCSZxri8-V8-W_ul_hkri2076iuMaTD7B9yxKbPKDMwMO8e8YWZetGh-a-gvDfq-HolsXRyaLSGhnQCdcMkW0PpTLaG_h5du4XsmZCgJH3H0DYWhSV4EZvDfpckNJcMBEMvmh7RyQWsIYWh2jyhPr06--u6seSNrEd0pTxxSoQ3cIh_vn6rRoRIXk45pZa-XbMhANsj3-zQKgv4bXIh_9nJdTeJWA"
    response = client.post("/ping", headers={"authorization": valid_token})
    # Assuming the successful response returns a user_id
    assert response.status_code == 200
    assert "user_id" in response.json()


#testing post

def test_post_message_success():
    # Replace with appropriate test data
    message_data = {
        "user_uid": "user123",
        "message_content": "Hello, world!",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "timestamp": "2023-11-11T21:09:32.840000+00:00"
    }
    with patch('message-test') as mock_db:
        mock_db.return_value.push.return_value = {"name": "test_message_id"}
        response = client.post("/message", json=message_data)
    assert response.status_code == 200
    assert response.json()["message"] == "Message posted successfully"

def test_post_message_invalid_data():
    # Example with missing 'user_uid'
    message_data = {
        "message_content": "Hello, world!",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "timestamp": "2023-11-11T21:09:32.840000+00:00"
    }
    response = client.post("/message", json=message_data)
    # Assuming your endpoint validates data and returns 422 for invalid data
    assert response.status_code == 422

def test_post_message_firebase_error():
    message_data = {
        "user_uid": "user123",
        "message_content": "Hello, world!",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "timestamp": "2023-11-11T21:09:32.840000+00:00"
    }
    with patch('message-test') as mock_db:
        mock_db.return_value.push.side_effect = Exception("Firebase error")
        response = client.post("/message", json=message_data)
    assert response.status_code == 400
    assert "Failed to store message" in response.json()["detail"]