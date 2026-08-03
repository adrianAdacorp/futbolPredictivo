"""Validación automatizada con Pandera (Punto 3).

Define esquemas declarativos (tipos, rangos, categorías, unicidad) para los
datasets procesados. validate() aplica el esquema y lanza error si algo falla.
"""
import logging

try:
    import pandera.pandas as pa
except ImportError:  # compatibilidad con versiones previas
    import pandera as pa

logger = logging.getLogger(__name__)


fixtures_features_schema = pa.DataFrameSchema(
    {
        "fixture_id": pa.Column(nullable=False, unique=True),
        "league_name": pa.Column(nullable=False),
        "home_goals": pa.Column(int, pa.Check.ge(0), nullable=False, coerce=True),
        "away_goals": pa.Column(int, pa.Check.ge(0), nullable=False, coerce=True),
        "total_goals": pa.Column(int, pa.Check.ge(0), coerce=True),
        "result_1x2": pa.Column(str, pa.Check.isin(["H", "D", "A"])),
        "home_win": pa.Column(int, pa.Check.isin([0, 1]), coerce=True),
        "btts": pa.Column(int, pa.Check.isin([0, 1]), coerce=True),
        "points_home": pa.Column(int, pa.Check.isin([0, 1, 3]), coerce=True),
        "points_away": pa.Column(int, pa.Check.isin([0, 1, 3]), coerce=True),
    },
    strict=False,   # permite columnas extra (month, goals_bin, form, etc.)
    coerce=True,
)


market_gap_schema = pa.DataFrameSchema(
    {
        "fixture_id": pa.Column(nullable=False),
        "imp_home": pa.Column(float, pa.Check.in_range(0, 1), coerce=True),
        "imp_draw": pa.Column(float, pa.Check.in_range(0, 1), coerce=True),
        "imp_away": pa.Column(float, pa.Check.in_range(0, 1), coerce=True),
        "imp_prob_actual": pa.Column(float, pa.Check.in_range(0, 1), coerce=True),
        "market_surprise": pa.Column(float, pa.Check.in_range(0, 1), coerce=True),
        "n_bookmakers": pa.Column(nullable=True, coerce=True),
    },
    strict=False,
    coerce=True,
)


def validate(df, schema, name):
    """Valida df contra schema. Devuelve el df validado o relanza el error."""
    try:
        out = schema.validate(df, lazy=True)
        logger.info("Validación [%s]: OK (%s filas)", name, len(out))
        return out
    except pa.errors.SchemaErrors as exc:
        logger.error("Validación [%s]: FALLÓ", name)
        logger.error("%s", exc.failure_cases.head(20).to_string())
        raise
