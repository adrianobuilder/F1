"""Normalizacao deterministica dos nove datasets do MVP."""

import json
import math

import pandas as pd

from f1.domain.models import ContractError, Endpoint, Record

KEYS: dict[Endpoint, list[str]] = {
    Endpoint.MEETINGS: ["meeting_key"],
    Endpoint.SESSIONS: ["session_key"],
    Endpoint.DRIVERS: ["driver_number"],
    Endpoint.RESULTS: ["driver_number"],
    Endpoint.LAPS: ["driver_number", "lap_number"],
    Endpoint.STINTS: ["driver_number", "stint_number"],
    Endpoint.PIT: ["driver_number", "date"],
    Endpoint.POSITION: ["driver_number", "date"],
    Endpoint.WEATHER: ["date"],
}
NUMERIC = {
    "meeting_key",
    "session_key",
    "driver_number",
    "year",
    "lap_number",
    "stint_number",
    "position",
    "lap_duration",
    "duration",
    "number_of_laps",
    "lap_start",
    "lap_end",
    "tyre_age_at_start",
    "lane_duration",
    "stop_duration",
    "pit_duration",
    "air_temperature",
    "track_temperature",
    "humidity",
    "pressure",
    "rainfall",
    "wind_direction",
    "wind_speed",
    "duration_sector_1",
    "duration_sector_2",
    "duration_sector_3",
    "duration_q1",
    "duration_q2",
    "duration_q3",
}


def _flatten(row: Record) -> Record:
    result = dict(row)
    for field in ("duration", "gap_to_leader"):
        value = row.get(field)
        if isinstance(value, list):
            if len(value) != 3:
                raise ContractError(
                    "Resultado de classificacao deve conter Q1, Q2 e Q3."
                )
            for number, item in enumerate(value, 1):
                result[f"{field}_q{number}"] = item
            result[field] = None
    return {
        key: json.dumps(value, sort_keys=True)
        if isinstance(value, (list, dict))
        else value
        for key, value in result.items()
    }


def normalize(endpoint: Endpoint, raw: list[Record]) -> pd.DataFrame:
    """Valida chaves, normaliza datas/tipos e rejeita duplicatas conflitantes.

    Campos nao previstos permanecem no bruto. Arrays nao analiticos sao texto
    JSON no Parquet; duracao e diferencas de classificacao possuem colunas Q1-Q3.
    """
    frame = pd.DataFrame([_flatten(row) for row in raw])
    keys = KEYS[endpoint]
    if frame.empty:
        return pd.DataFrame({key: pd.Series(dtype="object") for key in keys})
    if any(key not in frame or frame[key].isna().any() for key in keys):
        raise ContractError(f"Campos essenciais invalidos em {endpoint.value}.")
    required = {
        Endpoint.MEETINGS: {"meeting_name"},
        Endpoint.SESSIONS: {"meeting_key", "session_name", "date_start", "date_end"},
        Endpoint.POSITION: {"position"},
    }.get(endpoint, set())
    if not required.issubset(frame.columns):
        raise ContractError(f"Schema incompleto em {endpoint.value}.")
    _normalize_types(frame, endpoint)
    _validate_keys(frame, keys)
    if (
        "is_pit_out_lap" in frame
        and not frame["is_pit_out_lap"]
        .dropna()
        .map(lambda value: isinstance(value, bool))
        .all()
    ):
        raise ContractError("Indicador de volta de saida invalido.")
    frame = frame.drop_duplicates()
    if frame.duplicated(keys).any():
        raise ContractError(f"Registros conflitantes em {endpoint.value}.")
    return frame.sort_values(keys).reset_index(drop=True)


def _validate_keys(frame: pd.DataFrame, keys: list[str]) -> None:
    for key in keys:
        if frame[key].isna().any():
            raise ContractError(f"Chave ausente: {key}.")
        if key != "date" and ((frame[key] <= 0).any() or (frame[key] % 1 != 0).any()):
            raise ContractError(f"Identificador invalido: {key}.")


def _normalize_types(frame: pd.DataFrame, endpoint: Endpoint) -> None:
    """Valida numeros finitos e datas antes da verificacao de identidade."""
    try:
        for column in frame.columns:
            if column in {"date", "date_start", "date_end"}:
                frame[column] = pd.to_datetime(
                    frame[column], utc=True, errors="raise", format="ISO8601"
                )
            elif column in NUMERIC:
                frame[column] = pd.to_numeric(frame[column], errors="raise")
                if frame[column].dropna().map(lambda x: not math.isfinite(x)).any():
                    raise ValueError("Numero nao finito")
            elif column.startswith("gap_to_leader"):
                frame[column] = frame[column].astype("string")
    except (ValueError, TypeError, OverflowError) as exc:
        raise ContractError(f"Tipos invalidos em {endpoint.value}.") from exc
