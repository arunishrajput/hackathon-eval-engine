"""Integration tests for the submission API endpoints."""
import pytest
from unittest.mock import AsyncMock, patch
from app.models.user import User, UserRole
from app.models.hackathon import Hackathon, HackathonStatus
from app.core.security import hash_password, create_access_token


async def _make_admin(db) -> User:
    user = User(
        email="admin@test.com",
        hashed_password=hash_password("password"),
        role=UserRole.admin,
        full_name="Test Admin",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def _make_participant(db) -> User:
    user = User(
        email="part@test.com",
        hashed_password=hash_password("password"),
        role=UserRole.participant,
        full_name="Test Participant",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def _make_active_hackathon(db, admin_id) -> Hackathon:
    h = Hackathon(
        title="Test Hackathon",
        admin_id=admin_id,
        status=HackathonStatus.active,
    )
    db.add(h)
    await db.flush()
    await db.refresh(h)
    return h


def _auth_headers(user: User) -> dict:
    token = create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_submission_success(client, db):
    """A participant can submit a GitHub URL to an active hackathon."""
    admin = await _make_admin(db)
    participant = await _make_participant(db)
    hackathon = await _make_active_hackathon(db, admin.id)

    with patch("app.api.v1.submissions.enqueue_evaluation", new=AsyncMock()):
        response = await client.post(
            "/api/v1/submissions/",
            json={
                "hackathon_id": str(hackathon.id),
                "repo_url": "https://github.com/tiangolo/fastapi",
            },
            headers=_auth_headers(participant),
        )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["repo_url"] == "https://github.com/tiangolo/fastapi"
    assert data["hackathon_id"] == str(hackathon.id)


@pytest.mark.asyncio
async def test_create_submission_invalid_url(client, db):
    """Non-GitHub URLs are rejected."""
    admin = await _make_admin(db)
    participant = await _make_participant(db)
    hackathon = await _make_active_hackathon(db, admin.id)

    response = await client.post(
        "/api/v1/submissions/",
        json={
            "hackathon_id": str(hackathon.id),
            "repo_url": "https://gitlab.com/some/repo",
        },
        headers=_auth_headers(participant),
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_submission_duplicate(client, db):
    """A participant cannot submit twice to the same hackathon."""
    admin = await _make_admin(db)
    participant = await _make_participant(db)
    hackathon = await _make_active_hackathon(db, admin.id)

    with patch("app.api.v1.submissions.enqueue_evaluation", new=AsyncMock()):
        r1 = await client.post(
            "/api/v1/submissions/",
            json={"hackathon_id": str(hackathon.id), "repo_url": "https://github.com/tiangolo/fastapi"},
            headers=_auth_headers(participant),
        )
        assert r1.status_code == 201

        r2 = await client.post(
            "/api/v1/submissions/",
            json={"hackathon_id": str(hackathon.id), "repo_url": "https://github.com/pallets/flask"},
            headers=_auth_headers(participant),
        )
        assert r2.status_code == 400


@pytest.mark.asyncio
async def test_create_submission_unauthenticated(client, db):
    """Unauthenticated users cannot submit."""
    admin = await _make_admin(db)
    hackathon = await _make_active_hackathon(db, admin.id)

    response = await client.post(
        "/api/v1/submissions/",
        json={"hackathon_id": str(hackathon.id), "repo_url": "https://github.com/tiangolo/fastapi"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_submission_owner(client, db):
    """Submission owner can retrieve their submission."""
    admin = await _make_admin(db)
    participant = await _make_participant(db)
    hackathon = await _make_active_hackathon(db, admin.id)

    with patch("app.api.v1.submissions.enqueue_evaluation", new=AsyncMock()):
        create_resp = await client.post(
            "/api/v1/submissions/",
            json={"hackathon_id": str(hackathon.id), "repo_url": "https://github.com/tiangolo/fastapi"},
            headers=_auth_headers(participant),
        )
    submission_id = create_resp.json()["id"]

    get_resp = await client.get(
        f"/api/v1/submissions/{submission_id}",
        headers=_auth_headers(participant),
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == submission_id


@pytest.mark.asyncio
async def test_get_submission_other_user_forbidden(client, db):
    """A different participant cannot read another's submission."""
    admin = await _make_admin(db)
    participant = await _make_participant(db)
    other = User(
        email="other@test.com",
        hashed_password=hash_password("password"),
        role=UserRole.participant,
    )
    db.add(other)
    await db.flush()
    await db.refresh(other)
    hackathon = await _make_active_hackathon(db, admin.id)

    with patch("app.api.v1.submissions.enqueue_evaluation", new=AsyncMock()):
        create_resp = await client.post(
            "/api/v1/submissions/",
            json={"hackathon_id": str(hackathon.id), "repo_url": "https://github.com/tiangolo/fastapi"},
            headers=_auth_headers(participant),
        )
    submission_id = create_resp.json()["id"]

    get_resp = await client.get(
        f"/api/v1/submissions/{submission_id}",
        headers=_auth_headers(other),
    )
    assert get_resp.status_code == 403


@pytest.mark.asyncio
async def test_list_my_submissions(client, db):
    """Participant can list their own submissions."""
    admin = await _make_admin(db)
    participant = await _make_participant(db)
    hackathon = await _make_active_hackathon(db, admin.id)

    with patch("app.api.v1.submissions.enqueue_evaluation", new=AsyncMock()):
        await client.post(
            "/api/v1/submissions/",
            json={"hackathon_id": str(hackathon.id), "repo_url": "https://github.com/tiangolo/fastapi"},
            headers=_auth_headers(participant),
        )

    list_resp = await client.get("/api/v1/submissions/", headers=_auth_headers(participant))
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1
