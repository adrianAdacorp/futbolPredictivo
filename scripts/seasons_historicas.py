"""Lista las temporadas FINALIZADAS de cada liga y sugiere la más reciente.

Uso (desde la raíz):
    python scripts/seasons_historicas.py
"""
import logging

import _bootstrap  # noqa: F401
import requests

from config import settings
from src.logger import setup_logging

logger = logging.getLogger("seasons_hist")


def _seasons_de_liga(payload):
    data = payload.get("data") or {}
    seasons = data.get("seasons") or []
    if isinstance(seasons, dict):
        seasons = [seasons]
    return seasons


def main():
    setup_logging(settings.LOG_DIR)
    token = settings.SPORTMONKS_TOKEN
    if not token:
        logger.error("SPORTMONKS_TOKEN vacío. Configura .env.")
        raise SystemExit(1)

    headers = {"Authorization": token, "Accept": "application/json"}
    sugeridas = {}

    logger.info("== TEMPORADAS FINALIZADAS POR LIGA ==")
    for name, league_id in settings.LEAGUES.items():
        url = f"{settings.BASE_URL.rstrip('/')}/leagues/{league_id}"
        try:
            resp = requests.get(url, headers=headers,
                                params={"include": "seasons"}, timeout=30)
        except requests.RequestException as exc:
            logger.error("%-25s | ERROR DE RED: %s", name, exc)
            continue

        if resp.status_code != 200:
            logger.warning("%-25s | HTTP %s", name, resp.status_code)
            continue

        seasons = _seasons_de_liga(resp.json())
        finalizadas = [s for s in seasons if s.get("finished")]
        finalizadas.sort(key=lambda s: s.get("ending_at") or "", reverse=True)

        logger.info("-- %s (id=%s) | %s temporadas finalizadas --",
                    name, league_id, len(finalizadas))
        for s in finalizadas[:5]:
            logger.info("   id=%-6s | %-9s | %s -> %s",
                        s.get("id"), s.get("name"),
                        s.get("starting_at"), s.get("ending_at"))

        if finalizadas:
            top = finalizadas[0]
            sugeridas[name] = (top.get("id"), top.get("name"))

    logger.info("-- Sugerencia: última temporada completa por liga --")
    print("\nSEASONS = {")
    for name, (sid, sname) in sugeridas.items():
        print(f'    "{name}": {sid},  # {sname}')
    print("}\n")


if __name__ == "__main__":
    main()
