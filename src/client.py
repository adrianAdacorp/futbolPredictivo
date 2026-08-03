"""Cliente HTTP para la API de Sportmonks v3.

- Autenticación por header (mantiene el token fuera de URLs/logs).
- Reintentos automáticos para errores transitorios (5xx / red) vía urllib3.
- Fail-fast en errores de cliente (4xx: 401/403/422) — no reintenta parámetros malos.
- Manejo de 429 (Retry-After) y del objeto rate_limit del cuerpo.
- Backoff exponencial y paginación transparente (pagination.has_more).
"""
import logging
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class SportmonksError(Exception):
    """Error no recuperable de la API."""


class SportmonksClient:
    def __init__(self, token, base_url, timeout=30, max_retries=5,
                 backoff_factor=1.5, rate_limit_buffer=5, per_page=50):
        if not token:
            raise SportmonksError(
                "Token vacío: define SPORTMONKS_TOKEN en el entorno (.env)."
            )
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.rate_limit_buffer = rate_limit_buffer
        self.per_page = per_page

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": token,
            "Accept": "application/json",
        })
        retry = Retry(
            total=3, connect=3, read=3,
            status_forcelist=(500, 502, 503, 504),
            allowed_methods=("GET",),
            backoff_factor=1.0,
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
        self.session.mount("https://", adapter)

    def _sleep_backoff(self, attempt):
        wait = self.backoff_factor * (2 ** attempt)
        logger.warning("Reintento %s: esperando %.1fs", attempt + 1, wait)
        time.sleep(wait)

    def _respect_rate_limit(self, payload):
        rate = payload.get("rate_limit") or {}
        remaining = rate.get("remaining")
        resets_in = rate.get("resets_in_seconds", 3600)
        if remaining is not None and remaining <= self.rate_limit_buffer:
            logger.warning(
                "Rate limit casi agotado (remaining=%s). Durmiendo %ss.",
                remaining, resets_in,
            )
            time.sleep(resets_in + 1)

    def get(self, endpoint, params=None):
        """GET a un endpoint. Devuelve el payload JSON completo."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        params = dict(params or {})

        for attempt in range(self.max_retries):
            try:
                resp = self.session.get(url, params=params, timeout=self.timeout)
            except requests.RequestException as exc:
                logger.error("Error de red en %s: %s", url, exc)
                self._sleep_backoff(attempt)
                continue

            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 60))
                logger.warning("429 Too Many Requests. Esperando %ss.", retry_after)
                time.sleep(retry_after)
                continue
            if resp.status_code == 401:
                raise SportmonksError("401 No autorizado: token inválido o sin permisos.")
            if resp.status_code == 403:
                raise SportmonksError("403 Prohibido: entidad fuera de tu suscripción.")
            if resp.status_code == 422:
                raise SportmonksError(f"422 Parámetros inválidos: {resp.text[:200]}")
            if 400 <= resp.status_code < 500:
                raise SportmonksError(
                    f"{resp.status_code} Error de cliente: {resp.text[:200]}")
            if resp.status_code >= 400:
                logger.error("HTTP %s en %s: %s", resp.status_code, url, resp.text[:300])
                self._sleep_backoff(attempt)
                continue

            payload = resp.json()
            self._respect_rate_limit(payload)
            return payload

        raise SportmonksError(f"Fallo tras {self.max_retries} intentos: {url}")

    def fetch_all(self, endpoint, params=None, max_pages=None):
        """Recorre la paginación y devuelve la lista completa de registros."""
        params = dict(params or {})
        params.setdefault("per_page", self.per_page)
        records, page = [], 1

        while True:
            params["page"] = page
            payload = self.get(endpoint, params)
            data = payload.get("data", [])

            if isinstance(data, dict):
                return [data]

            records.extend(data)
            pagination = payload.get("pagination") or {}
            if not pagination.get("has_more"):
                break
            if max_pages and page >= max_pages:
                logger.info("Límite de páginas (%s) alcanzado.", max_pages)
                break
            page += 1

        return records
