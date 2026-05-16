# Phase 7 Report — Frontend

**Status**: Completed
**Date**: 2026-05-15
**Phase duration**: Day 6–7

---

## Summary

Phase 7 built the complete Next.js 14 frontend: all admin and participant pages, reusable evaluation components, the SSE hook for real-time progress, the Recharts score radar, and the RAG mentor chat UI. By the end of Phase 7, the full user journey from registration through evaluation result viewing and mentor chatbot interaction was functional.

---

## What Was Built

### Application Structure
- **Next.js 14 App Router** with TypeScript, Tailwind CSS, and Radix UI primitives
- **`frontend/src/app/layout.tsx`** — root layout with Zustand auth provider and toast notifications
- **`frontend/src/lib/api.ts`** — typed API client using `axios` with JWT injection via request interceptors
- **`frontend/src/lib/types.ts`** — TypeScript type definitions for all API response shapes
- **`frontend/src/lib/auth.ts`** — token storage utilities (localStorage-based)
- **`frontend/src/store/auth.ts`** — Zustand auth store with `user`, `accessToken`, `role`; persisted to localStorage

### Pages — Auth
- **`/` (Landing)** — hero section, feature grid, call-to-action links
- **`/auth/login`** — JSON body login; inline error display; redirects to role-appropriate dashboard
- **`/auth/register`** — creates participant account; redirects to participant portal

### Pages — Admin
- **`/admin`** — hackathon table with participant count, submission count, status badge, and New Hackathon button
- **`/admin/hackathons/new`** — hackathon creation form with title, description, start/end date, and settings
- **`/admin/hackathons/[id]`** — hackathon detail with status transition buttons and submission status table
- **`/admin/hackathons/[id]/criteria`** — inline weight editor with real-time sum validation; save disabled when weights don't sum to 1.0
- **`/admin/hackathons/[id]/submissions`** — all submissions with evaluation status and agent result preview
- **`/admin/hackathons/[id]/rankings`** — finalized rankings table; Finalize Hackathon button

### Pages — Participant
- **`/participant`** — dashboard summary cards (active hackathons, submitted count, evaluations completed)
- **`/participant/hackathons`** — hackathon listing with state-aware action buttons (Join / Submit / View)
- **`/participant/submit/[hackathonId]`** — GitHub URL input form with client-side regex validation; submit button disabled after first click to prevent double-submission
- **`/participant/evaluation/[submissionId]`** — SSE-powered progress stream → score radar chart → report viewer; fetches evaluation after stream completes
- **`/participant/leaderboard/[hackathonId]`** — leaderboard table with current user row highlighted, trophy icons for top 3, percentile badge column
- **`/participant/mentor/[submissionId]`** — RAG mentor chat with starter question chips, message history, and retrieved chunk citations

### Components
- **`ProgressStream`** — animated stage timeline (Queued → Cloning → Analyzing → Evaluating → Complete) consuming the `useEvaluationStream` hook
- **`ScoreRadarChart`** — Recharts `RadarChart` showing per-agent scores; reference lines at 5.0 and 7.5; responsive container
- **`AgentResultCard`** — expandable card with agent name, score badge, confidence, reasoning text, strengths list, weaknesses list
- **`EvidenceList`** — renders evidence items with file path and observation text
- **`ReportViewer`** — Radix UI `Tabs` component with Summary / Agents / Raw JSON tabs
- **`ChatInterface`** — message list with role-based alignment; auto-scroll to latest message; retrieved chunk citation display
- **`Navbar`** — role-aware navigation links (admin tabs hidden for participants); logout clears Zustand store
- **`Sidebar`** — collapsible admin navigation sidebar
- **`HackathonCard`** — status badge, date range, participant count, state-aware action button
- **`LeaderboardTable`** — sortable table with rank, team name, score, percentile; highlights current user's row

### Hooks
- **`frontend/src/hooks/useEvaluationStream.ts`** — `useEvaluationStream(submissionId, onComplete)`: wraps `EventSource` in a `useEffect`; builds `EvaluationStageInfo[]` array from SSE events; dispatches to local state; calls `onComplete(evaluation)` when stream signals `completed`; closes the `EventSource` on unmount
- **`frontend/src/hooks/useAuth.ts`** — reads from Zustand store; provides `user`, `isAdmin`, `isLoading` derived state

---

## Key Decisions Made

- **Zustand for auth state** — Redux was considered but Zustand's minimal boilerplate and built-in `persist` middleware made it the clear choice for the project scale; token and user persisted to localStorage for page reload survival
- **SSE via `EventSource` API** — not WebSockets; the evaluation stream is unidirectional (server → client); `EventSource` reconnects automatically and works through standard HTTP proxies and Nginx; no additional library needed
- **Axios with request interceptors** for JWT injection — cleaner than adding `Authorization` headers to every fetch call; interceptor reads token from localStorage/Zustand store
- **Radix UI primitives** (Dialog, Tabs, DropdownMenu, Toast) over a full component library — provides accessible, unstyled primitives that integrate cleanly with Tailwind CSS without style conflicts
- **Recharts `RadarChart`** for score visualization — shows multi-axis agent scores in a format immediately readable by technical judges; reference lines at 5.0 (below average) and 7.5 (above average) provide calibration anchors

---

## Known Issues / Technical Debt

- **Plain `fetch`/`useEffect` for data fetching** — no caching, revalidation, or deduplication. **Debt**: migrate to SWR or React Query for improved developer experience and automatic cache management.
- **No optimistic UI updates** — form submissions wait for server response before updating the UI, creating perceived latency on slow connections. **Debt**: add optimistic updates for join hackathon and withdraw submission actions.
- **Mentor chat not token-streamed** — the `ChatInterface` has a `streaming` prop but token-by-token SSE forwarding from the backend is not yet implemented. Full responses appear after a 10–30 second wait.
- **Admin criteria weight validation is client-side only** — the server also validates but the client-side validation message ("weights must sum to 1.0") improves UX. **Debt**: add server-side formatted error to complement client validation.

---

## Verification Checklist

- [x] Landing page renders without errors at `http://localhost`
- [x] Login with admin credentials redirects to `/admin`; login with participant credentials redirects to `/participant`
- [x] `useEvaluationStream` hook receives SSE events and advances stage indicators correctly
- [x] `ScoreRadarChart` renders with three agent score axes when evaluation data is available
- [x] Submit form client-side regex rejects `https://gitlab.com/...` URL before API call
- [x] Submit button correctly disabled after first click (prevents double-submission)
- [x] Admin finalize button appears on hackathon detail page; triggers `POST /admin/hackathons/{id}/finalize`
- [x] Leaderboard highlights current user's row
- [x] Mentor chat `POST /chat/sessions/{id}/messages` returns response and displays it in the chat list
- [x] Logout clears Zustand store and localStorage token; redirects to login
- [x] `npm run lint` exits 0 (no ESLint errors in frontend code)
