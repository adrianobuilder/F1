"""Entrada: poetry run streamlit run src/f1/dashboard/app.py."""

from datetime import UTC, datetime

import pandas as pd
import streamlit as st

from f1.dashboard.charts import driver_maps
from f1.dashboard.views import VIEW_ENDPOINTS, load_frame, render_view
from f1.domain.models import Endpoint, F1Error
from f1.processing.analytics import completed_sessions, default_drivers, event_time
from f1.processing.service import DataService, open_service
from f1.utils.config import Settings
from f1.utils.logging import configure_logging


def reset_filters(*keys: str) -> None:
    """Limpa selecoes dependentes quando muda um filtro superior."""
    for key in keys:
        st.session_state.pop(key, None)


def catalog(
    service: DataService, endpoint: Endpoint, year: int, refresh: bool
) -> pd.DataFrame:
    """Obtem catalogo com feedback visivel de fallback e coleta."""
    dataset = service.dataset(endpoint, {"year": year}, refresh=refresh)
    if dataset.provenance.warning:
        st.sidebar.warning(dataset.provenance.warning)
    st.sidebar.caption(
        f"{endpoint.value}: {dataset.provenance.collected_at:%d/%m/%Y %H:%M} UTC"
    )
    return dataset.frame


def dashboard(service: DataService) -> None:
    """Compõe seletores encadeados, indicadores e uma visao por vez."""
    with st.sidebar:
        st.markdown("### Filtros da sessão")
        year = st.selectbox(
            "Temporada",
            list(range(datetime.now(UTC).year, 2022, -1)),
            key="year",
            on_change=reset_filters,
            args=("meeting", "session", "pilots"),
        )
        refresh = st.button(
            "Atualizar dados",
            width="stretch",
            help="Atualiza os catálogos e os dados da visão selecionada.",
        )
    with st.spinner("Preparando catálogo histórico…"):
        meetings = catalog(service, Endpoint.MEETINGS, year, refresh)
        sessions = completed_sessions(
            catalog(service, Endpoint.SESSIONS, year, refresh)
        )
    if sessions.empty or meetings.empty:
        st.info(
            "Nenhuma sessão encerrada disponível nesta temporada. Selecione outro ano."
        )
        return
    available = sessions["meeting_key"].drop_duplicates().astype(int).tolist()
    meeting_names = dict(
        zip(meetings["meeting_key"], meetings["meeting_name"], strict=True)
    )
    with st.sidebar:
        meeting = st.selectbox(
            "Grande Prêmio",
            available,
            key="meeting",
            format_func=lambda value: meeting_names.get(value, str(value)),
            on_change=reset_filters,
            args=("session", "pilots"),
        )
    options = sessions.loc[sessions["meeting_key"].eq(meeting)]
    session_names = dict(
        zip(options["session_key"], options["session_name"], strict=True)
    )
    with st.sidebar:
        session = st.selectbox(
            "Sessão",
            options["session_key"].astype(int).tolist(),
            key="session",
            format_func=lambda value: session_names[value],
            on_change=reset_filters,
            args=("pilots",),
        )
    record = options.loc[options["session_key"].eq(session)].iloc[0]
    offset = str(record.get("gmt_offset") or "00:00:00")
    st.title(str(meeting_names.get(meeting, "Dashboard F1")))
    st.caption(
        f"{record['session_name']} · {record.get('circuit_short_name', '')} · "
        f"{event_time(record.get('date_start'), offset)}"
    )
    with st.spinner("Carregando participantes e resultado…"):
        drivers = load_frame(service, Endpoint.DRIVERS, session, refresh)
        results = load_frame(service, Endpoint.RESULTS, session, refresh)
    if drivers.empty:
        st.info("Sem participantes disponíveis para esta sessão.")
        return
    names, colors = driver_maps(drivers)
    if "pilots" in st.session_state:
        st.session_state["pilots"] = [
            int(value) for value in st.session_state["pilots"] if value in names
        ][:4]
    with st.sidebar:
        selected = st.multiselect(
            "Pilotos para comparar",
            list(names),
            default=default_drivers(drivers, results)
            if "pilots" not in st.session_state
            else None,
            format_func=lambda value: names[value],
            max_selections=4,
            key="pilots",
        )
        st.divider()
        st.caption(
            "Dados históricos · OpenF1\n\nHorários no fuso do evento. Sem acompanhamento ao vivo."
        )
    left, middle, right = st.columns(3)
    left.metric("Temporada", str(year))
    middle.metric("Participantes", len(drivers))
    right.metric("Pilotos selecionados", len(selected))
    if not selected:
        st.info("Selecione de um a quatro pilotos na barra lateral.")
        return
    view = st.radio(
        "Explorar sessão", list(VIEW_ENDPOINTS), horizontal=True, key="view"
    )
    st.divider()
    with st.spinner("Preparando a análise…"):
        render_view(
            view, service, session, selected, names, colors, results, refresh, offset
        )


def main() -> None:
    """Valida configuracao e encerra recursos a cada rerun."""
    st.set_page_config(page_title="F1 · Histórico", page_icon="🏁", layout="wide")
    st.markdown("**F1 / HISTÓRICO**")
    try:
        settings = Settings.from_env()
        configure_logging(settings.logger_level())
        with open_service(settings) as service:
            dashboard(service)
    except (F1Error, ValueError) as exc:
        st.error(str(exc))
        st.info(
            "Verifique a conexão ou selecione uma temporada com dados locais. Uma atualização pode recuperar arquivos inválidos."
        )


if __name__ == "__main__":
    main()
