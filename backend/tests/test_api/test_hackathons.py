"""
Tests for /api/v1/hackathons endpoints.

Covers:
  - GET  /           — lists only non-draft hackathons
  - POST /           — admin creates; participant cannot
  - GET  /{id}       — fetch by id
  - POST /{id}/join  — join an active hackathon; duplicate join rejected
"""

import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

from app.models.user import User, UserRole
from app.models.hackathon import Hackathon, HackathonStatus


# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------

async def _register_and_login(client: AsyncClient, email: str, password: str = "testpass1") -> str:
    """Register a participant user and return an access token."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Test User"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def _make_admin(db: AsyncSession, email: str) -> None:
    """Promote a registered user to the admin role."""
    await db.execute(
        update(User).where(User.email == email).values(role=UserRole.admin)
    )
    await db.flush()


@pytest.fixture
async def participant_token(client: AsyncClient) -> str:
    return await _register_and_login(client, "participant@hacktest.com")


@pytest.fixture
async def admin_token(client: AsyncClient, db: AsyncSession) -> str:
    token = await _register_and_login(client, "admin@hacktest.com", "adminpass1")
    await _make_admin(db, "admin@hacktest.com")
    # Re-login to pick up the new role claim (JWT is still valid; role is
    # checked from DB at request time, not encoded in the token).
    return token


@pytest.fixture
async def active_hackathon(client: AsyncClient, db: AsyncSession, admin_token: str) -> dict:
    """Create and activate a hackathon, returning its JSON response."""
    create_resp = await client.post(
        "/api/v1/hackathons/",
        json={"title": "Test Hackathon", "description": "For automated tests"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_resp.status_code == 201
    hackathon = create_resp.json()

    # Transition draft → active
    patch_resp = await client.patch(
        f"/api/v1/hackathons/{hackathon['id']}/status",
        params={"new_status": "active"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert patch_resp.status_code == 200
    return patch_resp.json()


# ---------------------------------------------------------------------------
# GET /api/v1/hackathons/
# ---------------------------------------------------------------------------

async def test_list_hackathons_returns_only_non_draft(
    client: AsyncClient, db: AsyncSession, admin_token: str
):
    """Draft hackathons must not appear in the public listing."""
    # Create a draft hackathon (default status)
    draft_resp = await client.post(
        "/api/v1/hackathons/",
        json={"title": "Draft Hackathon"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert draft_resp.status_code == 201
    draft_id = draft_resp.json()["id"]

    # Create and activate another
    active_resp = await client.post(
        "/api/v1/hackathons/",
        json={"title": "Active Hackathon"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert active_resp.status_code == 201
    active_id = active_resp.json()["id"]
    await client.patch(
        f"/api/v1/hackathons/{active_id}/status",
        params={"new_status": "active"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    list_resp = await client.get("/api/v1/hackathons/")
    assert list_resp.status_code == 200
    ids = [h["id"] for h in list_resp.json()]

    assert active_id in ids
    assert draft_id not in ids


async def test_list_hackathons_returns_200_empty(client: AsyncClient):
    """With no hackathons at all the endpoint returns 200 with an empty list."""
    resp = await client.get("/api/v1/hackathons/")
    assert resp.status_code == 200
    assert resp.json() == []


# ---------------------------------------------------------------------------
# POST /api/v1/hackathons/
# ---------------------------------------------------------------------------

async def test_admin_can_create_hackathon(client: AsyncClient, admin_token: str):
    """An admin user should be able to create a hackathon (201)."""
    resp = await client.post(
        "/api/v1/hackathons/",
        json={
            "title": "My Hackathon",
            "description": "A test hackathon",
            "max_submissions": 50,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "My Hackathon"
    assert body["status"] == "draft"
    assert body["max_submissions"] == 50
    assert "id" in body


async def test_admin_can_create_hackathon_with_criteria(
    client: AsyncClient, admin_token: str
):
    """Criteria can be included inline when creating a hackathon."""
    resp = await client.post(
        "/api/v1/hackathons/",
        json={
            "title": "Hackathon With Criteria",
            "criteria": [
                {"name": "Code Quality", "weight": 0.5, "agent_id": "code_quality"},
                {"name": "Innovation", "weight": 0.5, "agent_id": "innovation"},
            ],
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert len(body["criteria"]) == 2
    criterion_names = {c["name"] for c in body["criteria"]}
    assert "Code Quality" in criterion_names
    assert "Innovation" in criterion_names


async def test_participant_cannot_create_hackathon(
    client: AsyncClient, participant_token: str
):
    """A participant user must receive 403 when trying to create a hackathon."""
    resp = await client.post(
        "/api/v1/hackathons/",
        json={"title": "Sneaky Hackathon"},
        headers={"Authorization": f"Bearer {participant_token}"},
    )
    assert resp.status_code == 403


async def test_unauthenticated_cannot_create_hackathon(client: AsyncClient):
    """Creating a hackathon without a token must return 401."""
    resp = await client.post("/api/v1/hackathons/", json={"title": "Anon Hackathon"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/v1/hackathons/{id}
# ---------------------------------------------------------------------------

async def test_get_hackathon_by_id(
    client: AsyncClient, admin_token: str, active_hackathon: dict
):
    """Fetching a hackathon by its ID returns the correct resource."""
    hackathon_id = active_hackathon["id"]
    resp = await client.get(f"/api/v1/hackathons/{hackathon_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == hackathon_id
    assert body["title"] == active_hackathon["title"]


async def test_get_hackathon_nonexistent_returns_404(client: AsyncClient):
    """Requesting a non-existent hackathon ID should return 404."""
    resp = await client.get(f"/api/v1/hackathons/{uuid.uuid4()}")
    assert resp.status_code == 404


async def test_get_draft_hackathon_returns_it_directly(
    client: AsyncClient, admin_token: str
):
    """The detail endpoint returns draft hackathons (unlike the list endpoint)."""
    create_resp = await client.post(
        "/api/v1/hackathons/",
        json={"title": "Draft Detail"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    draft_id = create_resp.json()["id"]
    resp = await client.get(f"/api/v1/hackathons/{draft_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "draft"


# ---------------------------------------------------------------------------
# POST /api/v1/hackathons/{id}/join
# ---------------------------------------------------------------------------

async def test_participant_can_join_active_hackathon(
    client: AsyncClient,
    participant_token: str,
    active_hackathon: dict,
):
    """A participant should be able to join an active hackathon (201)."""
    hackathon_id = active_hackathon["id"]
    resp = await client.post(
        f"/api/v1/hackathons/{hackathon_id}/join",
        headers={"Authorization": f"Bearer {participant_token}"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "message" in body
    assert body["hackathon_id"] == hackathon_id


async def test_duplicate_join_returns_409(
    client: AsyncClient,
    participant_token: str,
    active_hackathon: dict,
):
    """Joining the same hackathon twice should return 409 Conflict."""
    hackathon_id = active_hackathon["id"]
    headers = {"Authorization": f"Bearer {participant_token}"}

    first = await client.post(f"/api/v1/hackathons/{hackathon_id}/join", headers=headers)
    assert first.status_code == 201

    second = await client.post(f"/api/v1/hackathons/{hackathon_id}/join", headers=headers)
    assert second.status_code == 409


async def test_join_draft_hackathon_returns_400(
    client: AsyncClient,
    participant_token: str,
    admin_token: str,
):
    """Attempting to join a draft (non-active) hackathon should return 400."""
    create_resp = await client.post(
        "/api/v1/hackathons/",
        json={"title": "Draft Join Test"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    draft_id = create_resp.json()["id"]

    resp = await client.post(
        f"/api/v1/hackathons/{draft_id}/join",
        headers={"Authorization": f"Bearer {participant_token}"},
    )
    assert resp.status_code == 400


async def test_join_nonexistent_hackathon_returns_404(
    client: AsyncClient, participant_token: str
):
    """Joining a hackathon with a random UUID should return 404."""
    resp = await client.post(
        f"/api/v1/hackathons/{uuid.uuid4()}/join",
        headers={"Authorization": f"Bearer {participant_token}"},
    )
    assert resp.status_code == 404


async def test_join_requires_authentication(
    client: AsyncClient, active_hackathon: dict
):
    """Joining without a token must return 401."""
    hackathon_id = active_hackathon["id"]
    resp = await client.post(f"/api/v1/hackathons/{hackathon_id}/join")
    assert resp.status_code == 401
