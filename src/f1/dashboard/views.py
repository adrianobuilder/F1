"""Apresentacao das cinco visoes e exportacao da populacao exibida."""

import pandas as pd
import streamlit as st

from f1.dashboard.charts import labelled, line_chart, stint_chart
from f1.domain.models import Endpoint, F1Error
from f1.processing.analytics import (
    filter_drivers,
    format_lap,
    lap_series,
    lap_summary,
    localize_times,
    valid_laps,
)
from f1.processing.service import DataService

VIEW_ENDPOINTS: dict[str, tuple[Endpoint, ...]] = {
    "Resumo": (),
    "Comparação": (Endpoint.LAPS,),
    "Estratégia": (Endpoint.STINTS, Endpoint.PIT),
    "Posições": (Endpoint.POSITION,),
    "Clima": (Endpoint.WEATHER,),
}


def table(frame: pd.DataFrame, key: str) -> None:
    """Apresenta tabela e exporta exatamente as mesmas linhas/colunas."""
    frame = frame.drop(
        columns=[
            "meeting_key",
            "session_key",
            "segments_sector_1",
            "segments_sector_2",
            "segments_sector_3",
            "pit_duration",
        ],
        errors="ignore",
    ).rename(
        columns={
            "driver_number": "Número",
            "position": "Posição",
            "number_of_laps": "Voltas",
            "points": "Pontos",
            "dnf": "Não terminou",
            "dns": "Não largou",
            "dsq": "Desclassificado",
            "duration": "Duração (s)",
            "duration_q1": "Q1 (s)",
            "duration_q2": "Q2 (s)",
            "duration_q3": "Q3 (s)",
            "gap_to_leader": "Diferença para o líder",
            "gap_to_leader_q1": "Diferença Q1",
            "gap_to_leader_q2": "Diferença Q2",
            "gap_to_leader_q3": "Diferença Q3",
            "lap_number": "Volta",
            "lap_duration": "Tempo de volta (s)",
            "date": "Horário",
            "date_start": "Início",
            "stint_number": "Stint",
            "compound": "Composto",
            "lap_start": "Volta inicial",
            "lap_end": "Volta final",
            "tyre_age_at_start": "Idade inicial do pneu (voltas)",
            "air_temperature": "Ar (°C)",
            "track_temperature": "Pista (°C)",
            "humidity": "Umidade (%)",
            "pressure": "Pressão (mbar)",
            "rainfall": "Chuva (0/1)",
            "wind_speed": "Vento (m/s)",
            "wind_direction": "Direção do vento (°)",
            "is_pit_out_lap": "Saída dos boxes",
            "duration_sector_1": "Setor 1 (s)",
            "duration_sector_2": "Setor 2 (s)",
            "duration_sector_3": "Setor 3 (s)",
            "i1_speed": "Velocidade I1 (km/h)",
            "i2_speed": "Velocidade I2 (km/h)",
            "st_speed": "Speed trap (km/h)",
        }
    )
    numeric_format = {
        str(column): st.column_config.NumberColumn(format="%.3f")
        for column in frame.select_dtypes(include="float").columns
    }
    st.dataframe(frame, hide_index=True, width="stretch", column_config=numeric_format)
    st.download_button(
        "Baixar CSV",
        frame.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"f1_{key}.csv",
        mime="text/csv",
        key=f"download_{key}",
    )


def load_frame(
    service: DataService, endpoint: Endpoint, session: int, refresh: bool
) -> pd.DataFrame:
    """Carrega via servico e informa origem, vazio e fallback em cada recurso."""
    try:
        dataset = service.dataset(endpoint, {"session_key": session}, refresh=refresh)
    except F1Error as exc:
        st.warning(f"{endpoint.value}: {exc}")
        return pd.DataFrame()
    if dataset.provenance.warning:
        st.warning(dataset.provenance.warning)
    collected = dataset.provenance.collected_at.strftime("%d/%m/%Y %H:%M UTC")
    st.caption(f"OpenF1 / {endpoint.value} · coletado em {collected}")
    if dataset.frame.empty:
        st.info("A fonte não disponibilizou registros para esta sessão.")
    return dataset.frame


@st.cache_data(show_spinner=False, max_entries=32)
def cached_summary(laps: pd.DataFrame, selected: tuple[int, ...]) -> pd.DataFrame:
    """Cache apenas de calculo puro; arquivos continuam sendo a persistencia."""
    return lap_summary(laps, list(selected))


def render_view(
    view: str,
    service: DataService,
    session: int,
    selected: list[int],
    names: dict[int, str],
    colors: dict[str, str],
    results: pd.DataFrame,
    refresh: bool,
    offset: str,
) -> None:
    """Busca somente os recursos necessarios para a visao aberta."""
    if view == "Resumo":
        st.subheader("Resultado da sessão")
        frame = results.sort_values("position") if "position" in results else results
        if frame.empty:
            st.info("Resultado ainda não disponível na fonte.")
        else:
            table(labelled(filter_drivers(frame, selected), names), f"result_{session}")
        return
    frames = {
        endpoint: localize_times(
            load_frame(service, endpoint, session, refresh), offset
        )
        for endpoint in VIEW_ENDPOINTS[view]
    }
    if view == "Comparação":
        render_comparison(frames[Endpoint.LAPS], selected, names, colors, session)
    elif view == "Estratégia":
        render_strategy(frames, selected, names, session)
    elif view == "Posições":
        frame = labelled(filter_drivers(frames[Endpoint.POSITION], selected), names)
        if not frame.empty and "position" in frame:
            st.plotly_chart(
                line_chart(
                    frame,
                    "date",
                    "position",
                    "Evolução das posições",
                    colors,
                    reverse=True,
                    labels={"date": "Horário do evento", "position": "Posição"},
                ),
                width="stretch",
            )
            table(frame, f"position_{session}")
    else:
        render_weather(frames[Endpoint.WEATHER], session)


def render_comparison(
    laps: pd.DataFrame,
    selected: list[int],
    names: dict[int, str],
    colors: dict[str, str],
    session: int,
) -> None:
    """Apresenta estatisticas e serie por volta, com exclusoes explicitas."""
    summary = cached_summary(laps, tuple(selected))
    if summary.empty:
        st.info("Sem voltas válidas para os pilotos selecionados.")
        return
    columns = st.columns(len(summary))
    for column, row in zip(columns, summary.to_dict("records"), strict=True):
        column.metric(
            names.get(row["driver_number"], str(row["driver_number"])),
            format_lap(row["best_lap"]),
        )
        column.caption(f"Melhor volta · {int(row['laps'])} voltas consideradas")
    st.caption(
        "Tempos positivos e não nulos; voltas de saída dos boxes excluídas. "
        "A média descreve as voltas selecionadas, sem correção de ritmo."
    )
    table(
        labelled(summary, names).rename(
            columns={
                "best_lap": "Melhor volta (s)",
                "mean_lap": "Média (s)",
                "laps": "Voltas consideradas",
            }
        ),
        f"comparison_{session}",
    )
    frame = labelled(lap_series(laps, selected), names)
    st.plotly_chart(
        line_chart(
            frame,
            "lap_number",
            "lap_duration",
            "Tempo por volta",
            colors,
            labels={"lap_number": "Volta", "lap_duration": "Duração (s)"},
        ),
        width="stretch",
    )
    sectors = [str(key) for key in frame if str(key).startswith("duration_sector_")]
    if sectors:
        sector_frame = frame.melt(
            id_vars=["Piloto", "lap_number"],
            value_vars=sectors,
            var_name="Setor",
            value_name="Duração (s)",
        )
        sector = st.selectbox(
            "Setor", sectors, format_func=lambda value: f"Setor {value[-1]}"
        )
        st.plotly_chart(
            line_chart(
                sector_frame.loc[sector_frame["Setor"].eq(sector)],
                "lap_number",
                "Duração (s)",
                f"Setor {sector[-1]}",
                colors,
                labels={"lap_number": "Volta"},
            ),
            width="stretch",
        )
    with st.expander("Voltas consideradas"):
        table(labelled(valid_laps(laps, selected), names), f"laps_{session}")


def render_strategy(
    frames: dict[Endpoint, pd.DataFrame],
    selected: list[int],
    names: dict[int, str],
    session: int,
) -> None:
    """Mantem tempo parado distinto do tempo total de passagem pelo pit lane."""
    stints = labelled(filter_drivers(frames[Endpoint.STINTS], selected), names)
    if not stints.empty:
        st.plotly_chart(stint_chart(stints), width="stretch")
        table(stints, f"stints_{session}")
    st.subheader("Paradas nos boxes")
    pit = labelled(filter_drivers(frames[Endpoint.PIT], selected), names)
    if not pit.empty:
        if "stop_duration" not in pit or pit["stop_duration"].isna().all():
            st.info(
                "Tempo parado não disponível. Ele não equivale ao tempo no pit lane."
            )
        table(
            pit.rename(
                columns={
                    "stop_duration": "Tempo parado (s)",
                    "lane_duration": "Tempo no pit lane (s)",
                }
            ),
            f"pit_{session}",
        )


def render_weather(frame: pd.DataFrame, session: int) -> None:
    """Series de clima sem substituir medicoes ausentes por zero."""
    if frame.empty:
        return
    for field, title, unit in (
        ("air_temperature", "Temperatura do ar", "°C"),
        ("track_temperature", "Temperatura da pista", "°C"),
        ("humidity", "Umidade relativa", "%"),
        ("wind_speed", "Velocidade do vento", "m/s"),
        ("wind_direction", "Direção do vento", "°"),
        ("rainfall", "Presença de chuva", "0/1"),
    ):
        if field in frame and frame[field].notna().any():
            st.plotly_chart(
                line_chart(
                    frame,
                    "date",
                    field,
                    title,
                    labels={"date": "Horário do evento", field: f"{title} ({unit})"},
                ),
                width="stretch",
            )
    table(frame, f"weather_{session}")
