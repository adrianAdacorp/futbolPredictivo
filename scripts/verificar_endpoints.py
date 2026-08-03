"""Diagnóstico de acceso: prueba qué endpoints responde tu plan Sportmonks.

Uso (desde la raíz del proyecto):
    python scripts/verificar_endpoints.py
"""
import logging

import _bootstrap  # noqa: F401  (ajusta sys.path a la raíz del proyecto)
import requests

from config import settings
from src.logger import setup_logging

logger = logging.getLogger("verificar")

PRUEBAS = [
    ("Leagues (catálogo del plan)", "leagues", {}),
    ("Livescores (en vivo)", "livescores", {}),
    ("Fixtures (rango de fechas)", "fixtures/between/2025-08-01/2025-08-07",
     {"include": "participants;scores;league;season"}),
]


def _get(base_url, token, endpoint, params):
    url = f"{base_url.rstrip('/')}/{endpoint}"
    headers = {"Authorization": token, "Accept": "application/json"}
    return requests.get(url, headers=headers, params=params, timeout=30)


def _resumen(resp):
    if resp.status_code == 200:
        payload = resp.json()
        data = payload.get("data", [])
        n = len(data) if isinstance(data, list) else 1
        rate = payload.get("rate_limit") or {}
        return f"OK 200 | registros={n} | remaining={rate.get('remaining', '?')}"
    if resp.status_code == 403:
        return "403 FORBIDDEN | fuera de tu plan/suscripción"
    if resp.status_code == 401:
        return "401 UNAUTHORIZED | token inválido"
    return f"{resp.status_code} | {resp.text[:120]}"


def main():
    setup_logging(settings.LOG_DIR)
    token = settings.SPORTMONKS_TOKEN
    if not token:
        logger.error("SPORTMONKS_TOKEN vacío. Configura .env antes de probar.")
        raise SystemExit(1)

    logger.info("== DIAGNÓSTICO DE ENDPOINTS ==")
    league_ids, season_ids, fixture_ids = [], [], []

    for nombre, endpoint, params in PRUEBAS:
        try:
            resp = _get(settings.BASE_URL, token, endpoint, params)
        except requests.RequestException as exc:
            logger.error("%-32s | ERROR DE RED: %s", nombre, exc)
            continue
        logger.info("%-32s | %s", nombre, _resumen(resp))

        if resp.status_code == 200:
            for row in resp.json().get("data", []):
                if not isinstance(row, dict):
                    continue
                if endpoint == "leagues":
                    league_ids.append((row.get("id"), row.get("name")))
                if "fixtures/between" in endpoint:
                    fixture_ids.append(row.get("id"))
                    if row.get("season_id"):
                        season_ids.append(row.get("season_id"))

    if league_ids:
        logger.info("-- Ligas disponibles en tu plan --")
        for lid, name in league_ids:
            logger.info("   id=%s | %s", lid, name)

    if season_ids:
        sid = season_ids[0]
        resp = _get(settings.BASE_URL, token, f"standings/seasons/{sid}",
                    {"include": "participant"})
        logger.info("%-32s | %s", f"Standings (season {sid})", _resumen(resp))

    if fixture_ids:
        fid = fixture_ids[0]
        resp = _get(settings.BASE_URL, token,
                    f"odds/pre-match/fixtures/{fid}", {})
        logger.info("%-32s | %s", f"Odds (fixture {fid})", _resumen(resp))

    logger.info("== FIN DIAGNÓSTICO ==")


if __name__ == "__main__":
    main()
