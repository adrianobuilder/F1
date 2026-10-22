"""Fixtures sinteticas; nenhum dado de teste alimenta a aplicacao real."""

import httpx
import pytest

from f1.domain.models import Endpoint, Record


@pytest.fixture
def payloads() -> dict[Endpoint, list[Record]]:
    """Uma sessao ficticia para validar contratos e interacoes offline."""
    return {
        Endpoint.MEETINGS: [
            {"meeting_key": 1, "meeting_name": "GP de teste", "year": 2024}
        ],
        Endpoint.SESSIONS: [
            {
                "meeting_key": 1,
                "session_key": 2,
                "session_name": "Race",
                "date_start": "2024-01-01T12:00:00Z",
                "date_end": "2024-01-01T14:00:00Z",
                "gmt_offset": "-03:00:00",
                "circuit_short_name": "Circuito teste",
            }
        ],
        Endpoint.DRIVERS: [
            {"driver_number": 1, "full_name": "Piloto Um", "team_colour": "FF294C"},
            {"driver_number": 2, "full_name": "Piloto Dois", "team_colour": "47C8FF"},
        ],
        Endpoint.RESULTS: [
            {"driver_number": 1, "position": 1, "duration": 200.0},
            {"driver_number": 2, "position": 2, "duration": 205.0},
        ],
        Endpoint.LAPS: [
            {
                "driver_number": 1,
                "lap_number": 1,
                "lap_duration": 90.0,
                "is_pit_out_lap": True,
            },
            {
                "driver_number": 1,
                "lap_number": 2,
                "lap_duration": 80.0,
                "duration_sector_1": 20.0,
            },
            {
                "driver_number": 1,
                "lap_number": 3,
                "lap_duration": 82.0,
                "duration_sector_1": 21.0,
            },
            {
                "driver_number": 2,
                "lap_number": 1,
                "lap_duration": 85.0,
                "duration_sector_1": 22.0,
            },
        ],
        Endpoint.STINTS: [
            {
                "driver_number": 1,
                "stint_number": 1,
                "compound": "SOFT",
                "lap_start": 1,
                "lap_end": 3,
                "tyre_age_at_start": 0,
            }
        ],
        Endpoint.PIT: [
            {"driver_number": 1, "date": "2024-01-01T12:30:00Z", "lane_duration": 22.0}
        ],
        Endpoint.POSITION: [
            {"driver_number": 1, "date": "2024-01-01T12:00:00Z", "position": 1}
        ],
        Endpoint.WEATHER: [
            {
                "date": "2024-01-01T12:00:00Z",
                "air_temperature": 27.0,
                "track_temperature": 32.0,
                "humidity": 65.0,
                "wind_speed": 2.0,
                "wind_direction": 90,
                "rainfall": 0,
            }
        ],
    }


@pytest.fixture
def transport(payloads: dict[Endpoint, list[Record]]) -> httpx.MockTransport:
    """Responde por endpoint sem usar rede real."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json=payloads[Endpoint(request.url.path.rsplit("/", 1)[-1])]
        )

    return httpx.MockTransport(handler)
