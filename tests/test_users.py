"""User management API tests — admin access, CRUD, and safety guards."""

from __future__ import annotations

import pytest

from app.models import User
from app.security import hash_password

ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "change-me"


# ── Bootstrap ────────────────────────────────────────────────────────────────

def test_bootstrap_admin_has_is_admin_flag(auth_client):
    r = auth_client.get("/api/auth/me")
    assert r.status_code == 200
    assert r.json()["is_admin"] is True


# ── Access control ────────────────────────────────────────────────────────────

def test_non_admin_cannot_list_users(client, session):
    _add_user(session, "plain@example.com", is_admin=False)
    client.post("/api/auth/login", json={"email": "plain@example.com", "password": "pass"})
    assert client.get("/api/users").status_code == 403


def test_non_admin_cannot_create_user(client, session):
    _add_user(session, "plain@example.com", is_admin=False)
    client.post("/api/auth/login", json={"email": "plain@example.com", "password": "pass"})
    r = client.post("/api/users", json={"email": "new@example.com", "password": "x"})
    assert r.status_code == 403


def test_unauthenticated_cannot_access_users(client):
    assert client.get("/api/users").status_code == 401


# ── List ──────────────────────────────────────────────────────────────────────

def test_admin_can_list_users(auth_client):
    r = auth_client.get("/api/users")
    assert r.status_code == 200
    users = r.json()
    assert isinstance(users, list)
    assert any(u["email"] == ADMIN_EMAIL for u in users)


# ── Create ────────────────────────────────────────────────────────────────────

def test_admin_creates_regular_user(auth_client):
    r = auth_client.post(
        "/api/users",
        json={"email": "bob@example.com", "password": "secret123", "is_admin": False},
    )
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["email"] == "bob@example.com"
    assert data["is_admin"] is False
    assert data["is_active"] is True


def test_admin_creates_admin_user(auth_client):
    r = auth_client.post(
        "/api/users",
        json={"email": "alice@example.com", "password": "pass", "is_admin": True},
    )
    assert r.status_code == 201
    assert r.json()["is_admin"] is True


def test_duplicate_email_rejected(auth_client):
    auth_client.post("/api/users", json={"email": "dup@example.com", "password": "a"})
    r = auth_client.post("/api/users", json={"email": "dup@example.com", "password": "b"})
    assert r.status_code == 409


# ── Update ────────────────────────────────────────────────────────────────────

def test_toggle_admin_flag(auth_client):
    created = auth_client.post(
        "/api/users", json={"email": "t@example.com", "password": "x"}
    ).json()
    uid = created["id"]

    r = auth_client.patch(f"/api/users/{uid}", json={"is_admin": True})
    assert r.status_code == 200
    assert r.json()["is_admin"] is True

    r = auth_client.patch(f"/api/users/{uid}", json={"is_admin": False})
    assert r.status_code == 200
    assert r.json()["is_admin"] is False


def test_last_admin_cannot_be_demoted(auth_client):
    me = auth_client.get("/api/auth/me").json()
    r = auth_client.patch(f"/api/users/{me['id']}", json={"is_admin": False})
    assert r.status_code == 400
    assert "last admin" in r.json()["detail"].lower()


def test_deactivate_user_blocks_login(auth_client, client, session):
    _add_user(session, "tmp@example.com", is_admin=False)
    users = auth_client.get("/api/users").json()
    uid = next(u["id"] for u in users if u["email"] == "tmp@example.com")

    auth_client.patch(f"/api/users/{uid}", json={"is_active": False})

    r = client.post("/api/auth/login", json={"email": "tmp@example.com", "password": "pass"})
    assert r.status_code == 401


def test_reactivate_user_restores_login(auth_client, client, session):
    _add_user(session, "reac@example.com", is_admin=False)
    users = auth_client.get("/api/users").json()
    uid = next(u["id"] for u in users if u["email"] == "reac@example.com")

    auth_client.patch(f"/api/users/{uid}", json={"is_active": False})
    auth_client.patch(f"/api/users/{uid}", json={"is_active": True})

    r = client.post("/api/auth/login", json={"email": "reac@example.com", "password": "pass"})
    assert r.status_code == 200


# ── Helpers ───────────────────────────────────────────────────────────────────

def _add_user(session, email: str, *, is_admin: bool = False) -> User:
    u = User(email=email, password_hash=hash_password("pass"), is_admin=is_admin, is_active=True)
    session.add(u)
    session.commit()
    return u
