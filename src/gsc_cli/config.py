"""Config directory and credential management."""

from __future__ import annotations

import json
import os
from pathlib import Path


def get_config_dir() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    config_dir = base / "gsc-cli"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def _secure_write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2))
    path.chmod(0o600)


def save_oauth_token(token_data: dict) -> Path:
    path = get_config_dir() / "oauth_token.json"
    _secure_write(path, token_data)
    return path


def load_oauth_token() -> dict | None:
    path = get_config_dir() / "oauth_token.json"
    if path.exists():
        return json.loads(path.read_text())
    return None


def save_service_account(key_data: dict) -> Path:
    path = get_config_dir() / "service_account.json"
    _secure_write(path, key_data)
    return path


def load_service_account() -> dict | None:
    path = get_config_dir() / "service_account.json"
    if path.exists():
        return json.loads(path.read_text())
    return None


def save_client_secrets(secrets_data: dict) -> Path:
    path = get_config_dir() / "client_secrets.json"
    _secure_write(path, secrets_data)
    return path


def load_client_secrets() -> dict | None:
    path = get_config_dir() / "client_secrets.json"
    if path.exists():
        return json.loads(path.read_text())
    return None


def save_config(config: dict) -> Path:
    path = get_config_dir() / "config.json"
    path.write_text(json.dumps(config, indent=2))
    return path


def load_config() -> dict:
    path = get_config_dir() / "config.json"
    if path.exists():
        return json.loads(path.read_text())
    return {}
