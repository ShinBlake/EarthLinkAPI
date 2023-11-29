from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch
import uvicorn
import pyrebase
from models import *
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from fastapi.requests import Request
import firebase_admin
from firebase_admin import credentials,auth
import geohash2
from geopy.distance import distance
import numpy as np
from geopy.distance import great_circle
import ast
import random
import string

def generate_random_string(length=6):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string

# Generate a 6-character random alphanumeric string


client = TestClient(app)


# Tests for creating account
def test_create_account_success():
    # Replace with appropriate test data
    random_string = generate_random_string()
    email = random_string + "@gmail.com"
    response = client.post("/signup", json={"email": email, "password": "password123"})
    assert response.status_code == 201

def test_create_account_existing_email():
    # This should be an email that already exists in your Firebase project
    response = client.post("/signup", json={"email": "string@gmail.com", "password": "password123"})
    assert response.status_code == 400
    assert "Account already created for the email" in response.json()["detail"]

def test_create_account_invalid_data():
    # Sending invalid email format
    response = client.post("/signup", json={"email": "invalidemail", "password": "password123"})
    # Assuming your endpoint handles validation and returns 422 for invalid data
    assert response.status_code == 422
 


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
    response = client.post("/login", json={"email": "test2@gmail.com", "password": "123456"})
    
    assert response.status_code == 200
    assert "token" in response.json()

def test_login_invalid_credentials():
    # Use invalid credentials for this test
    response = client.post("/login", json={"email": "invalid@example.com", "password": "wrongpassword"})
    assert response.status_code == 400
    assert "Invalid email/password" in response.json()["detail"]

#testig ping
def test_validate_token():
    response = client.post("/login", json={"email": "test2@gmail.com", "password": "123456"})
    token = response.json()["token"]
    # Assuming you have a way to get or mock a valid token
    response = client.post("/ping", headers={"authorization": token})
    # Assuming the successful response returns a user_id
    assert response.status_code == 200


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
    response = client.post("/message", json=message_data)
    assert response.status_code == 200

def test_post_message_invalid_data():
    # Example with missing 'user_uid'
    message_data = {
        "message_content": "Hello, world!",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "timestamp": "2023-11-11T21:09:32.840000+00:00"
    }
    response = client.post("/message", json=message_data)
    assert response.status_code == 422

def test_post_message_firebase_error():
    message_data = {
        "user_uid": "user123",
        "message_content": "Hello, world!",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "timestamp": "2023-11-11T21:09:32.840000+00:00"
    }
    with patch('main.db') as mock_db:
        mock_db.return_value.push.side_effect = Exception("Firebase error")
        response = client.post("/message", json=message_data)
    assert response.status_code == 500
   

# Tests for getUsers endpoint
# -------------------------------------

def test_get_users_success():
    response = client.get("/getUsers")
    assert response.status_code == 200
    # Additional assertions can be added to check the content of the response

def test_get_users_exception_handling():
    # Mock an exception in the database call
    with patch('main.db') as mock_db:
        mock_db.side_effect = Exception("Database error")
        response = client.get("/getUsers")
    assert response.status_code == 500

# Tests for getUser/{user_uid} endpoint
# --------------------------------------

def test_get_user_by_uid_success():
    user_uid = "ots6aMY5FrUogLU0v87X22pINoI3"  # Replace with a valid UID
    response = client.get(f"/getUser/{user_uid}")
    assert response.status_code == 200
    # Further assertions can be added to validate response content

def test_get_user_by_uid_nonexistent():
    user_uid = "nonexistent_uid"
    response = client.get(f"/getUser/{user_uid}")
    assert response.status_code == 500

def test_get_user_by_uid_exception_handling():
    user_uid = "any_uid"
    with patch('main.db') as mock_db:
        mock_db.side_effect = Exception("Database error")
        response = client.get(f"/getUser/{user_uid}")
    assert response.status_code == 500

# Tests for getAllMessages endpoint
# ----------------------------------

def test_get_all_messages_success():
    response = client.get("/getAllMessages")
    assert response.status_code == 200
    # Assertions to check the response content can be added

def test_get_all_messages_exception_handling():
    with patch('main.db') as mock_db:
        mock_db.side_effect = Exception("Database error")
        response = client.get("/getAllMessages")
    assert response.status_code == 500

# Tests for getMessagesFromUser/{userID} endpoint
# ----------------------------------------------

def test_get_messages_from_user_success():
    user_id = "ots6aMY5FrUogLU0v87X22pINoI3"  # Replace with valid user ID
    response = client.get(f"/getMessagesFromUser/{user_id}")
    assert response.status_code == 200
    # Additional assertions for response content

def test_get_messages_from_user_empty():
    user_id = "ots6aMY5FrUogLU0v87X22pINoI3"
    response = client.get(f"/getMessagesFromUser/{user_id}")
    assert response.status_code == 200
    assert response.json() == []

def test_get_messages_from_user_exception_handling():
    user_id = "any_user_id"
    with patch('main.db') as mock_db:
        mock_db.side_effect = Exception("Database error")
        response = client.get(f"/getMessagesFromUser/{user_id}")
    assert response.status_code == 500

# Tests for getMessagesByRadius/{latitude}/{longitude} endpoint
# -------------------------------------------------------------

def test_get_messages_by_radius_success():
    latitude, longitude = 40.7128, -74.0060  # Replace with valid coordinates
    response = client.get(f"/getMessagesByRadius/{latitude}/{longitude}")
    assert response.status_code == 200
    # Further assertions to check response content

def test_get_messages_by_radius_no_messages():
    latitude, longitude = 0, 0  # Coordinates with no messages
    response = client.get(f"/getMessagesByRadius/{latitude}/{longitude}")
    assert response.status_code == 200


# Tests for deleteMessage/{messageID} endpoint
# --------------------------------------------

def test_delete_message_success():
    message_id = "-Nj-JVcymD6uw7oIq9Xg"  # Replace with a valid message ID
    response = client.delete(f"/deleteMessage/{message_id}")
    assert response.status_code == 200
    # Additional assertions can be added to confirm deletion

