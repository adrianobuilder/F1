"""Contratos da integracao e erros publicos da aplicacao."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

type JsonValue = (
    str | int | float | bool | list[JsonValue] | dict[str, JsonValue] | None
)
type Record = dict[str, JsonValue]


class Endpoint(StrEnum):
    """Recursos suportados pelo MVP historico."""

    MEETINGS = "meetings"
    SESSIONS = "sessions"
    DRIVERS = "drivers"
    RESULTS = "session_result"
    LAPS = "laps"
    STINTS = "stints"
    PIT = "pit"
    POSITION = "position"
    WEATHER = "weather"


class F1Error(Exception):
    """Falha operacional que pode ser apresentada sem traceback ao usuario."""


class SourceError(F1Error):
    """A fonte nao forneceu uma resposta utilizavel."""


class ContractError(F1Error):
    """Os dados recebidos violam o contrato do dataset."""


class StorageError(F1Error):
    """Nao foi possivel ler ou publicar um dataset local."""


@dataclass(frozen=True)
class Provenance:
    """Origem e estado de atualizacao do dataset apresentado."""

    collected_at: datetime
    stale: bool = False
    warning: str | None = None
