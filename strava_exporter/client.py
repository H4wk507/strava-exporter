from __future__ import annotations

import time
import webbrowser
from collections.abc import Iterator
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, cast
from urllib.parse import parse_qs, urlparse

from stravalib import Client
from stravalib.model import AthleteStats, DetailedAthlete, SummaryActivity
from stravalib.protocol import AccessInfo, Scope

from strava_exporter.keyring import load_tokens, save_tokens


class StravaClient:
    SCOPES: list[Scope] = ["read", "activity:read_all", "profile:read_all"]
    REDIRECT_PORT = 8000
    REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}"

    def __init__(self, client_id: int, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self._client = Client()

        self._authenticate()

    def get_activities(
        self,
        after: datetime | None = None,
        limit: int | None = None,
    ) -> Iterator[SummaryActivity]:
        return self._client.get_activities(after=after, limit=limit)

    def get_athlete(self) -> DetailedAthlete:
        return self._client.get_athlete()

    def get_athlete_stats(self) -> AthleteStats:
        return self._client.get_athlete_stats()

    def _authenticate(self) -> None:
        """Load, authorize, or refresh tokens, then set the access token."""
        tokens = load_tokens() or self._authorize()

        if not tokens.get("access_token") or tokens.get("expires_at", 0) - time.time() < 60:
            print("Refreshing access token...")
            tokens = dict(
                self._client.refresh_access_token(self.client_id, self.client_secret, tokens["refresh_token"])
            )
            save_tokens(tokens)

        self._client.access_token = tokens["access_token"]

    def _authorize(self) -> dict[str, Any]:
        """Run the one-time browser authorization and store the new tokens."""
        url = self._client.authorization_url(self.client_id, self.REDIRECT_URI, scope=self.SCOPES)
        print(f"\nAuthorize in your browser (opening now):\n  {url}\n")
        webbrowser.open(url)
        code = self._capture_code()
        access_info = cast(AccessInfo, self._client.exchange_code_for_token(self.client_id, self.client_secret, code))
        tokens = dict(access_info)
        save_tokens(tokens)
        return tokens

    @classmethod
    def _capture_code(cls) -> str:
        """Run a one-shot local server and return the OAuth `code` from Strava."""
        captured: dict[str, str] = {}

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                code = parse_qs(urlparse(self.path).query).get("code", [None])[0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(
                    b"<h2>Authorized. You can close this tab.</h2>" if code else b"<h2>Authorization failed.</h2>"
                )
                if code:
                    captured["code"] = code

            def log_message(self, *_: Any) -> None:
                pass

        with HTTPServer(("localhost", cls.REDIRECT_PORT), Handler) as server:
            server.handle_request()
        if "code" not in captured:
            raise RuntimeError("Did not receive an authorization code from Strava.")
        return captured["code"]
