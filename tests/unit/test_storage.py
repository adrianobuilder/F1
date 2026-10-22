"""Garantias da publicacao e preservacao do snapshot anterior."""

import json
from pathlib import Path
from unittest.mock import patch

import httpx
import pandas as pd
import pytest

from f1.domain.models import Endpoint, StorageError
from f1.ingestion.client import OpenF1Client
from f1.ingestion.storage import SnapshotStore
from f1.processing.normalize import normalize
from f1.processing.service import DataService
from f1.utils.config import Settings


def test_idempotence_and_failed_publish(tmp_path: Path) -> None:
    store = SnapshotStore(tmp_path)
    raw = [{"driver_number": 1}]
    frame = normalize(Endpoint.DRIVERS, raw)
    params = {"session_key": 2}
    store.publish(Endpoint.DRIVERS, params, raw, frame)
    store.publish(Endpoint.DRIVERS, params, raw, frame)
    assert len(store.read(Endpoint.DRIVERS, params)[0]) == 1
    with (
        patch.object(pd.DataFrame, "to_parquet", side_effect=OSError("disk")),
        pytest.raises(StorageError),
    ):
        store.publish(Endpoint.DRIVERS, params, raw, frame)
    assert len(store.read(Endpoint.DRIVERS, params)[0]) == 1


def test_corrupt_files_detected(tmp_path: Path) -> None:
    store = SnapshotStore(tmp_path)
    store.publish(
        Endpoint.WEATHER, {"session_key": 2}, [], normalize(Endpoint.WEATHER, [])
    )
    next(tmp_path.rglob("*.parquet")).write_bytes(b"broken")
    with pytest.raises(StorageError):
        store.read(Endpoint.WEATHER, {"session_key": 2})


def test_service_offline_fallback_and_cache(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path)
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return (
            httpx.Response(200, json=[{"driver_number": 1}])
            if len(calls) == 1
            else httpx.Response(400)
        )

    client = OpenF1Client(settings, httpx.MockTransport(handler))
    service = DataService(client, SnapshotStore(tmp_path), settings)
    first = service.dataset(Endpoint.DRIVERS, {"session_key": 2})
    service.dataset(Endpoint.DRIVERS, {"session_key": 2})
    assert len(calls) == 1
    fallback = service.dataset(Endpoint.DRIVERS, {"session_key": 2}, refresh=True)
    assert fallback.provenance.stale
    assert fallback.provenance.collected_at == first.provenance.collected_at
    pd.testing.assert_frame_equal(first.frame, fallback.frame)
    client.close()


def test_expired_catalog_refreshes(tmp_path: Path) -> None:
    store = SnapshotStore(tmp_path)
    store.publish(
        Endpoint.MEETINGS, {"year": 2024}, [], normalize(Endpoint.MEETINGS, [])
    )
    manifest_path = next((tmp_path / "manifests").rglob("*.json"))
    manifest = json.loads(manifest_path.read_text())
    manifest["collected_at"] = "2020-01-01T00:00:00+00:00"
    manifest_path.write_text(json.dumps(manifest))
    client = OpenF1Client(
        Settings(), httpx.MockTransport(lambda _: httpx.Response(200, json=[]))
    )
    service = DataService(client, store, Settings())
    assert (
        service.dataset(Endpoint.MEETINGS, {"year": 2024}).provenance.collected_at.year
        > 2020
    )
    client.close()
