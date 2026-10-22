"""Preparacao sob demanda e fallback explicito para snapshots validos."""

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from time import monotonic
from uuid import uuid4

import pandas as pd

from f1.domain.models import Endpoint, F1Error, Provenance, StorageError
from f1.ingestion.client import OpenF1Client
from f1.ingestion.storage import SnapshotStore
from f1.processing.normalize import normalize
from f1.utils.config import Settings

logger = logging.getLogger(__name__)


@dataclass
class Dataset:
    """Tabela e proveniencia que a interface deve apresentar juntas."""

    frame: pd.DataFrame
    provenance: Provenance


class DataService:
    """Coordena cliente e snapshots; nao depende do Streamlit."""

    def __init__(
        self, client: OpenF1Client, store: SnapshotStore, settings: Settings
    ) -> None:
        self.client, self.store, self.settings = client, store, settings

    def dataset(
        self, endpoint: Endpoint, params: dict[str, int], *, refresh: bool = False
    ) -> Dataset:
        """Reutiliza dados completos; atualiza catalogos e preserva fallback."""
        previous = None
        try:
            previous = self.store.read(endpoint, params)
        except StorageError:
            logger.warning("snapshot_unreadable", extra={"endpoint": endpoint.value})
        catalog = endpoint in {Endpoint.MEETINGS, Endpoint.SESSIONS}
        if previous and not refresh:
            frame, provenance = previous
            expired = catalog and datetime.now(
                UTC
            ) - provenance.collected_at > timedelta(
                hours=self.settings.catalog_ttl_hours
            )
            if not expired:
                return Dataset(frame, provenance)
        run_id, started = uuid4().hex, monotonic()
        context = {"run_id": run_id, "endpoint": endpoint.value}
        logger.info("dataset_started", extra=context)
        try:
            raw = self.client.fetch(endpoint, params)
            frame = normalize(endpoint, raw)
            if (
                "session_key" in params
                and "session_key" in frame
                and not frame["session_key"].eq(params["session_key"]).all()
            ):
                raise F1Error("A resposta inclui outra sessao.")
            provenance = self.store.publish(endpoint, params, raw, frame)
        except F1Error:
            logger.exception("dataset_failed", extra=context)
            if previous is None:
                raise
            frame, provenance = previous
            return Dataset(
                frame,
                replace(
                    provenance,
                    stale=True,
                    warning="Atualizacao falhou. Exibindo o ultimo snapshot valido.",
                ),
            )
        logger.info(
            "dataset_completed",
            extra={
                **context,
                "rows": len(frame),
                "duration_seconds": monotonic() - started,
            },
        )
        return Dataset(frame, provenance)


@contextmanager
def open_service(settings: Settings) -> Iterator[DataService]:
    """Abre e fecha adaptadores no limite de uma execucao da interface."""
    client = OpenF1Client(settings)
    try:
        yield DataService(client, SnapshotStore(settings.data_dir), settings)
    finally:
        client.close()
