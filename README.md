# strava-exporter

> [!IMPORTANT]
> **Strava now requires a paid subscription to use the API.**
> Since **30 June 2026**, Strava's Developer Program _Standard Tier_ only works
> if the account that **owns the API application** has an active Strava
> subscription. Without one, your app is flagged **Inactive** and every request
> fails with 403.

Fetch your [Strava](https://www.strava.com) activities into a clean CSV, plus a
JSON snapshot of your training baseline - data you can hand to your personal
~~AI agent~~ trainer for context on your fitness and load.

## Quickstart

1. **Install uv:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Install dependencies:**

```bash
uv sync
```

3. **Create a Strava API application** at <https://www.strava.com/settings/api>.
   Set the _Authorization Callback Domain_ to `localhost`, then copy:
   - **Client ID** (a number)
   - **Client Secret** (40-character hex; click _Show_)

4. **Run it:**

```bash
uv run strava-exporter
```

On the first run it asks for the Client ID and Client Secret from step 3,
stores them in your OS keyring, and opens a browser to authorize once - later
runs reuse the stored tokens.

## Options

| Flag                  | Description                                                         |
| --------------------- | ------------------------------------------------------------------- |
| `-o, --output`        | Output CSV path (default: `activities.csv`)                         |
| `--days-back N`       | Only activities from the last N days (default: all time)            |
| `--sport TYPE`        | Sport type to keep, e.g. `Run` or `Ride`. Repeatable (default: all) |
| `--no-athlete-stats`  | Skip the `*.athlete.json` baseline                                  |
| `--reset-credentials` | Forget stored Client ID/Secret and tokens, then re-authenticate     |

## Security

Credentials and OAuth tokens live in your OS keyring (macOS Keychain / GNOME
Keyring / Windows Credential Locker), encrypted at rest - nothing on disk, no
`.env`.

## Development

The project uses Makefile for typical tasks:

- `make lint` - Ruff check + mypy --strict
- `make format` - Ruff format
- `make clean` - Remove cache files
