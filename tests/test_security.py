from app.security import decrypt_token, encrypt_token, hash_password, verify_password


def test_token_roundtrip():
    secret = "ya29.super-secret-token"
    enc = encrypt_token(secret)
    assert enc != secret
    assert decrypt_token(enc) == secret


def test_empty_token_passthrough():
    assert encrypt_token("") == ""
    assert decrypt_token("") is None
    assert decrypt_token(None) is None


def test_password_hashing():
    h = hash_password("hunter2")
    assert verify_password("hunter2", h)
    assert not verify_password("wrong", h)
