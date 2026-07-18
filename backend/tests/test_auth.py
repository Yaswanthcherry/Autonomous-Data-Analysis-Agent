import pytest


@pytest.mark.asyncio
async def test_register(client):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "TestPass123!",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_register_duplicate(client):
    await client.post("/api/v1/auth/register", json={
        "email": "dup@example.com",
        "full_name": "Dup User",
        "password": "TestPass123!",
    })
    resp = await client.post("/api/v1/auth/register", json={
        "email": "dup@example.com",
        "full_name": "Dup User",
        "password": "TestPass123!",
    })
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_login(client):
    await client.post("/api/v1/auth/register", json={
        "email": "login@example.com",
        "full_name": "Login User",
        "password": "TestPass123!",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "login@example.com",
        "password": "TestPass123!",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    resp = await client.post("/api/v1/auth/login", json={
        "email": "login@example.com",
        "password": "WrongPassword",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
