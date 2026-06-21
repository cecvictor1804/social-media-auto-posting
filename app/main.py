"""FastAPI app wiring: middleware, API routers, OAuth redirects, SPA serving.

Run the web app:    uvicorn app.main:app --reload      (serves API on :8000)
Run the frontend:   cd frontend && npm run dev          (Vite dev server :5173,
                    proxies /api + /oauth + /healthz back to :8000)
Run the scheduler:  python -m app.scheduler.worker       (separate process)

In production the built SPA (``frontend/dist``) is served by this app at ``/``.
Route handlers live in app/api/*; this module only assembles them.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.api import accounts, auth, drafts, media, oauth, posts, token, users
from app.auth import ensure_admin
from app.config import settings
from app.db import SessionLocal

BASE_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = BASE_DIR / "frontend" / "dist"

app = FastAPI(title="Social Media Auto-Posting Agent")
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret)

if settings.cors_origin_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.on_event("startup")
def _startup() -> None:
    session = SessionLocal()
    try:
        ensure_admin(session)
    finally:
        session.close()


# JSON API (/api) + OAuth browser-redirect routes.
for _router in (auth.router, token.router, drafts.router, posts.router, media.router, accounts.router, oauth.router, users.router):
    app.include_router(_router)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


# ═══════════════ Local media serving (only when not using S3) ════════════════
# With S3 configured, media lives in the bucket and is fetched by its public URL.
# Otherwise the local-disk fallback stores files here and serves them at /media.
if not settings.s3_bucket:
    _media_dir = Path(settings.media_local_dir)
    _media_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/media", StaticFiles(directory=str(_media_dir)), name="media")


# ════════════════════════ Serve the built SPA (prod) ═════════════════════════
# In dev the Vite server hosts the SPA and proxies /api here, so DIST_DIR is
# absent and these mounts are skipped. After `npm run build` the app serves the
# compiled SPA at / with client-side routing (deep links return index.html).
if DIST_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="assets")
    _INDEX = DIST_DIR / "index.html"

    @app.get("/{full_path:path}")
    def spa(full_path: str):
        # API / OAuth / media / health are handled above; never fall through.
        if full_path.startswith(("api/", "oauth/", "media/")) or full_path == "healthz":
            raise HTTPException(status_code=404, detail="Not found")
        candidate = DIST_DIR / full_path
        if full_path and candidate.is_file():
            return FileResponse(str(candidate))
        return FileResponse(str(_INDEX))
