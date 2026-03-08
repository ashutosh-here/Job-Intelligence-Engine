# Job Intelligence Engine (JIE)

Job Intelligence Engine is a modular SaaS platform for:

- discovering job links from multiple sources
- extracting structured job data
- scoring and ranking jobs semantically
- storing embeddings for similarity search
- enriching companies
- generating recruiter outreach drafts
- exposing analytics and historical intelligence

This repository includes:

- `backend`: FastAPI + SQLAlchemy + Celery + Playwright + pgvector
- `frontend`: Next.js + Tailwind + Recharts dashboard
- `docker-compose.yml`: full stack orchestration

## 1. Architecture

```text
Frontend (Next.js)
  ->
FastAPI API
  ->
Orchestrator
  ->
Source Engine
  ->
Extraction Engine (ATS adapters + heuristic + LLM fallback)
  ->
Semantic Engine
  ->
Vector Engine
  ->
Enrichment Engine
  ->
Scoring Engine
  ->
Outreach Engine
  ->
Analytics Engine
  ->
PostgreSQL (pgvector) + Redis
```

## 2. Core Capabilities Implemented

- multi-source extraction adapters:
  - ATS: Greenhouse, Lever, Ashby, Workable
  - job boards: LinkedIn, Indeed, Naukri
  - generic career pages
- idempotent ingest:
  - unique fingerprint per source/job payload
- auth and tenant isolation:
  - JWT-based auth
  - RBAC roles (`user`, `admin`)
  - tenant scoping across data routes
- anti-bot hardening:
  - per-domain rate limiting
  - persistent browser session state
  - user-agent rotation
  - proxy pool rotation with cooldown/sticky assignment
  - strategy profiles per source (scroll/pagination/delay)
  - challenge solver integration
  - signed challenge solver provider (`signed_http_v1`)
- observability:
  - request telemetry middleware
  - Prometheus metrics endpoint
  - pipeline counters
- CI drift gating:
  - recorded-source contract tests fail when selectors drift

## 3. Prerequisites

- Docker + Docker Compose (recommended)
- or local:
  - Python 3.11
  - Node 20+
  - PostgreSQL 16+ with `pgvector`
  - Redis 7+
  - Playwright Chromium runtime

## 4. Quick Start (Docker)

```bash
docker compose up --build
```

Services:

- Backend API: `http://localhost:8000`
- Frontend: `http://localhost:3000`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

## 5. Local Setup (Without Docker)

### Backend

```bash
cd backend
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows (PowerShell):
# .\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
playwright install chromium
python -m app.bootstrap
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Celery Worker + Beat

```bash
cd backend
celery -A worker.celery_app worker -l info
celery -A worker.celery_app beat -l info
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 6. Configuration

Copy `.env.example` to `.env` and update values.

### Required baseline

- `DATABASE_URL`
- `REDIS_URL`
- `APP_SECRET_KEY`

### Auth and tokens

- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `JWT_ALGORITHM`

### Embedding and LLM

- `LOCAL_LLM_ENDPOINT`
- `LOCAL_LLM_MODEL`
- `EMBEDDING_MODEL` (default baked in code)

### Anti-bot and crawling controls

- `SOURCE_RATE_LIMIT_PER_MINUTE`
- `SOURCE_MAX_PAGES`
- `SOURCE_MAX_SCROLLS`
- `SOURCE_ROTATE_USER_AGENTS`
- `SOURCE_BLOCK_RESOURCE_TYPES` (comma-separated, example: `image,font,media`)

### Proxy pool

- `SOURCE_ENABLE_PROXY_ROTATION=true|false`
- `SOURCE_PROXIES`
  - format examples:
    - `linkedin|indeed=http://user:pass@proxy1:8080`
    - `naukri=http://proxy2:8080`
    - `http://proxy3:8080`
- `SOURCE_PROXY_MAX_FAILURES`
- `SOURCE_PROXY_COOLDOWN_SECONDS`
- `SOURCE_PROXY_STICKY_MINUTES`

### Challenge solver

- `SOURCE_CHALLENGE_SOLVER_ENABLED=true|false`
- `SOURCE_CHALLENGE_SOLVER_PROVIDER=signed_http_v1|unsigned_http_v1`
- `SOURCE_CHALLENGE_SOLVER_ENDPOINT`
- `SOURCE_CHALLENGE_SOLVER_API_KEY`
- `SOURCE_CHALLENGE_SOLVER_SIGNING_SECRET` (required for `signed_http_v1`)
- `SOURCE_CHALLENGE_RESPONSE_MAX_SKEW_SECONDS`
- `SOURCE_CHALLENGE_RETRY_LIMIT`

### Observability

- `METRICS_ENABLED=true|false`

## 7. Migrations

Alembic is the source of truth.

```bash
cd backend
alembic upgrade head
```

Initial migration file:

- `backend/alembic/versions/20260308_0001_initial.py`

## 8. How To Use The App (End-to-End)

All endpoints below use API base `http://localhost:8000`.

### 8.1 Register user

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email":"user@example.com",
    "password":"StrongPass123!",
    "role":"user"
  }'
```

### 8.2 Login and capture token

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"StrongPass123!"}'
```

Take `access_token` from response.

### 8.3 Create source

```bash
curl -X POST http://localhost:8000/sources \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "url":"https://boards.greenhouse.io/acme",
    "type":"greenhouse",
    "refresh_interval":3600,
    "keywords":["python","backend"],
    "custom_selectors":{"job_links":"a.opening"}
  }'
```

### 8.4 Run ingestion pipeline

Async queue trigger:

```bash
curl -X POST "http://localhost:8000/sources/<SOURCE_ID>/run?user_profile=Backend%20Python%20AWS%20Kubernetes" \
  -H "Authorization: Bearer <TOKEN>"
```

Sync trigger:

```bash
curl -X POST "http://localhost:8000/orchestrator/run/<SOURCE_ID>?user_profile=Backend%20Python%20AWS%20Kubernetes" \
  -H "Authorization: Bearer <TOKEN>"
```

### 8.5 Query jobs

```bash
curl -X GET "http://localhost:8000/jobs?limit=20&min_score=0.4" \
  -H "Authorization: Bearer <TOKEN>"
```

### 8.6 Similar jobs

```bash
curl -X GET "http://localhost:8000/jobs/similar/<JOB_ID>?limit=10" \
  -H "Authorization: Bearer <TOKEN>"
```

### 8.7 Outreach draft

```bash
curl -X POST http://localhost:8000/outreach/draft \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id":123,
    "user_profile":"7 years backend engineering, Python, distributed systems, AWS"
  }'
```

### 8.8 Analytics

```bash
curl -X GET http://localhost:8000/analytics/overview \
  -H "Authorization: Bearer <TOKEN>"
```

```bash
curl -X GET "http://localhost:8000/analytics/trends?days=30" \
  -H "Authorization: Bearer <TOKEN>"
```

## 9. Frontend Usage

Open:

- `http://localhost:3000`

The dashboard fetches:

- `/analytics/overview`
- `/analytics/trends`
- `/jobs`

Set frontend API target with:

- `NEXT_PUBLIC_API_BASE`

## 10. Signed Challenge Solver Protocol (`signed_http_v1`)

JIE request headers:

- `X-JIE-Timestamp`: unix seconds
- `X-JIE-Nonce`: random nonce
- `X-JIE-Signature`: `HMAC_SHA256(secret, "<timestamp>.<nonce>.<canonical_json_payload>")`

Solver response requirements:

- response body must be JSON
- response headers must include:
  - `X-JIE-Timestamp`
  - `X-JIE-Nonce`
  - `X-JIE-Signature` over response JSON with same algorithm

Validation behavior:

- bad/missing signature: rejected
- timestamp outside skew window: rejected
- reused nonce: rejected (replay protection)

Optional solver response body:

```json
{
  "solved": true,
  "reason": "challenge bypassed",
  "actions": [
    {"type":"click","selector":"#verify"},
    {"type":"wait","milliseconds":1500}
  ]
}
```

## 11. Observability

- Health:
  - `GET /health`
- Metrics:
  - `GET /metrics`

Prometheus metrics include request counters, latency histograms, and pipeline extraction/failure counters.

## 12. Testing

Run all tests:

```bash
cd backend
pytest -q
```

Run selector contract tests only:

```bash
cd backend
pytest -q -m contract tests/test_source_contracts.py
```

Contract tests use recorded HTML fixtures and fail on selector drift.

## 13. CI

Workflow file:

- `.github/workflows/backend-ci.yml`

Gates include:

- compile check
- full backend tests
- explicit contract marker run

If selector contracts fail, CI fails and merge should be blocked.

## 14. Security and Multi-Tenancy Notes

- All non-health endpoints are protected by JWT.
- Tenant data is scoped to `current_user.id` unless role is `admin`.
- Passwords are hashed.
- Signed solver mode should use HTTPS endpoint in production.
- Set strong random `APP_SECRET_KEY` in production.

## 15. Troubleshooting

- `Source already exists for this user`:
  - same user and URL already present; use existing source record.
- No jobs extracted:
  - run contract tests and inspect selector drift.
  - check anti-bot settings/proxy quality.
- Frequent bot-wall failures:
  - enable proxy rotation, increase delays, wire challenge solver.
- Missing embeddings similarity results:
  - ensure ingestion pipeline completed and embeddings were stored.
- API unauthorized:
  - verify Bearer token and expiration.

## 16. Production Checklist

- set strong secrets (`APP_SECRET_KEY`, solver signing secret)
- enable HTTPS and secure ingress
- run Alembic migrations in deploy pipeline
- configure external persistent storage for artifacts/screenshots
- set up Prometheus/Grafana dashboards from `/metrics`
- configure worker autoscaling and queue monitoring
- enforce CI required checks including contract tests
