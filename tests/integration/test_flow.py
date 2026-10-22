"""Fluxo HTTP simulado para arquivos e calculos reais."""

from pathlib import Path

import httpx
import pytest

from f1.domain.models import Endpoint
from f1.ingestion.client import OpenF1Client
from f1.ingestion.storage import SnapshotStore
from f1.processing.analytics import lap_summary
from f1.processing.service import DataService
from f1.utils.config import Settings


@pytest.mark.integration
def test_json_parquet_analytics_and_offline_reload(
    tmp_path: Path, transport: httpx.MockTransport
) -> None:
    settings = Settings(data_dir=tmp_path)
    client = OpenF1Client(settings, transport)
    service = DataService(client, SnapshotStore(tmp_path), settings)
    dataset = service.dataset(Endpoint.LAPS, {"session_key": 2})
    assert lap_summary(dataset.frame, [1]).iloc[0]["mean_lap"] == 81
    assert list((tmp_path / "raw").rglob("*.json"))
    assert list((tmp_path / "processed").rglob("*.parquet"))
    client.close()
    offline = OpenF1Client(
        settings,
        httpx.MockTransport(lambda _: pytest.fail("Rede nao deve ser consultada")),
    )
    reloaded = DataService(offline, SnapshotStore(tmp_path), settings).dataset(
        Endpoint.LAPS, {"session_key": 2}
    )
    assert reloaded.provenance == dataset.provenance
    assert len(reloaded.frame) == len(dataset.frame)
    offline.close()
