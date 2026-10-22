"""Interacoes reais Streamlit em execucao offline com fonte simulada."""

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import httpx
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from f1.dashboard.charts import driver_maps, line_chart, stint_chart
from f1.dashboard.views import table
from f1.domain.models import Endpoint, Record
from f1.ingestion.client import OpenF1Client
from f1.ingestion.storage import SnapshotStore
from f1.processing.service import DataService
from f1.utils.config import Settings


def test_all_views_filters_and_cached_reopen(
    tmp_path: Path, transport: httpx.MockTransport, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("F1_DATA_DIR", str(tmp_path))

    @contextmanager
    def factory(settings: Settings) -> Iterator[DataService]:
        client = OpenF1Client(settings, transport)
        try:
            yield DataService(client, SnapshotStore(tmp_path), settings)
        finally:
            client.close()

    with patch("f1.processing.service.open_service", factory):
        app_path = Path(__file__).resolve().parents[2] / "src/f1/dashboard/app.py"
        app = AppTest.from_file(app_path, default_timeout=30).run()
        assert not app.exception
        assert app.multiselect[0].value == [1, 2]
        for view in ["Comparação", "Estratégia", "Posições", "Clima"]:
            app.radio[0].set_value(view).run()
            assert not app.exception
            assert len(app.get("plotly_chart")) >= 1
        app.multiselect[0].set_value([1]).run()
        assert app.metric[2].value == "1"
        app.selectbox[0].select(2023).run()
        assert not app.exception
        assert app.multiselect[0].value == [1, 2]
        app.multiselect[0].set_value([]).run()
        assert not app.exception
        assert any("Selecione" in message.value for message in app.info)


def test_export_matches_table() -> None:
    frame = pd.DataFrame({"driver_number": [1], "lap_duration": [80.0]})
    with (
        patch("f1.dashboard.views.st.dataframe") as display,
        patch("f1.dashboard.views.st.download_button") as download,
    ):
        table(frame, "selected")
    shown = display.call_args.args[0]
    assert shown["Número"].tolist() == [1]
    assert shown["Tempo de volta (s)"].tolist() == [80.0]
    assert download.call_args.args[1] == shown.to_csv(index=False).encode("utf-8-sig")


def test_charts_are_bound_to_filtered_rows(
    payloads: dict[Endpoint, list[Record]],
) -> None:
    drivers = pd.DataFrame(payloads[Endpoint.DRIVERS])
    names, colors = driver_maps(drivers)
    assert colors[names[1]] == "#FF294C"
    frame = pd.DataFrame(
        {"Piloto": [names[1]], "lap_number": [1], "lap_duration": [80.0]}
    )
    assert len(line_chart(frame, "lap_number", "lap_duration", "Voltas").data) == 1
    stints = pd.DataFrame(
        {"Piloto": [names[1]], "lap_start": [2], "lap_end": [4], "compound": ["SOFT"]}
    )
    figure = stint_chart(stints)
    assert figure.data[0].base[0] == 2
    assert figure.data[0].x[0] == 3
