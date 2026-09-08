"""
auth.py
-------
Lightweight local user authentication for the TikZ Diagram Studio.

Stores user accounts as a JSON file (users.json) next to this module.
Passwords are hashed with SHA-256 + per-user salt.

Old records created without a salt are automatically detected and
migrated to the salted format on first successful login.

Public API
----------
register_user(username, password, email) -> bool
    Create a new account; returns False if username already exists.

verify_user(username, password) -> bool
    Return True if credentials are correct (handles legacy + new records).

get_user_info(username) -> dict | None
    Return stored user metadata (without password hash).

user_exists(username) -> bool
    Return True if username is registered.
"""

import hashlib
import json
import secrets
from pathlib import Path
from typing import Optional

_USERS_FILE = Path(__file__).parent / "users.json"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_users() -> dict:
    if _USERS_FILE.exists():
        try:
            return json.loads(_USERS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_users(users: dict) -> None:
    _USERS_FILE.write_text(
        json.dumps(users, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _hash_salted(password: str, salt: str) -> str:
    """New-style: salt + password → SHA-256."""
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def _hash_legacy(password: str) -> str:
    """Old-style: plain SHA-256 (no salt) — used only for migration."""
    return hashlib.sha256(password.encode()).hexdigest()


def _normalize(username: str) -> str:
    return username.strip().lower()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def register_user(username: str, password: str, email: str = "") -> bool:
    """
    Register a new user.
    Returns True on success, False if username is already taken or input is invalid.
    """
    username = _normalize(username)
    if not username or not password:
        return False

    users = _load_users()
    if username in users:
        return False

    salt = secrets.token_hex(16)
    users[username] = {
        "username": username,
        "email": email.strip(),
        "salt": salt,
        "password_hash": _hash_salted(password, salt),
    }
    _save_users(users)
    return True


def verify_user(username: str, password: str) -> bool:
    """
    Return True if username + password match.

    Handles both:
    - New records (have a 'salt' field)
    - Legacy records (no 'salt' — created by older auth code)
      → migrates them to salted format automatically on success.
    """
    username = _normalize(username)
    users = _load_users()
    record = users.get(username)
    if not record:
        return False

    if "salt" in record:
        # New-style salted record
        return _hash_salted(password, record["salt"]) == record["password_hash"]
    else:
        # Legacy record — try plain SHA-256
        if _hash_legacy(password) == record["password_hash"]:
            # ✅ Password correct — migrate to salted format now
            salt = secrets.token_hex(16)
            record["salt"] = salt
            record["password_hash"] = _hash_salted(password, salt)
            users[username] = record
            _save_users(users)
            return True
        return False


def get_user_info(username: str) -> Optional[dict]:
    """Return user metadata without the password hash, or None if not found."""
    username = _normalize(username)
    users = _load_users()
    record = users.get(username)
    if not record:
        return None
    return {
        "username": record.get("username", username),
        "email": record.get("email", ""),
    }


def user_exists(username: str) -> bool:
    """Return True if username is registered."""
    return _normalize(username) in _load_users()
