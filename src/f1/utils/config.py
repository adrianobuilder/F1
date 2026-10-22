"""Configuracao validada, sem carregamento implicito de arquivos .env."""

import logging
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Parametros operacionais; caminhos sao relativos ao diretorio de execucao."""

    data_dir: Path = Path("data")
    log_level: str = "INFO"
    timeout: float = 20
    attempts: int = 3
    catalog_ttl_hours: float = 24

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Settings":
        """Le e valida os limites antes de abrir conexoes ou criar arquivos."""
        values = os.environ if env is None else env
        try:
            settings = cls(
                data_dir=Path(values.get("F1_DATA_DIR", "data")),
                log_level=values.get("F1_LOG_LEVEL", "INFO").upper(),
                timeout=float(values.get("F1_HTTP_TIMEOUT", "20")),
                attempts=int(values.get("F1_HTTP_ATTEMPTS", "3")),
                catalog_ttl_hours=float(values.get("F1_CATALOG_TTL_HOURS", "24")),
            )
        except (ValueError, TypeError) as exc:
            raise ValueError("Configuracao F1 numerica invalida") from exc
        if not 0 < settings.timeout <= 120 or not 1 <= settings.attempts <= 3:
            raise ValueError("Timeout deve ser (0,120] e tentativas entre 1 e 3")
        if settings.catalog_ttl_hours <= 0 or settings.log_level not in (
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        ):
            raise ValueError("TTL ou nivel de log invalido")
        return settings

    def logger_level(self) -> int:
        """Converte o nivel validado para a biblioteca padrao."""
        return int(logging.getLevelNamesMapping()[self.log_level])
