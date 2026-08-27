"""Backend test suite for Haven Pet API endpoints."""

import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    res = await client.get("/")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_auth_flow(client):
    # 1. Signup
    signup_payload = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "password123",
    }
    res = await client.post("/api/v1/auth/signup", json=signup_payload)
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data

    access_token = data["access_token"]
    refresh_token = data["refresh_token"]

    # 2. Get current user profile
    headers = {"Authorization": f"Bearer {access_token}"}
    res = await client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == 200
    assert res.json()["email"] == "test@example.com"

    # 3. Login
    login_payload = {"email": "test@example.com", "password": "password123"}
    res = await client.post("/api/v1/auth/login", json=login_payload)
    assert res.status_code == 200

    # 4. Refresh token
    res = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert res.status_code == 200
    assert "access_token" in res.json()


@pytest.mark.asyncio
async def test_pet_crud_flow(client):
    # Register user
    signup_res = await client.post(
        "/api/v1/auth/signup",
        json={"name": "Owner", "email": "owner@example.com", "password": "password123"},
    )
    headers = {"Authorization": f"Bearer {signup_res.json()['access_token']}"}

    # Create Pet
    pet_payload = {
        "name": "Max",
        "species": "dog",
        "breed": "Golden Retriever",
        "weight": 25.0,
        "gender": "male",
    }
    res = await client.post("/api/v1/pets", json=pet_payload, headers=headers)
    assert res.status_code == 201
    pet = res.json()
    assert pet["name"] == "Max"
    pet_id = pet["id"]

    # List Pets
    res = await client.get("/api/v1/pets", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) == 1

    # Get Single Pet
    res = await client.get(f"/api/v1/pets/{pet_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["id"] == pet_id

    # Update Pet
    res = await client.put(f"/api/v1/pets/{pet_id}", json={"weight": 26.5}, headers=headers)
    assert res.status_code == 200
    assert res.json()["weight"] == 26.5

    # Add Behavior Log
    log_payload = {"category": "eating", "value": "2 cups", "notes": "Good appetite"}
    res = await client.post(f"/api/v1/pets/{pet_id}/behavior-logs", json=log_payload, headers=headers)
    assert res.status_code == 201
    assert res.json()["category"] == "eating"

    # Query Behavior Logs
    res = await client.get(f"/api/v1/pets/{pet_id}/behavior-logs", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) == 1

    # AI Chat Endpoint Test
    chat_payload = {"pet_id": pet_id, "message": "What diet is best for Max?"}
    res = await client.post("/api/v1/chat", json=chat_payload, headers=headers)
    assert res.status_code == 200
    assert "reply" in res.json()
    assert "agent_used" in res.json()

    # ML Image Recognition Endpoint Test
    files = {"file": ("test.jpg", b"fake_image_bytes", "image/jpeg")}
    res = await client.post("/api/v1/ml/recognize", files=files, headers=headers)
    assert res.status_code == 200
    assert res.json()["species"] == "dog"

    # Delete Pet
    res = await client.delete(f"/api/v1/pets/{pet_id}", headers=headers)
    assert res.status_code == 204
