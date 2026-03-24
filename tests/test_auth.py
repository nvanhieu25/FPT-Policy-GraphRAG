"""
tests/test_auth.py

Tests for authentication endpoints.
"""
import pytest


@pytest.mark.asyncio
async def test_register_success(client):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "test@fpt.com",
        "username": "testuser",
        "password": "securepass123",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "test@fpt.com"
    assert data["username"] == "testuser"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    payload = {"email": "dup@fpt.com", "username": "dupuser1", "password": "pass"}
    await client.post("/api/v1/auth/register", json=payload)
    resp = await client.post("/api/v1/auth/register", json={
        "email": "dup@fpt.com", "username": "dupuser2", "password": "pass"
    })
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client):
    await client.post("/api/v1/auth/register", json={
        "email": "login@fpt.com", "username": "loginuser", "password": "mypassword"
    })
    resp = await client.post("/api/v1/auth/token", data={
        "username": "login@fpt.com", "password": "mypassword"
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/api/v1/auth/register", json={
        "email": "wrong@fpt.com", "username": "wronguser", "password": "correct"
    })
    resp = await client.post("/api/v1/auth/token", data={
        "username": "wrong@fpt.com", "password": "incorrect"
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated(client):
    await client.post("/api/v1/auth/register", json={
        "email": "me@fpt.com", "username": "meuser", "password": "pass123"
    })
    token_resp = await client.post("/api/v1/auth/token", data={
        "username": "me@fpt.com", "password": "pass123"
    })
    token = token_resp.json()["access_token"]
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "meuser"


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401
