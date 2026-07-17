from __future__ import annotations

import csv
import json
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from stravalib.model import ActivityTotals, AthleteStats, DetailedAthlete, SummaryActivity

# Strava's workout_type codes: runs use 0-3, rides use 10-12.
_WORKOUT_TYPES = {
    0: "default",
    1: "race",
    2: "long_run",
    3: "workout",
    10: "default",
    11: "race",
    12: "workout",
}


def sport_type(a: SummaryActivity) -> str | None:
    for attr in (a.sport_type, a.type):
        if attr is not None and attr.root is not None:
            return str(attr.root)
    return None


def _num(value: float | None) -> float | None:
    return None if value is None else float(value)


def _workout_label(workout_type: int | None) -> str | None:
    return _WORKOUT_TYPES.get(workout_type) if workout_type is not None else None


def _iso_week(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    iso = dt.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def _row(a: SummaryActivity) -> dict[str, Any]:
    distance_m, moving_s = _num(a.distance), _num(a.moving_time)
    pace = (moving_s / 60) / (distance_m / 1000) if distance_m and moving_s else None
    speed_mps = _num(a.average_speed)
    local = a.start_date_local
    return {
        "id": a.id,
        "name": a.name,
        "sport_type": sport_type(a),
        "workout": _workout_label(a.workout_type),
        "date": a.start_date,
        "date_local": local,
        "day_of_week": local.strftime("%A") if local else None,
        "start_hour": local.hour if local else None,
        "iso_week": _iso_week(local),
        "distance_km": (distance_m / 1000) if distance_m else None,
        "moving_time_seconds": moving_s,
        "elapsed_time_seconds": _num(a.elapsed_time),
        "elevation_gain_m": _num(a.total_elevation_gain),
        "elev_high_m": _num(a.elev_high),
        "elev_low_m": _num(a.elev_low),
        "average_speed_mps": speed_mps,
        "average_speed_kmh": round(speed_mps * 3.6, 2) if speed_mps else None,
        "max_speed_mps": _num(a.max_speed),
        "average_pace_min_km": pace,
        "average_watts": _num(a.average_watts),
        "weighted_average_watts": _num(a.weighted_average_watts),
        "max_watts": _num(a.max_watts),
        "device_watts": a.device_watts,
        "kilojoules": _num(a.kilojoules),
        "has_heartrate": a.has_heartrate,
        "average_heartrate": a.average_heartrate,
        "max_heartrate": a.max_heartrate,
        "average_cadence": a.average_cadence,
        "relative_effort": a.suffer_score,
        "pr_count": a.pr_count,
        "trainer": a.trainer,
        "commute": a.commute,
        "manual": a.manual,
    }


def to_rows(activities: Iterable[SummaryActivity]) -> list[dict[str, Any]]:
    """Build rows sorted newest first (undated activities sort last)."""
    oldest = datetime.min.replace(tzinfo=timezone.utc)
    rows = [_row(a) for a in activities]
    rows.sort(key=lambda r: r["date"] or oldest, reverse=True)
    return rows


def write_csv(rows: list[dict[str, Any]], path: str | Path) -> None:
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _totals(t: ActivityTotals | None) -> dict[str, Any] | None:
    if t is None:
        return None
    distance_m, moving_s = _num(t.distance), _num(t.moving_time)
    return {
        "count": t.count,
        "distance_km": round(distance_m / 1000, 2) if distance_m is not None else None,
        "moving_time_hours": round(moving_s / 3600, 2) if moving_s is not None else None,
        "elevation_gain_m": _num(t.elevation_gain),
    }


def athlete_summary(athlete: DetailedAthlete, stats: AthleteStats) -> dict[str, Any]:
    """Flatten profile + rolling totals into the athlete's training baseline."""
    return {
        "athlete_id": athlete.id,
        "name": " ".join(p for p in (athlete.firstname, athlete.lastname) if p),
        "sex": athlete.sex,
        "weight_kg": _num(athlete.weight),
        "ftp": athlete.ftp,
        "recent_4w": {
            "run": _totals(stats.recent_run_totals),
            "ride": _totals(stats.recent_ride_totals),
            "swim": _totals(stats.recent_swim_totals),
        },
        "year_to_date": {
            "run": _totals(stats.ytd_run_totals),
            "ride": _totals(stats.ytd_ride_totals),
            "swim": _totals(stats.ytd_swim_totals),
        },
        "all_time": {
            "run": _totals(stats.all_run_totals),
            "ride": _totals(stats.all_ride_totals),
            "swim": _totals(stats.all_swim_totals),
        },
    }


def write_json(data: dict[str, Any], path: str | Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
