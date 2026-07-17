#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from getpass import getpass
from pathlib import Path

from strava_exporter.client import StravaClient
from strava_exporter.export import athlete_summary, sport_type, to_rows, write_csv, write_json
from strava_exporter.keyring import (
    delete_credentials,
    delete_tokens,
    load_credentials,
    save_credentials,
)


def prompt_credentials() -> tuple[int, str]:
    """Ask once for Strava API credentials; the caller stores them in the keyring."""
    print("Enter your Strava API credentials (https://www.strava.com/settings/api).")
    client_id = int(input("Client ID: ").strip())
    client_secret = getpass("Client Secret: ").strip()
    if not client_secret:
        raise ValueError("Client Secret must not be empty.")
    return client_id, client_secret


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch Strava activities into a CSV.")
    parser.add_argument("-o", "--output", default="activities.csv")
    parser.add_argument("--days-back", type=int, help="Only the last N days. Default: all time.")
    parser.add_argument("--sport", action="append", help="Keep sport type, e.g. Run (repeatable). Default: all.")
    parser.add_argument(
        "--no-athlete-stats",
        action="store_true",
        help="Skip the athlete baseline JSON (profile + recent/all-time totals).",
    )
    parser.add_argument(
        "--reset-credentials",
        action="store_true",
        help="Forget the stored Client ID/Secret and tokens, then re-authenticate.",
    )
    args = parser.parse_args(argv)

    if args.reset_credentials:
        delete_credentials()
        delete_tokens()
        print("Cleared stored Strava credentials and tokens.")

    credentials = load_credentials()
    if credentials is None:
        try:
            credentials = prompt_credentials()
        except (ValueError, EOFError, KeyboardInterrupt):
            print("\nInvalid or missing Strava API credentials.", file=sys.stderr)
            return 1
        save_credentials(*credentials)

    client = StravaClient(*credentials)

    after = None
    if args.days_back:
        after = datetime.now(timezone.utc) - timedelta(days=args.days_back)
    wanted = set(args.sport) if args.sport else None

    print("Fetching activities...")
    activities = [a for a in client.get_activities(after=after) if not wanted or sport_type(a) in wanted]
    rows = to_rows(activities)

    if rows:
        write_csv(rows, args.output)
        print(f"Wrote {len(rows)} activities to {args.output}")
    else:
        print("No activities found.")

    if not args.no_athlete_stats:
        out = Path(args.output)
        athlete_path = out.with_name(f"{out.stem}.athlete.json")
        try:
            summary = athlete_summary(client.get_athlete(), client.get_athlete_stats())
            write_json(summary, athlete_path)
            print(f"Wrote athlete baseline to {athlete_path}")
        except Exception as exc:  # non-fatal: the CSV is the main output
            print(f"Skipped athlete baseline ({exc}).", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
