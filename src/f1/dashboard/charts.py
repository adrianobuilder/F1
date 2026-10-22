"""Figuras interativas sem consultas ou efeitos colaterais."""

import re
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

COMPOUNDS = {
    "SOFT": "#FF4655",
    "MEDIUM": "#FFD54A",
    "HARD": "#EDF2F7",
    "INTERMEDIATE": "#4AD891",
    "WET": "#4D9DFF",
    "UNKNOWN": "#8794AA",
}


def driver_maps(drivers: pd.DataFrame) -> tuple[dict[int, str], dict[str, str]]:
    """Associa identificadores a nomes e cores validas da equipe."""
    names, colors = {}, {}
    for row in drivers.to_dict("records"):
        number = int(row["driver_number"])
        name = f"{number} · {row.get('full_name') or row.get('name_acronym') or number}"
        names[number] = name
        color = str(row.get("team_colour", ""))
        if re.fullmatch(r"[0-9a-fA-F]{6}", color):
            colors[name] = f"#{color}"
    return names, colors


def labelled(frame: pd.DataFrame, names: dict[int, str]) -> pd.DataFrame:
    """Adiciona rotulos sem alterar a tabela de origem."""
    result = frame.copy()
    if "driver_number" in result:
        result["Piloto"] = (
            result["driver_number"]
            .map(names)
            .fillna(result["driver_number"].astype(str))
        )
    return result


def line_chart(
    frame: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    colors: dict[str, str] | None = None,
    *,
    reverse: bool = False,
    labels: dict[str, str] | None = None,
) -> go.Figure:
    """Desenha series sem ligar lacunas de medidas ausentes."""
    kwargs: dict[str, Any] = {}
    if "Piloto" in frame:
        kwargs.update(color="Piloto", color_discrete_map=colors or {})
    fig = px.line(frame.sort_values(x), x=x, y=y, title=title, labels=labels, **kwargs)
    fig.update_traces(connectgaps=False)
    if reverse:
        fig.update_yaxes(autorange="reversed", dtick=1)
        fig.update_traces(line_shape="hv")
    fig.update_layout(
        template="plotly_dark",
        height=390,
        margin=dict(l=20, r=20, t=55, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def stint_chart(frame: pd.DataFrame) -> go.Figure:
    """Mostra intervalos inclusivos de voltas por composto e piloto."""
    fig = go.Figure()
    legends: set[str] = set()
    for row in frame.to_dict("records"):
        compound = str(row.get("compound") or "UNKNOWN")
        start, end = row.get("lap_start"), row.get("lap_end")
        if pd.isna(start) or pd.isna(end) or end < start:
            continue
        fig.add_trace(
            go.Bar(
                y=[row["Piloto"]],
                x=[end - start + 1],
                base=[start],
                orientation="h",
                name=compound,
                legendgroup=compound,
                showlegend=compound not in legends,
                marker_color=COMPOUNDS.get(compound, "#8794AA"),
                customdata=[[start, end, row.get("tyre_age_at_start")]],
                hovertemplate="%{y}<br>Voltas %{customdata[0]} a %{customdata[1]}"
                "<br>Idade inicial: %{customdata[2]} voltas<extra>%{fullData.name}</extra>",
            )
        )
        legends.add(compound)
    fig.update_layout(
        title="Stints e compostos",
        barmode="overlay",
        template="plotly_dark",
        height=350,
        xaxis_title="Volta",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig
