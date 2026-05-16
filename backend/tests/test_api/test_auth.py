"""
Tests for /api/v1/auth endpoints.

Covers:
  - POST /register  — happy path and duplicate-email conflict
  - POST /login     — valid credentials and wrong password
  - GET  /me        — authenticated access and missing token
"""

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

async def test_register_creates_user(client: AsyncClient):
    """Successful registration returns 201 with the new user's data."""
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "securepass1",
            "full_name": "New User",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "newuser@example.com"
    assert body["full_name"] == "New User"
    assert "id" in body
    # Password must never be echoed back
    assert "password" not in body
    assert "hashed_password" not in body


async def test_register_returns_role_participant_by_default(client: AsyncClient):
    """Newly registered users are assigned the 'participant' role."""
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "role@example.com", "password": "securepass1"},
    )
    assert resp.status_code == 201
    assert resp.json()["role"] == "participant"


async def test_register_duplicate_email_returns_409(client: AsyncClient):
    """Registering the same email twice should return 409 Conflict."""
    payload = {"email": "dup@example.com", "password": "securepass1"}
    first = await client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201

    second = await client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409
    assert "already registered" in second.json()["detail"].lower()


async def test_register_missing_email_returns_422(client: AsyncClient):
    """Omitting the email field should fail validation with 422."""
    resp = await client.post(
        "/api/v1/auth/register", json={"password": "securepass1"}
    )
    assert resp.status_code == 422


async def test_register_short_password_returns_422(client: AsyncClient):
    """Password shorter than 8 characters should fail Pydantic validation."""
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "short@example.com", "password": "abc"},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@pytest.fixture
async def registered_user(client: AsyncClient):
    """Helper: register a user and return the credentials."""
    creds = {"email": "login_test@example.com", "password": "loginpass1"}
    resp = await client.post(
        "/api/v1/auth/register",
        json={**creds, "full_name": "Login Tester"},
    )
    assert resp.status_code == 201
    return creds, resp.json()


async def test_login_valid_credentials_returns_tokens(
    client: AsyncClient, registered_user
):
    """Correct email/password returns both access and refresh tokens plus user."""
    creds, _ = registered_user
    resp = await client.post("/api/v1/auth/login", json=creds)
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == creds["email"]


async def test_login_wrong_password_returns_401(
    client: AsyncClient, registered_user
):
    """Wrong password should return 401 Unauthorized."""
    creds, _ = registered_user
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": creds["email"], "password": "wrongpassword"},
    )
    assert resp.status_code == 401


async def test_login_nonexistent_email_returns_401(client: AsyncClient):
    """Login with an email that was never registered returns 401."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@example.com", "password": "doesntmatter"},
    )
    assert resp.status_code == 401


async def test_login_returns_valid_jwt(client: AsyncClient, registered_user):
    """The returned access_token should be a non-empty string."""
    creds, _ = registered_user
    resp = await client.post("/api/v1/auth/login", json=creds)
    token = resp.json()["access_token"]
    assert isinstance(token, str)
    assert len(token) > 20
    # JWT format: three base64 segments separated by dots
    assert token.count(".") == 2


# ---------------------------------------------------------------------------
# /me endpoint
# ---------------------------------------------------------------------------

async def test_get_me_with_valid_token(client: AsyncClient, registered_user):
    """Authenticated GET /me should return the current user's profile."""
    creds, user_data = registered_user
    login = await client.post("/api/v1/auth/login", json=creds)
    token = login.json()["access_token"]

    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == creds["email"]
    assert body["id"] == user_data["id"]


async def test_get_me_without_token_returns_401(client: AsyncClient):
    """Unauthenticated request to /me must return 401."""
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_get_me_with_invalid_token_returns_401(client: AsyncClient):
    """A tampered / invalid Bearer token must be rejected."""
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not.a.valid.token"},
    )
    assert resp.status_code == 401
