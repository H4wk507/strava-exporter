import json
from typing import Any

import keyring
from keyring.errors import PasswordDeleteError

KEYRING_SERVICE = "strava-exporter"
KEYRING_USER = "tokens"
KEYRING_CREDENTIALS = "credentials"


def load_tokens() -> dict[str, Any] | None:
    raw = keyring.get_password(KEYRING_SERVICE, KEYRING_USER)
    return json.loads(raw) if raw else None


def save_tokens(tokens: dict[str, Any]) -> None:
    keyring.set_password(KEYRING_SERVICE, KEYRING_USER, json.dumps(tokens))


def load_credentials() -> tuple[int, str] | None:
    raw = keyring.get_password(KEYRING_SERVICE, KEYRING_CREDENTIALS)
    if not raw:
        return None
    data = json.loads(raw)
    return int(data["client_id"]), data["client_secret"]


def save_credentials(client_id: int, client_secret: str) -> None:
    keyring.set_password(
        KEYRING_SERVICE,
        KEYRING_CREDENTIALS,
        json.dumps({"client_id": client_id, "client_secret": client_secret}),
    )


def _delete(user: str) -> None:
    try:
        keyring.delete_password(KEYRING_SERVICE, user)
    except PasswordDeleteError:
        pass


def delete_credentials() -> None:
    _delete(KEYRING_CREDENTIALS)


def delete_tokens() -> None:
    _delete(KEYRING_USER)
