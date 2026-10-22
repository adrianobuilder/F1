"""Snapshots imutaveis; manifesto atomico e ultimo ponto de publicacao."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import cast
from uuid import uuid4

import pandas as pd

from f1.domain.models import Endpoint, Provenance, Record, StorageError

SCHEMA_VERSION = 1


class SnapshotStore:
    """Persiste geracoes sem sobrescrever o ultimo snapshot valido."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def _manifest(self, endpoint: Endpoint, params: dict[str, int]) -> Path:
        key = "_".join(f"{key}-{value}" for key, value in sorted(params.items()))
        if any(key not in {"year", "session_key"} for key in params) or any(
            not isinstance(value, int) or value < 1 for value in params.values()
        ):
            raise StorageError("Particao de armazenamento invalida.")
        return self.root / "manifests" / endpoint.value / f"{key}.json"

    def read(
        self, endpoint: Endpoint, params: dict[str, int]
    ) -> tuple[pd.DataFrame, Provenance] | None:
        """Le somente geracoes completas da versao de schema atual."""
        manifest_path = self._manifest(endpoint, params)
        if not manifest_path.exists():
            return None
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest["schema_version"] != SCHEMA_VERSION:
                return None
            if manifest["state"] != "complete" or manifest["params"] != params:
                raise ValueError("Manifesto inconsistente")
            target = (self.root / manifest["processed"]).resolve()
            if not target.is_relative_to(self.root):
                raise ValueError("Caminho invalido")
            if self._digest(target) != manifest["sha256"]:
                raise ValueError("Checksum invalido")
            frame = pd.read_parquet(target)
            if len(frame) != manifest["rows"]:
                raise ValueError("Contagem inconsistente")
            return frame, Provenance(datetime.fromisoformat(manifest["collected_at"]))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise StorageError("Snapshot local invalido; atualize os dados.") from exc

    def publish(
        self,
        endpoint: Endpoint,
        params: dict[str, int],
        raw: list[Record],
        frame: pd.DataFrame,
    ) -> Provenance:
        """Publica manifesto somente apos JSON e Parquet completos.

        Uma falha deixa no maximo arquivos orfaos; a geracao anterior permanece
        referenciada. Nao ha garantia de coordenacao entre escritores concorrentes.
        """
        manifest_path = self._manifest(endpoint, params)
        generation = uuid4().hex
        scope = manifest_path.stem
        relative = Path(endpoint.value) / scope / generation
        raw_path = self.root / "raw" / relative.with_suffix(".json")
        processed_path = self.root / "processed" / relative.with_suffix(".parquet")
        collected = datetime.now(UTC)
        temporary = manifest_path.with_suffix(f".{generation}.tmp")
        try:
            for path in (raw_path, processed_path, manifest_path):
                path.parent.mkdir(parents=True, exist_ok=True)
            raw_path.write_text(
                json.dumps(raw, ensure_ascii=False, allow_nan=False), encoding="utf-8"
            )
            frame.to_parquet(processed_path, index=False)
            manifest = {
                "endpoint": endpoint.value,
                "params": params,
                "schema_version": SCHEMA_VERSION,
                "state": "complete",
                "collected_at": collected.isoformat(),
                "rows": len(frame),
                "raw": raw_path.relative_to(self.root).as_posix(),
                "processed": processed_path.relative_to(self.root).as_posix(),
                "sha256": self._digest(processed_path),
            }
            temporary.write_text(json.dumps(manifest), encoding="utf-8")
            temporary.replace(manifest_path)
        except (OSError, ValueError, TypeError) as exc:
            raise StorageError("Nao foi possivel publicar os arquivos locais.") from exc
        finally:
            temporary.unlink(missing_ok=True)
        return Provenance(collected)

    @staticmethod
    def _digest(path: Path) -> str:
        with path.open("rb") as stream:
            return cast(str, hashlib.file_digest(stream, "sha256").hexdigest())
