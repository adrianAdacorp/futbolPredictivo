# Sportmonks Ingest — Observatorio de Analítica Deportiva

Pipeline modular de ingesta y transformación de datos de fútbol desde la
**API de Sportmonks v3** hacia formato columnar **Parquet**, con feature
engineering, validación y optimización de memoria.

Ligas: **Superliga Danesa (271)** y **Premiership Escocesa (501)** — temporada 2025/2026.

## Estructura

```
sportmonks_ingest/
├── main.py                  # Ingesta (Temas 1-2): API -> Parquet
├── build_features.py        # Transformación (Tema 3): features + validación + escalado
├── requirements.txt
├── .env.example             # plantilla de variables de entorno
├── config/
│   └── settings.py          # env, rutas, catálogo de ligas/temporadas
├── src/
│   ├── client.py            # cliente HTTP: auth, retries, rate limit, paginación
│   ├── endpoints.py         # endpoints (fixtures con troceo de fechas, standings, odds)
│   ├── normalize.py         # JSON -> DataFrames (ingesta)
│   ├── storage.py           # escritura Parquet particionado (idempotente)
│   ├── logger.py            # logging
│   ├── pipeline.py          # orquestación de ingesta
│   ├── cleaning.py          # deduplicación / limpieza (Tema 3)
│   ├── features.py          # feature engineering + brecha vs. mercado (Tema 3)
│   ├── scaling.py           # normalización / estandarización (Tema 3)
│   ├── schemas.py           # validación automatizada con Pandera (Tema 3)
│   └── optimize.py          # downcasting / memoria (Tema 3)
├── scripts/                 # utilidades de diagnóstico (opcionales)
│   ├── verificar_endpoints.py
│   ├── obtener_seasons.py
│   ├── seasons_historicas.py
│   └── explorar_parquet.py
├── data/parquet/            # salida (raw + marts)
└── logs/                    # ingest.log
```

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows (PowerShell: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned)
pip install -r requirements.txt
copy .env.example .env            # y coloca tu token en SPORTMONKS_TOKEN
```

## Uso

```bash
# 1) Ingesta (Temas 1-2)
python main.py --start 2025-07-15 --end 2026-05-20

# 2) Transformación (Tema 3)
python build_features.py                # estandarización (z-score)
python build_features.py --scale minmax # normalización 0-1

# Diagnóstico (opcional)
python scripts/verificar_endpoints.py
python scripts/explorar_parquet.py
```

## Datasets generados

| Ruta | Contenido |
|---|---|
| `data/parquet/fixtures` | Partidos crudos normalizados |
| `data/parquet/standings` | Tablas de posiciones |
| `data/parquet/odds` | Cuotas crudas (todos los mercados/casas) |
| `data/parquet/marts/fixtures_features` | Features derivados + forma reciente |
| `data/parquet/marts/odds_1x2` | Odds 1X2 agregadas (consenso + spread) |
| `data/parquet/marts/market_gap` | Fixtures + odds + brecha vs. mercado (columnas escaladas `_z`) |
| `data/parquet/marts/standings_clean` | Posiciones deduplicadas |

## Cobertura por entrega

- **Tema 1-2 (ingesta):** API v3 con includes, troceo de fechas (límite 100 días),
  paginación, rate limiting, backoff, fail-fast en 4xx, logs, Parquet particionado.
- **Tema 3 (transformación):** feature engineering y agregaciones (`features.py`),
  binning (`pd.cut`), estandarización/normalización (`scaling.py`), validación
  automatizada con Pandera (`schemas.py`), optimización de memoria por downcasting
  y vectorización (`optimize.py`).

## Seguridad

- El token se lee **solo** de variable de entorno; nunca se hardcodea.
- `.env` está en `.gitignore`: no debe subirse al repositorio.
- El token viaja en el header `Authorization`, no en la query string.
