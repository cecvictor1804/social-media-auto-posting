"""Secret handling: Fernet token encryption and password hashing.

Platform OAuth tokens are encrypted with a Fernet key (``FERNET_KEY``) before
being written to the database, and decrypted only when needed to call a
platform API. Dashboard passwords are hashed with bcrypt via passlib.
"""

from __future__ import annotations

import bcrypt
from cryptography.fernet import Fernet

from app.config import settings


def _fernet() -> Fernet:
    if not settings.fernet_key:
        raise RuntimeError(
            "FERNET_KEY is not set. Generate one with:\n"
            '  python -c "from cryptography.fernet import Fernet; '
            'print(Fernet.generate_key().decode())"'
        )
    return Fernet(settings.fernet_key.encode())


def encrypt_token(plaintext: str) -> str:
    """Encrypt a token for storage. Empty input returns empty string."""
    if not plaintext:
        return ""
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str | None) -> str | None:
    """Decrypt a stored token. ``None``/empty passes through as ``None``."""
    if not ciphertext:
        return None
    return _fernet().decrypt(ciphertext.encode()).decode()


def hash_password(password: str) -> str:
    # bcrypt only uses the first 72 bytes; truncate explicitly to avoid errors.
    return bcrypt.hashpw(password.encode()[:72], bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode()[:72], password_hash.encode())
    except ValueError:
        return False
