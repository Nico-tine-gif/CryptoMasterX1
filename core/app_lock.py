import os
import json
import hashlib
import hmac
import secrets
from pathlib import Path

APP_DIR = Path.home() / ".cryptomasterx1"
AUTH_FILE = APP_DIR / "auth.json"

PBKDF2_ITERATIONS = 310000
SALT_BYTES = 32
HASH_BYTES = 32


def _ensure_directory():
    APP_DIR.mkdir(parents=True, exist_ok=True)


def _derive_password(password, salt):
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
        dklen=HASH_BYTES,
    )


def password_exists():
    return AUTH_FILE.exists()


def create_password(password):
    if not isinstance(password, str):
        raise ValueError("Password must be text.")

    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters.")

    _ensure_directory()

    salt = secrets.token_bytes(SALT_BYTES)
    password_hash = _derive_password(password, salt)

    data = {
        "algorithm": "PBKDF2-HMAC-SHA256",
        "iterations": PBKDF2_ITERATIONS,
        "salt": salt.hex(),
        "password_hash": password_hash.hex(),
    }

    temporary = AUTH_FILE.with_suffix(".tmp")

    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(data, handle)

    os.replace(temporary, AUTH_FILE)

    try:
        os.chmod(AUTH_FILE, 0o600)
    except Exception:
        pass


def verify_password(password):
    if not password_exists():
        return False

    try:
        with open(AUTH_FILE, "r", encoding="utf-8") as handle:
            data = json.load(handle)

        salt = bytes.fromhex(data["salt"])
        stored_hash = bytes.fromhex(data["password_hash"])

        calculated_hash = _derive_password(password, salt)

        return hmac.compare_digest(
            calculated_hash,
            stored_hash,
        )

    except Exception:
        return False


def change_password(old_password, new_password):
    if not verify_password(old_password):
        return False

    create_password(new_password)
    return True
