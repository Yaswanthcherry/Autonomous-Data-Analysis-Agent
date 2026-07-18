"""
Dataset endpoint tests — upload, list, delete
"""
import io
import pytest


async def _register_and_login(client) -> str:
    """Helper: register + login, return Bearer token."""
    await client.post("/api/v1/auth/register", json={
        "email": "ds_user@example.com",
        "full_name": "DS User",
        "password": "TestPass123!",
    })
    res = await client.post("/api/v1/auth/login", json={
        "email": "ds_user@example.com",
        "password": "TestPass123!",
    })
    return res.json()["access_token"]


@pytest.mark.asyncio
async def test_upload_csv(client):
    token = await _register_and_login(client)
    csv_content = b"name,age,salary\nAlice,30,70000\nBob,25,50000\n"
    response = await client.post(
        "/api/v1/datasets/upload",
        files={"file": ("test.csv", io.BytesIO(csv_content), "text/csv")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["file_type"] == "csv"
    assert "id" in data


@pytest.mark.asyncio
async def test_upload_invalid_type(client):
    token = await _register_and_login(client)
    response = await client.post(
        "/api/v1/datasets/upload",
        files={"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_datasets(client):
    token = await _register_and_login(client)
    response = await client.get(
        "/api/v1/datasets/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_unauthenticated_upload(client):
    csv_content = b"a,b\n1,2\n"
    response = await client.post(
        "/api/v1/datasets/upload",
        files={"file": ("test.csv", io.BytesIO(csv_content), "text/csv")},
    )
    assert response.status_code == 403
