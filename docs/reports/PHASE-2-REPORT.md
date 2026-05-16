# Phase 2 Report — Auth + Core API

**Status**: Completed
**Date**: 2026-05-15
**Phase duration**: Day 1–2

---

## Summary

Phase 2 delivered the full authentication system and all core CRUD API endpoints. By the end of Phase 2, participants can register, log in with JWT tokens, and manage hackathon submissions through the REST API. Admins can create hackathons, configure criteria, and view all submissions.

---

## What Was Built

### Authentication System
- **`backend/app/core/security.py`** — JWT access token and refresh token creation/verification using `python-jose`; bcrypt password hashing via `passlib`
- **`backend/app/api/v1/auth.py`** — `POST /register`, `POST /login` (JSON body), `POST /token` (OAuth2 form for Swagger UI), `POST /refresh`, `GET /me`
- **`backend/app/dependencies.py`** — `get_current_user()` dependency extracts and verifies JWT from `Authorization: Bearer` header; `require_admin()` dependency enforces `role == admin`

### Hackathon Management
- **`backend/app/api/v1/hackathons.py`** — full hackathon CRUD plus participant join and criteria management:
  - `POST /hackathons/` — admin creates hackathon with title, description, dates, and JSONB settings
  - `GET /hackathons/` — lists all active hackathons
  - `GET /hackathons/{id}` — hackathon detail with criteria
  - `PATCH /hackathons/{id}` — admin updates hackathon
  - `POST /hackathons/{id}/join` — participant joins a hackathon (duplicate check included)
  - `POST /hackathons/{id}/criteria` — admin adds weighted evaluation criterion linked to an agent_id

### Submission Management
- **`backend/app/api/v1/submissions.py`** — full submission lifecycle:
  - `POST /submissions/` — validates GitHub URL via regex, enforces one-submission-per-hackathon unique constraint, enqueues evaluation job via ARQ
  - `GET /submissions/` — lists current user's submissions
  - `GET /submissions/{id}` — submission detail (owner or admin)
  - `GET /submissions/{id}/status` — SSE stream polling DB every 2 seconds; emits `progress`, `completed`, `error` events
  - `DELETE /submissions/{id}` — withdraw submission (only if pending or failed)

### Evaluation & Rankings API
- **`backend/app/api/v1/evaluations.py`** — `GET /evaluations/{id}` (full report), `GET /evaluations/{id}/agents` (per-agent detail)
- **`backend/app/api/v1/rankings.py`** — `GET /rankings/hackathon/{hackathon_id}` respecting the `show_rankings_before_finalization` setting
- **`backend/app/api/v1/admin.py`** — `POST /admin/hackathons/{id}/finalize`, `GET /admin/hackathons/{id}/submissions`, `GET /admin/users`

### Supporting Infrastructure
- **`backend/app/schemas/`** — Pydantic v2 request/response schemas for all entities
- **`backend/app/core/exceptions.py`** — `NotFoundError`, `ForbiddenError`, `BadRequestError`, `UnauthorizedError` with FastAPI exception handlers returning consistent JSON
- **`backend/app/core/middleware.py`** — `RequestLoggingMiddleware` using structlog for structured request/response logs
- **`backend/app/scripts/seed.py`** — idempotent seed script creating demo admin and participant accounts plus "AI Hackathon 2025" with three weighted criteria

---

## Key Decisions Made

- **Dual login endpoints**: Added both `/login` (JSON body) and `/token` (OAuth2 form) to support both direct API callers and Swagger UI's Authorize button, which requires the OAuth2 form format.
- **GitHub URL regex validation** on submission creation: `^https?://github\.com/[\w\-\.]+/[\w\-\.]+(/.*)?$` — rejects non-GitHub URLs upfront before enqueueing
- **One-submission-per-hackathon** enforced at both database (unique constraint on `hackathon_id + user_id`) and API level (explicit duplicate check with clear error message)
- **SSE polling at 2-second intervals** with 180-iteration maximum (6-minute cap) — balances latency vs. database query load
- **`X-Accel-Buffering: no` header** on SSE responses — prevents Nginx from buffering the event stream
- **Refresh tokens with 7-day expiry**; access tokens expire in 30 minutes to limit exposure window

---

## Known Issues / Technical Debt

- JWT tokens are not blacklisted on logout or password change. **Debt**: implement a Redis-backed token blacklist or reduce access token TTL.
- The `GET /hackathons/` endpoint loads all hackathons without pagination parameters. **Debt**: add `?page=` and `?per_page=` query parameters.
- Rate limiting via `slowapi` is imported but not applied to auth endpoints. **Debt**: add `@limiter.limit("10/minute")` to login and register endpoints.
- The seed script's demo hackathon is hardcoded to start immediately with a 7-day window; should accept a configurable window.

---

## Verification Checklist

- [x] `POST /register` creates user with bcrypt-hashed password; duplicate email returns 400
- [x] `POST /login` returns `access_token` and `refresh_token`; wrong password returns 401
- [x] `GET /me` with valid token returns user profile; expired token returns 401
- [x] `POST /hackathons/` with admin token creates hackathon; participant token returns 403
- [x] `POST /submissions/` with invalid GitHub URL returns 400 with clear error message
- [x] `POST /submissions/` with duplicate submission returns 400 "already submitted"
- [x] `GET /submissions/{id}/status` returns `text/event-stream` content type with `X-Accel-Buffering: no`
- [x] `DELETE /submissions/{id}` on an `evaluating` submission returns 400 with reason
- [x] `GET /admin/users` with participant token returns 403
- [x] Swagger UI at `/api/docs` shows all endpoints with correct schemas
- [x] `make seed` creates admin and participant accounts and the demo hackathon
- [x] Duplicate join attempt returns 409 Conflict
