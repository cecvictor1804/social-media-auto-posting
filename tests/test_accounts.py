"""Account storage + JSON API smoke tests.

Covers the shared encrypted upsert path and the React SPA's JSON contract:
login, listing, manual account creation (no token echoed), and that the core
read endpoints respond 200 with JSON.
"""

from __future__ import annotations

from datetime import timedelta

from app.models import Platform, SocialAccount, utcnow
from app.oauth.base import ConnectedAccount
from app.security import decrypt_token
from app.services import upsert_social_account


def test_upsert_encrypts_and_creates(session):
    acc = upsert_social_account(
        session,
        ConnectedAccount(
            platform=Platform.facebook,
            platform_account_id="page-1",
            display_name="My Page",
            access_token="secret-token",
            token_expires_at=utcnow() + timedelta(days=30),
        ),
    )
    # Token is stored encrypted (not plaintext) and round-trips.
    assert acc.access_token_enc != "secret-token"
    assert "secret-token" not in acc.access_token_enc
    assert decrypt_token(acc.access_token_enc) == "secret-token"
    assert acc.is_active is True


def test_upsert_updates_existing(session):
    first = upsert_social_account(
        session,
        ConnectedAccount(
            platform=Platform.facebook,
            platform_account_id="page-1",
            display_name="Old name",
            access_token="t1",
        ),
    )
    second = upsert_social_account(
        session,
        ConnectedAccount(
            platform=Platform.facebook,
            platform_account_id="page-1",  # same identity
            display_name="New name",
            access_token="t2",
        ),
    )
    assert first.id == second.id  # updated, not duplicated
    assert session.query(SocialAccount).count() == 1
    assert second.display_name == "New name"
    assert decrypt_token(second.access_token_enc) == "t2"


def test_unauthenticated_api_is_401(client):
    # SPA intercepts 401 and routes to login.
    assert client.get("/api/posts").status_code == 401


def test_api_manual_add_and_reads(auth_client):
    # Manual add (action=save → no network/verify) creates an account and never
    # echoes the token back.
    r = auth_client.post(
        "/api/accounts/facebook/manual",
        json={
            "display_name": "Brand Page",
            "platform_account_id": "page-xyz",
            "access_token": "tok-123",
            "action": "save",
        },
    )
    assert r.status_code == 200, r.text
    created = r.json()
    assert created["display_name"] == "Brand Page"
    assert created["token_set"] is True
    assert "tok-123" not in r.text  # token never returned

    listing = auth_client.get("/api/accounts")
    assert listing.status_code == 200
    names = [a["display_name"] for a in listing.json()["accounts"]]
    assert "Brand Page" in names
    assert "tok-123" not in listing.text

    # Core read endpoints respond with JSON.
    assert auth_client.get("/api/meta").status_code == 200
    assert auth_client.get("/api/posts").status_code == 200
    assert auth_client.get("/api/calendar").status_code == 200
