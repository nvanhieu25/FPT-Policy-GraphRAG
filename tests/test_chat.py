"""
tests/test_chat.py

Tests for chat endpoint with mocked pipeline.
"""
import pytest
from unittest.mock import patch, AsyncMock


async def _register_and_login(client, email, username):
    await client.post("/api/v1/auth/register", json={
        "email": email, "username": username, "password": "pass123"
    })
    resp = await client.post("/api/v1/auth/token", data={
        "username": email, "password": "pass123"
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_chat_unauthenticated(client):
    resp = await client.post("/api/v1/chat", json={"session_id": "s1", "query": "hello"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_chat_authenticated(client):
    headers = await _register_and_login(client, "chat@fpt.com", "chatuser")
    with patch("app.api.routes.message.run_query", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = "mocked answer"
        resp = await client.post("/api/v1/chat",
            json={"session_id": "sess-001", "query": "What is the leave policy?"},
            headers=headers,
        )
    assert resp.status_code == 200
    assert resp.json()["answer"] == "mocked answer"


@pytest.mark.asyncio
async def test_get_conversations_scoped(client):
    headers_a = await _register_and_login(client, "usera@fpt.com", "usera")
    headers_b = await _register_and_login(client, "userb@fpt.com", "userb")

    with patch("app.api.routes.message.run_query", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = "answer"
        await client.post("/api/v1/chat",
            json={"session_id": "sess-a", "query": "q"},
            headers=headers_a,
        )

    resp_a = await client.get("/api/v1/conversations", headers=headers_a)
    resp_b = await client.get("/api/v1/conversations", headers=headers_b)

    assert resp_a.status_code == 200
    assert resp_b.status_code == 200
    ids_a = [c["id"] for c in resp_a.json()["conversations"]]
    ids_b = [c["id"] for c in resp_b.json()["conversations"]]
    assert "sess-a" in ids_a
    assert "sess-a" not in ids_b
