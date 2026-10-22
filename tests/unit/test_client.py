"""Respostas, tentativas e falhas do adaptador HTTP."""

import httpx
import pytest

from f1.domain.models import Endpoint, SourceError
from f1.ingestion.client import OpenF1Client
from f1.utils.config import Settings


def test_retry_after_and_encoded_params() -> None:
    requests: list[httpx.Request] = []
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return (
            httpx.Response(429, headers={"Retry-After": "2"})
            if len(requests) == 1
            else httpx.Response(200, json=[])
        )

    client = OpenF1Client(Settings(), httpx.MockTransport(handler), sleeps.append)
    try:
        assert client.fetch(Endpoint.LAPS, {"session_key": 2}) == []
        assert sleeps == [2]
        assert requests[0].url.params["session_key"] == "2"
    finally:
        client.close()


@pytest.mark.parametrize("status,attempts", [(401, 1), (404, 1), (500, 3), (503, 3)])
def test_http_failure_attempts(status: int, attempts: int) -> None:
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(status)

    client = OpenF1Client(Settings(), httpx.MockTransport(handler), lambda _: None)
    try:
        with pytest.raises(SourceError):
            client.fetch(Endpoint.WEATHER, {"session_key": 2})
        assert len(requests) == attempts
    finally:
        client.close()


def test_timeout_is_bounded() -> None:
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        raise httpx.ReadTimeout("timeout", request=request)

    client = OpenF1Client(Settings(), httpx.MockTransport(handler), lambda _: None)
    with pytest.raises(SourceError):
        client.fetch(Endpoint.LAPS, {"session_key": 2})
    assert len(requests) == 3
    client.close()


@pytest.mark.parametrize("payload", [{"error": "bad"}, [1], "bad"])
def test_rejects_bad_structure(payload: object) -> None:
    client = OpenF1Client(
        Settings(), httpx.MockTransport(lambda _: httpx.Response(200, json=payload))
    )
    with pytest.raises(SourceError):
        client.fetch(Endpoint.LAPS, {"session_key": 2})
    client.close()
