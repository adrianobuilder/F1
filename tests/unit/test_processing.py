"""Contratos e regras de calculo sem efeitos colaterais."""

from datetime import UTC, datetime

import pandas as pd
import pytest

from f1.domain.models import ContractError, Endpoint, Record
from f1.processing.analytics import (
    completed_sessions,
    default_drivers,
    event_time,
    format_lap,
    lap_series,
    lap_summary,
    localize_times,
)
from f1.processing.normalize import normalize
from f1.utils.config import Settings


def test_lap_metrics_exclude_outlaps_missing_and_zero(
    payloads: dict[Endpoint, list[Record]],
) -> None:
    rows = payloads[Endpoint.LAPS] + [
        {"driver_number": 1, "lap_number": 4, "lap_duration": None},
        {"driver_number": 1, "lap_number": 5, "lap_duration": 0},
    ]
    result = lap_summary(normalize(Endpoint.LAPS, rows), [1]).iloc[0]
    assert result["best_lap"] == 80
    assert result["mean_lap"] == 81
    assert result["laps"] == 2


def test_qualifying_arrays_and_raw_unchanged() -> None:
    raw: list[Record] = [
        {
            "driver_number": 1,
            "duration": [80.0, 79.0, None],
            "gap_to_leader": [0, 0.5, None],
        }
    ]
    frame = normalize(Endpoint.RESULTS, raw)
    assert frame.iloc[0]["duration_q2"] == 79
    assert pd.isna(frame.iloc[0]["duration_q3"])
    assert raw[0]["duration"] == [80.0, 79.0, None]


def test_duplicate_identity_and_conflict() -> None:
    row: Record = {"driver_number": 1, "lap_number": 1, "lap_duration": 90}
    assert len(normalize(Endpoint.LAPS, [row, row])) == 1
    with pytest.raises(ContractError, match="conflitantes"):
        normalize(Endpoint.LAPS, [row, {**row, "lap_duration": 91}])


@pytest.mark.parametrize(
    "row",
    [
        {"driver_number": None, "lap_number": 1},
        {"driver_number": -1, "lap_number": 1},
        {"driver_number": "bad", "lap_number": 1},
        {"driver_number": 1, "lap_number": 1, "lap_duration": "NaN"},
    ],
)
def test_bad_essential_values(row: Record) -> None:
    with pytest.raises(ContractError):
        normalize(Endpoint.LAPS, [row])


def test_empty_is_valid() -> None:
    assert normalize(Endpoint.PIT, []).empty
    assert lap_summary(pd.DataFrame(), []).empty


def test_mixed_iso_precision_is_valid() -> None:
    frame = normalize(
        Endpoint.WEATHER,
        [
            {"date": "2023-09-17T12:29:38.500000+00:00"},
            {"date": "2023-09-17T12:29:39+00:00"},
        ],
    )
    assert len(frame) == 2
    assert str(frame["date"].dt.tz) == "UTC"


def test_invalid_catalog_and_null_date_do_not_publish() -> None:
    with pytest.raises(ContractError, match="Schema"):
        normalize(Endpoint.MEETINGS, [{"meeting_key": 1}])
    with pytest.raises(ContractError):
        normalize(Endpoint.WEATHER, [{"date": "NaT"}])


def test_missing_laps_remain_gaps_in_chart() -> None:
    frame = normalize(
        Endpoint.LAPS,
        [
            {"driver_number": 1, "lap_number": 1, "lap_duration": 90},
            {"driver_number": 1, "lap_number": 3, "lap_duration": 92},
        ],
    )
    series = lap_series(frame, [1])
    assert series["lap_number"].tolist() == [1, 2, 3]
    assert pd.isna(series.iloc[1]["lap_duration"])


def test_ended_sessions_and_default_drivers(
    payloads: dict[Endpoint, list[Record]],
) -> None:
    sessions = normalize(Endpoint.SESSIONS, payloads[Endpoint.SESSIONS])
    assert len(completed_sessions(sessions, datetime(2025, 1, 1, tzinfo=UTC))) == 1
    assert completed_sessions(sessions, datetime(2023, 1, 1, tzinfo=UTC)).empty
    sessions["is_cancelled"] = True
    assert completed_sessions(sessions).empty
    assert default_drivers(
        pd.DataFrame(payloads[Endpoint.DRIVERS]),
        pd.DataFrame(payloads[Endpoint.RESULTS]),
    ) == [1, 2]


def test_times_are_local_copies() -> None:
    frame = pd.DataFrame({"date": pd.to_datetime(["2024-01-01T12:00:00Z"])})
    result = localize_times(frame, "-03:00:00")
    assert result.iloc[0]["date"].hour == 9
    assert frame.iloc[0]["date"].hour == 12
    assert "09:00" in event_time(frame.iloc[0]["date"], "-03:00:00")
    assert format_lap(80.123) == "1:20.123"


@pytest.mark.parametrize(
    "env",
    [
        {"F1_HTTP_ATTEMPTS": "9"},
        {"F1_HTTP_TIMEOUT": "bad"},
        {"F1_CATALOG_TTL_HOURS": "0"},
        {"F1_LOG_LEVEL": "BOGUS"},
    ],
)
def test_config_rejects_invalid(env: dict[str, str]) -> None:
    with pytest.raises(ValueError):
        Settings.from_env(env)
