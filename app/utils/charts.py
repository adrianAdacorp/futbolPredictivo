"""Funciones de visualización reutilizables (Plotly) para las vistas de la Data App."""
import pandas as pd
import plotly.express as px

# Paleta alineada al tema ejecutivo-deportivo (.streamlit/config.toml)
ACCENT = "#22C55E"       # verde cancha — métrica principal / neutral
POSITIVE = "#22C55E"     # sobre-rendimiento / victoria local
NEGATIVE = "#EF4444"     # sub-rendimiento / derrota
NEUTRAL = "#F59E0B"      # empate / dato intermedio
QUALITATIVE_PALETTE = ["#22C55E", "#38BDF8", "#F59E0B", "#A78BFA", "#F472B6", "#FB923C"]
 
def bar_by_team(df: pd.DataFrame, team_col: str, value_col: str, title: str, y_label: str,
                 agg: str = "mean", top_n: int = 20):
    """Barras agregando value_col por team_col. agg: 'mean' | 'sum' | 'count'. y_label: etiqueta legible del eje Y."""
    grouped = df.groupby(team_col, as_index=False)[value_col].agg(agg)
    grouped = grouped.sort_values(value_col, ascending=False).head(top_n)
    fig = px.bar(grouped, x=team_col, y=value_col, title=title, text=value_col,
                 color_discrete_sequence=[ACCENT])
    fig.update_traces(texttemplate="%{text:.0f}", textposition="outside", cliponaxis=False)
    fig.update_layout(xaxis_title="", yaxis_title=y_label, showlegend=False)
    return fig


def line_over_time(df: pd.DataFrame, date_col: str, value_col: str, color_col: str, title: str,
                    y_label: str, legend_label: str = "Equipo"):
    """Serie temporal coloreada por categoría (ej. equipo). y_label/legend_label: etiquetas legibles."""
    fig = px.line(df.sort_values(date_col), x=date_col, y=value_col, color=color_col, title=title,
                   markers=True, color_discrete_sequence=QUALITATIVE_PALETTE)
    fig.update_layout(xaxis_title="", yaxis_title=y_label, legend_title_text=legend_label)
    return fig


def scatter_gap(df: pd.DataFrame, x_col: str, y_col: str, color_col: str, hover_col: str, title: str,
                 x_label: str, y_label: str):
    """Scatter genérico (ej. dispersión de mercado vs. sorpresa). x_label/y_label: etiquetas legibles."""
    fig = px.scatter(df, x=x_col, y=y_col, color=color_col, hover_data=[hover_col], title=title,
                      color_discrete_sequence=QUALITATIVE_PALETTE)
    fig.update_layout(xaxis_title=x_label, yaxis_title=y_label, legend_title_text="")
    return fig


def month_trend_chart(df: pd.DataFrame, x_col: str, y_col: str, color_col: str, category_order: list,
                       title: str, y_label: str):
    """Línea de tendencia por mes de temporada (orden cronológico jul→may, no calendario ene→dic)."""
    fig = px.line(df, x=x_col, y=y_col, color=color_col, markers=True, title=title,
                   category_orders={x_col: category_order}, color_discrete_sequence=QUALITATIVE_PALETTE)
    fig.update_layout(xaxis_title="", yaxis_title=y_label, legend_title_text="")
    return fig


def distribution_hist(df: pd.DataFrame, value_col: str, title: str, x_label: str, nbins: int = 20):
    """Histograma de distribución de una variable continua. x_label: etiqueta legible del eje X."""
    fig = px.histogram(df, x=value_col, nbins=nbins, title=title, color_discrete_sequence=[ACCENT])
    fig.update_layout(yaxis_title="N.º de partidos", xaxis_title=x_label)
    return fig


def grouped_bar(df: pd.DataFrame, x_col: str, y_col: str, color_col: str, title: str, y_label: str,
                 color_map=None, value_suffix="", decimals=0):
    """
    Barras agrupadas por categoría de color (ej. comparar ligas por tipo de resultado).
    color_map: mapeo opcional {categoría: color} (ej. resultados 1X2); sin él usa la paleta cualitativa.
    value_suffix: texto tras el número en la etiqueta de barra (ej. "%"); vacío por defecto.
    decimals: decimales a mostrar en la etiqueta (0 para porcentajes, 2 para promedios de goles).
    """
    fig = px.bar(df, x=x_col, y=y_col, color=color_col, barmode="group", title=title, text=y_col,
                 color_discrete_map=color_map, color_discrete_sequence=QUALITATIVE_PALETTE)
    fig.update_traces(texttemplate=f"%{{text:.{decimals}f}}{value_suffix}", textposition="outside", cliponaxis=False)
    fig.update_layout(xaxis_title="", yaxis_title=y_label, legend_title_text="")
    return fig

def diverging_bar_by_team(df: pd.DataFrame, team_col: str, value_col: str, title: str, x_label: str, top_n: int = 10):
    """
    Barras horizontales divergentes (verde/rojo) para mostrar sobre/sub-rendimiento por equipo.
    Muestra los top_n equipos con mayor y menor valor promedio.
    """
    grouped = df.groupby(team_col, as_index=False)[value_col].mean().sort_values(value_col)
    grouped = pd.concat([grouped.head(top_n), grouped.tail(top_n)]).drop_duplicates(subset=team_col)
    grouped["Rendimiento"] = grouped[value_col].apply(lambda x: "Sobre-rendimiento" if x > 0 else "Sub-rendimiento")
    fig = px.bar(
        grouped, x=value_col, y=team_col, orientation="h", color="Rendimiento", text=value_col,
        color_discrete_map={"Sobre-rendimiento": POSITIVE, "Sub-rendimiento": NEGATIVE}, title=title,
    )
    fig.update_traces(texttemplate="%{text:.2f}", textposition="outside", cliponaxis=False)
    fig.update_layout(xaxis_title=x_label, yaxis_title="", legend_title_text="")
    return fig