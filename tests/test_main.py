import uuid
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "AI Document Intelligence API is running"

def test_documents_requires_authentication():
    response = client.get("/documents")

    assert response.status_code == 401

def test_invalid_document_id():
    response = client.get("/documents/999999")

    assert response.status_code == 401

def test_register_short_password():
    response = client.post(
        "/register",
        json={
            "username": "testuser123",
            "email": "test123@example.com",
            "password": "123",
        },
    )

    assert response.status_code == 400

def test_invalid_login():
    response = client.post(
        "/login",
        json={
            "username": "nonexistent_user",
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401

def test_register_success():
    response = client.post(
        "/register",
        json={
            "username": f"pytest_{uuid.uuid4().hex[:8]}",
            "email": f"pytest_{uuid.uuid4().hex[:8]}@example.com",       
            "password": "securepass123",
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == "User registered successfully"

def test_login_success():
    response = client.post(
        "/login",
        json={
            "username": "pytest_user2026",
            "password": "securepass123",
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Login successful"
    assert "access_token" in response.json()    

def test_authenticated_documents_access():
    login_response = client.post(
        "/login",
        json={
            "username": "pytest_user2026",
            "password": "securepass123",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.get(
        "/documents",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200    