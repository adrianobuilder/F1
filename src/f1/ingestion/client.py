"""Cliente sincrono restrito a consultas GET da OpenF1."""

import random
import time
from collections.abc import Callable
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import cast

import httpx

from f1.domain.models import Endpoint, Record, SourceError
from f1.utils.config import Settings


class OpenF1Client:
    """Reutiliza conexoes e limita tentativas de falhas transitorias."""

    def __init__(
        self,
        settings: Settings,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.settings = settings
        self.sleep = sleep
        self.http = httpx.Client(
            base_url="https://api.openf1.org/v1/",
            timeout=settings.timeout,
            transport=transport,
            headers={"User-Agent": "f1-historical-dashboard/0.1"},
        )

    def close(self) -> None:
        """Libera conexoes do cliente."""
        self.http.close()

    def fetch(self, endpoint: Endpoint, params: dict[str, int]) -> list[Record]:
        """Retorna objetos JSON ou falha explicitamente, inclusive em HTTP 4xx.

        Args:
            endpoint: Recurso permitido pelo dominio.
            params: Filtros de temporada ou sessao.

        Raises:
            SourceError: Em falha de rede, HTTP ou estrutura JSON invalida.
        """
        for attempt in range(self.settings.attempts):
            try:
                response = self.http.get(endpoint.value, params=params)
            except httpx.TransportError as exc:
                if attempt + 1 == self.settings.attempts:
                    raise SourceError(
                        "A OpenF1 nao respondeu. Tente novamente."
                    ) from exc
                self.sleep(2**attempt + random.uniform(0, 0.5))
                continue
            if (
                response.status_code in {429, 500, 502, 503, 504}
                and attempt + 1 < self.settings.attempts
            ):
                self.sleep(self._delay(response, attempt))
                continue
            try:
                response.raise_for_status()
                payload = response.json()
            except (httpx.HTTPStatusError, ValueError) as exc:
                raise SourceError(
                    f"Consulta OpenF1 falhou ({response.status_code})."
                ) from exc
            if not isinstance(payload, list) or any(
                not isinstance(row, dict) for row in payload
            ):
                raise SourceError("A OpenF1 retornou um formato inesperado.")
            return cast(list[Record], payload)
        raise SourceError("Consulta OpenF1 indisponivel.")

    @staticmethod
    def _delay(response: httpx.Response, attempt: int) -> float:
        value = response.headers.get("Retry-After", "")
        try:
            delay = float(value)
        except ValueError:
            try:
                delay = (
                    parsedate_to_datetime(value) - datetime.now(UTC)
                ).total_seconds()
            except (TypeError, ValueError, OverflowError):
                delay = 2**attempt + random.uniform(0, 0.5)
        if delay > 60:
            raise SourceError("Limite da OpenF1 atingido. Aguarde antes de atualizar.")
        return max(0, delay)
