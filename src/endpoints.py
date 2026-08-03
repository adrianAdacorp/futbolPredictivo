"""Funciones de acceso a endpoints Sportmonks v3.

El sistema de `includes` (separados por ';') anexa entidades relacionadas en
una sola llamada, reduciendo el volumen de peticiones al cupo horario.
Ref: https://docs.sportmonks.com/v3
"""
from datetime import date, timedelta

FIXTURE_INCLUDES = "participants;scores;league;season;round;state;venue"
STANDINGS_INCLUDES = "participant;details.type"
H2H_INCLUDES = "participants;scores;league"


def _date_windows(start, end, max_days=95):
    """Divide [start, end] en ventanas de <= max_days (límite API: 100 días)."""
    d0 = date.fromisoformat(start)
    d1 = date.fromisoformat(end)
    while d0 <= d1:
        w_end = min(d0 + timedelta(days=max_days - 1), d1)
        yield d0.isoformat(), w_end.isoformat()
        d0 = w_end + timedelta(days=1)


def fetch_fixtures_between(client, start, end, league_id=None,
                           includes=FIXTURE_INCLUDES, max_pages=None):
    """Fixtures entre fechas. Trocea en ventanas <=100 días (límite de la API)."""
    all_records = []
    for w_start, w_end in _date_windows(start, end):
        endpoint = f"fixtures/between/{w_start}/{w_end}"
        params = {"include": includes}
        if league_id is not None:
            params["filters"] = f"fixtureLeagues:{league_id}"
        all_records.extend(client.fetch_all(endpoint, params, max_pages=max_pages))
    return all_records


def fetch_standings_by_season(client, season_id, includes=STANDINGS_INCLUDES):
    """Tabla de posiciones de una temporada."""
    endpoint = f"standings/seasons/{season_id}"
    return client.fetch_all(endpoint, {"include": includes})


def fetch_h2h(client, team_a, team_b, includes=H2H_INCLUDES):
    """Historial de enfrentamientos directos entre dos equipos."""
    endpoint = f"fixtures/head-to-head/{team_a}/{team_b}"
    return client.fetch_all(endpoint, {"include": includes})


def fetch_odds_by_fixture(client, fixture_id):
    """Cuotas pre-partido para un fixture."""
    endpoint = f"odds/pre-match/fixtures/{fixture_id}"
    return client.fetch_all(endpoint, {})
