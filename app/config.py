"""Typed application configuration loaded from environment / .env."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


def _csv_list(value: str) -> list[str]:
    """Split a comma-separated setting into a clean list (drops blanks)."""
    return [s.strip() for s in value.split(",") if s.strip()]


def _csv_set(value: str) -> set[str]:
    return set(_csv_list(value))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Core
    database_url: str = "sqlite:///./smap.db"
    session_secret: str = "change-me"
    fernet_key: str = ""
    app_base_url: str = "http://localhost:8000"
    display_timezone: str = "UTC"
    # Comma-separated extra origins allowed to call the API with credentials
    # (e.g. a separately-hosted Vite dev server). Empty by default — the Vite
    # dev proxy keeps things same-origin, so CORS is normally unnecessary.
    cors_origins: str = ""

    # First admin (bootstrapped on startup when no users exist)
    admin_email: str = "admin@example.com"
    admin_password: str = "change-me"

    # AI providers
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    gemini_api_key: str = ""
    default_ai_model: str = "claude-opus-4-8"

    # Meta (Facebook + Threads)
    meta_app_id: str = ""
    meta_app_secret: str = ""
    facebook_graph_version: str = "v25.0"
    facebook_scopes: str = (
        "pages_show_list,pages_manage_posts,pages_read_engagement,business_management"
    )
    threads_scopes: str = "threads_basic,threads_content_publish"

    # LinkedIn
    linkedin_client_id: str = ""
    linkedin_client_secret: str = ""
    linkedin_api_version: str = "202505"
    linkedin_scopes: str = "w_member_social,r_liteprofile"

    # JWT (mobile / Bearer-token auth)
    jwt_algorithm: str = "HS256"
    jwt_expire_days: int = 30

    # Scheduler
    scheduler_poll_seconds: int = 60
    max_publish_attempts: int = 5

    # ── Media storage ──────────────────────────────────────────────────────
    # If s3_bucket is set, uploads go to S3 (boto3); otherwise they fall back to
    # local disk served at {APP_BASE_URL}/media (fine for dev/tests).
    s3_bucket: str = ""
    s3_region: str = "us-east-1"
    s3_endpoint_url: str = ""  # set for S3-compatible stores (R2/MinIO/Spaces)
    s3_public_base_url: str = ""  # CDN / public base; else derived from bucket+region
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    media_local_dir: str = "media"  # used only by the local fallback backend
    media_max_image_mb: int = 10
    media_max_video_mb: int = 200
    allowed_image_types: str = "image/jpeg,image/png,image/gif,image/webp"
    allowed_video_types: str = "video/mp4,video/quicktime"

    # ── Derived helpers ──────────────────────────────────────────────────
    @property
    def facebook_scope_list(self) -> list[str]:
        return _csv_list(self.facebook_scopes)

    @property
    def threads_scope_list(self) -> list[str]:
        return _csv_list(self.threads_scopes)

    @property
    def linkedin_scope_list(self) -> list[str]:
        return _csv_list(self.linkedin_scopes)

    @property
    def cors_origin_list(self) -> list[str]:
        return _csv_list(self.cors_origins)

    @property
    def allowed_image_type_set(self) -> set[str]:
        return _csv_set(self.allowed_image_types)

    @property
    def allowed_video_type_set(self) -> set[str]:
        return _csv_set(self.allowed_video_types)

    def redirect_uri(self, platform: str) -> str:
        """OAuth callback URL for a given platform."""
        return f"{self.app_base_url.rstrip('/')}/oauth/{platform}/callback"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
