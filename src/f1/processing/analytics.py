"""Calculos puros compartilhados entre interface e testes."""

from datetime import UTC, datetime, timedelta, timezone

import pandas as pd


def completed_sessions(
    sessions: pd.DataFrame, now: datetime | None = None
) -> pd.DataFrame:
    """Seleciona sessoes encerradas e nao canceladas, mais recentes primeiro."""
    if sessions.empty or "date_end" not in sessions:
        return sessions.iloc[:0].copy()
    end = pd.to_datetime(sessions["date_end"], utc=True, errors="coerce")
    cancelled = sessions.get("is_cancelled", pd.Series(False, index=sessions.index))
    mask = (end <= (now or datetime.now(UTC))) & ~cancelled.fillna(False).astype(bool)
    return sessions.loc[mask].sort_values("date_end", ascending=False).copy()


def filter_drivers(frame: pd.DataFrame, drivers: list[int]) -> pd.DataFrame:
    """Aplica a mesma populacao usada em graficos, tabelas e exportacao."""
    if frame.empty or "driver_number" not in frame:
        return frame.copy()
    return frame.loc[frame["driver_number"].isin(drivers)].copy()


def valid_laps(laps: pd.DataFrame, drivers: list[int]) -> pd.DataFrame:
    """Exclui tempos nulos/nao positivos e voltas de saida dos boxes."""
    frame = filter_drivers(laps, drivers)
    if "lap_duration" not in frame:
        return frame.iloc[:0]
    pit_out = frame.get("is_pit_out_lap", pd.Series(False, index=frame.index))
    return frame.loc[
        frame["lap_duration"].gt(0) & ~pit_out.astype("boolean").fillna(False)
    ].copy()


def lap_summary(laps: pd.DataFrame, drivers: list[int]) -> pd.DataFrame:
    """Melhor volta, media e quantidade das voltas consideradas por piloto."""
    frame = valid_laps(laps, drivers)
    if frame.empty:
        return pd.DataFrame(columns=["driver_number", "best_lap", "mean_lap", "laps"])
    return (
        frame.groupby("driver_number", as_index=False)
        .agg(
            best_lap=("lap_duration", "min"),
            mean_lap=("lap_duration", "mean"),
            laps=("lap_duration", "count"),
        )
        .sort_values("best_lap")
    )


def lap_series(laps: pd.DataFrame, drivers: list[int]) -> pd.DataFrame:
    """Preserva lacunas de voltas ausentes ou excluidas nos graficos."""
    frame = filter_drivers(laps, drivers)
    if frame.empty or "lap_duration" not in frame:
        return frame.iloc[:0]
    pit_out = frame.get("is_pit_out_lap", pd.Series(False, index=frame.index))
    valid = frame["lap_duration"].gt(0) & ~pit_out.astype("boolean").fillna(False)
    durations = [
        column for column in frame if str(column).startswith("duration_sector_")
    ]
    for column in ["lap_duration", *durations]:
        frame[column] = frame[column].where(valid)
    groups = []
    for number, group in frame.groupby("driver_number"):
        first, last = int(group["lap_number"].min()), int(group["lap_number"].max())
        indexed = group.set_index("lap_number").reindex(range(first, last + 1))
        indexed["driver_number"] = number
        indexed.index.name = "lap_number"
        groups.append(indexed.reset_index())
    return pd.concat(groups, ignore_index=True)


def default_drivers(drivers: pd.DataFrame, results: pd.DataFrame) -> list[int]:
    """Prefere os dois primeiros classificados presentes na lista de pilotos."""
    available = [int(value) for value in drivers.get("driver_number", [])]
    ranked = results.sort_values("position") if "position" in results else results
    candidates = [int(value) for value in ranked.get("driver_number", [])]
    return [
        value for value in dict.fromkeys(candidates + available) if value in available
    ][:2]


def event_time(value: object, offset: str) -> str:
    """Formata um instante no deslocamento UTC fornecido pelo evento."""
    try:
        sign = -1 if offset.startswith("-") else 1
        hours, minutes, *_ = offset.lstrip("+-").split(":")
        tz = timezone(sign * timedelta(hours=int(hours), minutes=int(minutes)))
        timestamp = pd.Timestamp(str(value))
        if timestamp.tzinfo is None:
            timestamp = timestamp.tz_localize("UTC")
        return timestamp.tz_convert(tz).strftime("%d/%m/%Y %H:%M (UTC%z)")
    except (ValueError, TypeError):
        return "Horario indisponivel"


def format_lap(value: float) -> str:
    """Formata segundos como minutos, segundos e milissegundos."""
    milliseconds = round(value * 1000)
    minutes, remainder = divmod(milliseconds, 60000)
    seconds, millis = divmod(remainder, 1000)
    return f"{minutes}:{seconds:02d}.{millis:03d}"


def localize_times(frame: pd.DataFrame, offset: str) -> pd.DataFrame:
    """Converte somente a copia de apresentacao; armazenamento permanece UTC."""
    result = frame.copy()
    sign = -1 if offset.startswith("-") else 1
    try:
        hours, minutes, *_ = offset.lstrip("+-").split(":")
        tz = timezone(sign * timedelta(hours=int(hours), minutes=int(minutes)))
    except (ValueError, TypeError):
        tz = UTC
    for column in ("date", "date_start", "date_end"):
        if column in result:
            result[column] = pd.to_datetime(result[column], utc=True).dt.tz_convert(tz)
    return result
