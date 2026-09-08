"""
auth.py
-------
Lightweight local user authentication for the TikZ Diagram Studio.

Stores user accounts as a JSON file on disk (users.json).
Passwords are hashed with SHA-256 + a per-user salt — sufficient for a
local/demo application.  For production deployments replace this with
a proper identity provider (IBM AppID, OAuth, etc.).

Public API
----------
register_user(username, password, email) -> bool
    Create a new account; returns False if username already exists.

verify_user(username, password) -> bool
    Return True if credentials are correct.

get_user_info(username) -> dict | None
    Return the stored user record (without the password hash).
"""

import hashlib
import json
import os
import secrets
from pathlib import Path
from typing import Optional

# Location of the flat-file user store, next to this module
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


def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def register_user(username: str, password: str, email: str = "") -> bool:
    """
    Register a new user.

    Returns True on success, False if *username* is already taken.
    """
    username = username.strip().lower()
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
        "password_hash": _hash_password(password, salt),
    }
    _save_users(users)
    return True


def verify_user(username: str, password: str) -> bool:
    """Return True if *username* + *password* match a stored account."""
    username = username.strip().lower()
    users = _load_users()
    record = users.get(username)
    if not record:
        return False
    return record["password_hash"] == _hash_password(password, record["salt"])


def get_user_info(username: str) -> Optional[dict]:
    """Return user metadata without the password hash, or None if not found."""
    username = username.strip().lower()
    users = _load_users()
    record = users.get(username)
    if not record:
        return None
    return {
        "username": record["username"],
        "email": record.get("email", ""),
    }


def user_exists(username: str) -> bool:
    """Return True if *username* is registered."""
    return username.strip().lower() in _load_users()
