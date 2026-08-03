"""Configuración central del pipeline de ingesta Sportmonks.

Toda credencial se lee de variables de entorno (.env). NUNCA hardcodear el token.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- Credenciales / API -----------------------------------------------------
SPORTMONKS_TOKEN = os.getenv("SPORTMONKS_TOKEN", "")
BASE_URL = os.getenv("SPORTMONKS_BASE_URL", "https://api.sportmonks.com/v3/football")

# --- Rutas ------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PARQUET_DIR = DATA_DIR / "parquet"
LOG_DIR = BASE_DIR / "logs"

for _d in (RAW_DIR, PARQUET_DIR, LOG_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# --- Catálogo de competiciones (plan Free, verificado por diagnóstico) ------
LEAGUES = {
    "Danish Superliga": 271,
    "Scottish Premiership": 501,
}

# season_id de la temporada 2025/2026 (última completa) por liga.
SEASONS = {
    "Danish Superliga": 25536,
    "Scottish Premiership": 25598,
}

# --- Parámetros de red / rate limiting --------------------------------------
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "5"))
BACKOFF_FACTOR = float(os.getenv("BACKOFF_FACTOR", "1.5"))
RATE_LIMIT_BUFFER = int(os.getenv("RATE_LIMIT_BUFFER", "5"))
PER_PAGE = int(os.getenv("PER_PAGE", "50"))
