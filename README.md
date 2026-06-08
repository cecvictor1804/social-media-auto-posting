# Social Media Auto-Posting Agent

Schedule and auto-publish content across **Facebook (Pages)**, **LinkedIn**, and
**Threads**. Draft with AI (Claude / OpenAI / Gemini — selectable per draft),
review and edit, schedule, and a background worker publishes each post at the
right time with per-platform status tracking.

## How it works

Two processes share one database:

- **Web app** — a **FastAPI JSON API** plus a **React + TypeScript SPA**
  (Vite, Tailwind, shadcn/ui, light/dark) for compose, AI-draft, review/approve,
  schedule, queue, calendar, and connected-account management. In production
  FastAPI serves the compiled SPA (`frontend/dist`) at `/`.
- **Scheduler worker** (APScheduler) — every 60s it finds approved posts whose
  time has arrived and publishes them to each platform, retrying transient
  failures and refreshing expiring OAuth tokens.

```
Compose ─► (AI draft, optional) ─► Review/edit ─► Approve+Schedule ─► DB
                                                                       │ poll 60s
                                                          Scheduler worker ─► Facebook / LinkedIn / Threads
```

Content drafting is **hybrid**: the AI proposes, you approve. Nothing is
published without an explicit approval.

## Quick start (local, Docker)

```bash
cp .env.example .env
# Generate a Fernet key and paste it into FERNET_KEY:
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Set at least one AI key (ANTHROPIC_API_KEY / OPENAI_API_KEY / GEMINI_API_KEY)
# and an ADMIN_EMAIL / ADMIN_PASSWORD.

docker compose up --build
# Web UI: http://localhost:8000  (log in with ADMIN_EMAIL / ADMIN_PASSWORD)
```

`docker compose` runs Postgres, applies migrations, then starts the web app and
the scheduler worker as separate services.

## Quick start (local, no Docker)

```bash
python -m venv .venv && . .venv/Scripts/activate   # Windows
#                       . .venv/bin/activate        # macOS/Linux
pip install -r requirements.txt

cp .env.example .env   # set FERNET_KEY, an AI key, admin creds
# For zero-setup dev you can use SQLite:  DATABASE_URL=sqlite:///./smap.db
alembic upgrade head

# Terminal 1 — API
uvicorn app.main:app --reload                       # http://localhost:8000
# Terminal 2 — frontend dev server (proxies /api + /oauth to :8000)
cd frontend && npm install && npm run dev           # http://localhost:5173
# Terminal 3 — scheduler worker
python -m app.scheduler.worker
```

Open **http://localhost:5173** during development (Vite hot-reloads the UI and
proxies API calls to the FastAPI app on `:8000`). For a production-style single
process instead, build the SPA once and let FastAPI serve it at `:8000`:

```bash
cd frontend && npm install && npm run build         # outputs frontend/dist
uvicorn app.main:app                                # serves the SPA at /
```

## Connecting platforms

Open **Accounts** in the dashboard. You can connect a platform two ways:

1. **OAuth** — click *Connect via OAuth* (needs the platform's app credentials in
   `.env`, plus the relevant approvals).
2. **Manual** — expand *Add manually* and paste the account id + access token
   directly (works immediately, before App Review is granted). *Verify & save*
   checks the token with the platform and auto-fills the display name; *Save
   without checking* stores it as-is. Tokens are Fernet-encrypted at rest and are
   never rendered back in the UI — only "token set · expires…" metadata is shown.

For OAuth, each platform needs app credentials in `.env` (otherwise it shows "not
configured"):

| Platform | Credentials | Notes |
|---|---|---|
| Facebook | `META_APP_ID`, `META_APP_SECRET` | Needs `pages_manage_posts`, Business Verification + App Review. Yields a never-expiring Page token. |
| Threads  | `META_APP_ID`, `META_APP_SECRET` | Scopes `threads_basic`, `threads_content_publish`. Long-lived token, auto-refreshed. |
| LinkedIn | `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET` | "Share on LinkedIn" / Community Management product; 60-day token + refresh. |

Set `APP_BASE_URL` to your public URL — the OAuth redirect URIs are
`{APP_BASE_URL}/oauth/{platform}/callback`; register these in each provider's app.

> Meta App Review and LinkedIn product access can take days. Start them early.

## AI model selection

The compose screen has a **per-draft model dropdown** populated from the model
registry (`app/ai/base.py`). Only providers whose API key is set appear. Default
is `claude-opus-4-8`. The provider + model used are recorded on each post.

## Configuration

All settings come from `.env` (see `.env.example` for the full list and how to
generate `FERNET_KEY`). Tokens are encrypted at rest with Fernet. Times are
stored in UTC and displayed in `DISPLAY_TIMEZONE`.

## Tests

```bash
pytest
```

Covers token encryption, the AI orchestrator/registry routing, the scheduler's
due-post + retry logic, and the three publishers (mocked HTTP).

## Production (VPS)

1. Provision Postgres and a Python 3.12 venv at `/opt/social-media-auto-posting`.
2. `alembic upgrade head`.
3. Build the SPA: `cd frontend && npm ci && npm run build` (FastAPI then serves
   `frontend/dist` at `/`). The Docker image does this automatically.
4. Install the systemd units in `deploy/` (`smap-web.service`, `smap-worker.service`).
5. Put Nginx (see `deploy/nginx.conf.sample`) in front with TLS (certbot).
6. Set `APP_BASE_URL` to your HTTPS domain and register OAuth redirect URIs.

## Project layout

```
app/
  main.py            FastAPI JSON API + OAuth routes + SPA serving (prod)
  schemas.py         Pydantic request/response models (the API contract)
  config.py          settings (.env)
  models.py          SQLAlchemy models
  security.py        Fernet token encryption + password hashing
  auth.py            session-cookie auth
  services.py        post lifecycle helpers
  timeutil.py        UTC <-> display-timezone
  ai/                multi-provider drafting (base, anthropic, openai, gemini, drafting)
  publishers/        Facebook / LinkedIn / Threads (base protocol)
  oauth/             per-platform connect + refresh flows
  scheduler/         service.py (publish logic) + worker.py (APScheduler)
frontend/            React + TypeScript SPA (Vite, Tailwind, shadcn/ui)
  src/lib/           api client, types, platform branding
  src/components/    AppShell, theme toggle, shadcn/ui primitives, badges
  src/pages/         Login, Compose, Queue, Calendar, Accounts, Review
docs/workflow.svg    posting-workflow diagram (embedded in SERVICE.md)
docs/ONBOARDING.md   client intake/onboarding checklist
alembic/             migrations
deploy/              systemd units + nginx sample
tests/               pytest suite
```

## Media (images & video)

Attach images or a video to any draft in **Compose**. A post is **either 1–N
images (carousel) or a single video** — never mixed. Uploads go to **S3** when
`S3_BUCKET` is set, otherwise to a **local-disk fallback** served at
`{APP_BASE_URL}/media` (zero-config for dev). Platforms fetch media by its public
URL (LinkedIn additionally uploads the bytes through its Images/Videos API), so in
production the storage URL must be publicly reachable. Limits are configurable
(`MEDIA_MAX_IMAGE_MB`, `MEDIA_MAX_VIDEO_MB`).

## Current limitations (v1)

- Single admin user (bootstrapped from `.env`).
