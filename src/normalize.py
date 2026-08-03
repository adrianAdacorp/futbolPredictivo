"""Normalización de respuestas JSON de Sportmonks a DataFrames planos."""
import logging

import pandas as pd

logger = logging.getLogger(__name__)


def _home_away(participants):
    home = away = None
    for p in participants or []:
        location = (p.get("meta") or {}).get("location")
        if location == "home":
            home = p.get("name")
        elif location == "away":
            away = p.get("name")
    return home, away


def _current_goals(scores):
    home_goals = away_goals = None
    for s in scores or []:
        if s.get("description") == "CURRENT":
            score = s.get("score") or {}
            participant = score.get("participant")
            goals = score.get("goals")
            if participant == "home":
                home_goals = goals
            elif participant == "away":
                away_goals = goals
    return home_goals, away_goals


def normalize_fixtures(records):
    """Aplana la respuesta de fixtures a un DataFrame tabular."""
    rows = []
    for f in records:
        home, away = _home_away(f.get("participants"))
        hg, ag = _current_goals(f.get("scores"))
        league = f.get("league") or {}
        season = f.get("season") or {}
        rows.append({
            "fixture_id": f.get("id"),
            "name": f.get("name"),
            "league_id": f.get("league_id"),
            "league_name": league.get("name"),
            "season_id": f.get("season_id"),
            "season_name": season.get("name"),
            "starting_at": f.get("starting_at"),
            "state_id": f.get("state_id"),
            "has_odds": f.get("has_odds"),
            "home_team": home,
            "away_team": away,
            "home_goals": hg,
            "away_goals": ag,
            "result_info": f.get("result_info"),
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df["starting_at"] = pd.to_datetime(df["starting_at"], errors="coerce")
    for col in ("fixture_id", "league_id", "season_id", "state_id",
                "home_goals", "away_goals"):
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    df = df.drop_duplicates(subset=["fixture_id"]).reset_index(drop=True)
    return df


def normalize_standings(records):
    """Aplana la tabla de posiciones."""
    rows = []
    for s in records:
        participant = s.get("participant") or {}
        rows.append({
            "season_id": s.get("season_id"),
            "league_id": s.get("league_id"),
            "position": s.get("position"),
            "team_id": participant.get("id"),
            "team_name": participant.get("name"),
            "points": s.get("points"),
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    for col in ("season_id", "league_id", "position", "team_id", "points"):
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    return df.sort_values(["season_id", "position"]).reset_index(drop=True)


def _to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_odds(records, fixture_id=None, league_name=None):
    """Aplana cuotas SIN agregar: una fila por selección/mercado/bookmaker.

    Añade la probabilidad implícita cruda (1/cuota) por selección.
    """
    rows = []
    for o in records:
        value = _to_float(o.get("value") or o.get("dp3"))
        implied = (1.0 / value) if value and value > 0 else None
        rows.append({
            "odd_id": o.get("id"),
            "fixture_id": o.get("fixture_id", fixture_id),
            "league_name": league_name,
            "market_id": o.get("market_id"),
            "market_description": o.get("market_description"),
            "bookmaker_id": o.get("bookmaker_id"),
            "label": o.get("label"),
            "original_label": o.get("original_label"),
            "value": value,
            "implied_prob": implied,
            "probability_raw": o.get("probability"),
            "handicap": o.get("handicap"),
            "total": o.get("total"),
            "latest_update": o.get("latest_bookmaker_update") or o.get("updated_at"),
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    for col in ("odd_id", "fixture_id", "market_id", "bookmaker_id"):
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    return df
