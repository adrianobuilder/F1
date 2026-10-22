# Exemplos — Engenharia de Dados com Python

Leia ao configurar um projeto ou implementar um pipeline. Estes blocos formam um projeto mínimo coerente chamado **nome-projeto**, importado como **nome_projeto**. Copie cada bloco para o caminho indicado somente ao criar o projeto correspondente; não sobrescreva configuração existente sem adaptação.

As versões abaixo foram consultadas no PyPI e nos repositórios oficiais em **22/10/2026**. Os limites permitem correções compatíveis; a resolução exata deve ser gerada pelo Poetry e versionada em `poetry.lock`. Revalidar compatibilidade ao atualizar. O exemplo usa Python 3.12, sem impor essa versão a todos os projetos existentes.

## 1. `pyproject.toml`

O projeto de exemplo usa apenas biblioteca padrão em produção. Os grupos opcionais são instalados explicitamente. `pytest` executa somente os unitários por padrão; a integração é executada por caminho explícito.

```toml
[project]
name = "nome-projeto"
version = "0.1.0"
description = "Pipeline CSV para JSON com contratos explicitos"
authors = [{name = "Time de Engenharia de Dados"}]
readme = "README.md"
requires-python = ">=3.12,<3.13"
dependencies = []

[tool.poetry]
packages = [{include = "nome_projeto", from = "src"}]

[tool.poetry.group.dev]
optional = true

[tool.poetry.group.dev.dependencies]
ruff = ">=0.17.2,<0.18"
mypy = ">=2.4.0,<3"
pip-audit = ">=2.10.1,<3"

[tool.poetry.group.test]
optional = true

[tool.poetry.group.test.dependencies]
pytest = ">=9.1.1,<10"
pytest-cov = ">=7.1.0,<8"

[tool.poetry.group.docs]
optional = true

[tool.poetry.group.docs.dependencies]
mkdocs = ">=1.6.1,<2"
mkdocs-material = ">=9.7.7,<10"
mkdocstrings = {version = ">=1.0.8,<2", extras = ["python"]}

[build-system]
requires = ["poetry-core>=2.5.0,<3"]
build-backend = "poetry.core.masonry.api"

[tool.ruff]
target-version = "py312"
line-length = 88
src = ["src"]

[tool.ruff.lint]
select = ["E4", "E7", "E9", "F", "I", "B", "UP", "SIM", "C90", "RUF"]

[tool.ruff.lint.mccabe]
max-complexity = 10

[tool.ruff.lint.isort]
known-first-party = ["nome_projeto"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
docstring-code-format = true

[tool.pytest.ini_options]
minversion = "9.1"
testpaths = ["tests/unit"]
addopts = "--strict-markers --strict-config --cov=nome_projeto --cov-report=term-missing --cov-fail-under=50"
markers = ["integration: requer infraestrutura externa ou multiplas fronteiras reais"]

[tool.coverage.run]
source = ["nome_projeto"]
branch = false

[tool.coverage.report]
fail_under = 50
show_missing = true
precision = 2

[tool.mypy]
python_version = "3.12"
files = ["src"]
strict = true
```

Não adicionar `omit` para esconder módulos difíceis. `pytest --cov` usa o pacote instalado pelo Poetry e inclui módulos de produção não exercitados. O piso mede linhas porque `branch = false`.

## 2. Configuração segura

### `.env.example`

```dotenv
APP_ENV=development
INPUT_PATH=data/input.csv
OUTPUT_PATH=data/output.json
```

### `src/nome_projeto/utils/config.py`

```python
"""Configuracao validada a partir do ambiente."""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Caminhos locais da execucao."""

    input_path: Path
    output_path: Path

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> "Settings":
        """Carrega caminhos obrigatorios sem depender de estado global.

        Args:
            env: Variaveis exportadas pelo ambiente de execucao.

        Returns:
            Configuracao validada.

        Raises:
            ValueError: Se houver caminho ausente ou destino igual a origem.
        """
        source = env.get("INPUT_PATH", "").strip()
        target = env.get("OUTPUT_PATH", "").strip()
        if not source or not target:
            raise ValueError("INPUT_PATH e OUTPUT_PATH sao obrigatorios")
        input_path, output_path = Path(source), Path(target)
        if input_path.resolve() == output_path.resolve():
            raise ValueError("Origem e destino devem ser diferentes")
        return cls(input_path=input_path, output_path=output_path)
```

Na entrada da aplicação, usar `Settings.from_env(os.environ)`. Exportar variáveis pelo shell/runner; copiar `.env.example` não carrega variáveis automaticamente. Configurações de bancos/APIs devem validar campos essenciais sem incluir valores secretos nos erros.

## 3. Domínio e transformação tipados

### `src/nome_projeto/domain/sale.py`

```python
"""Contrato de dominio independente de infraestrutura."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Sale:
    """Venda identificada por chave de negocio e valor decimal."""

    sale_id: str
    amount: Decimal
```

### `src/nome_projeto/processing/sales.py`

```python
"""Validacao e normalizacao deterministica de vendas."""

from collections.abc import Iterable, Mapping
from decimal import Decimal, InvalidOperation

from nome_projeto.domain.sale import Sale


def parse_sale(row: Mapping[str, str | None]) -> Sale:
    """Valida uma linha externa antes de aplica-la ao dominio.

    Args:
        row: Campos sale_id e amount; decimal separado por ponto.

    Returns:
        Venda valida, sem conversao para ponto flutuante.

    Raises:
        ValueError: Se a chave estiver vazia ou o valor for invalido/negativo.
    """
    sale_id = (row.get("sale_id") or "").strip()
    if not sale_id:
        raise ValueError("sale_id obrigatorio")
    try:
        amount = Decimal(row.get("amount") or "")
    except InvalidOperation as exc:
        raise ValueError("amount deve ser decimal") from exc
    if not amount.is_finite() or amount < 0:
        raise ValueError("amount deve ser finito e nao negativo")
    return Sale(sale_id=sale_id, amount=amount)


def normalize_sales(rows: Iterable[Mapping[str, str | None]]) -> list[Sale]:
    """Remove duplicatas identicas, rejeita conflitos e ordena por chave.

    Args:
        rows: Linhas externas de uma particao pequena.

    Returns:
        Vendas unicas em ordem deterministica de identificador.

    Raises:
        ValueError: Se houver linha invalida ou valores conflitantes na chave.
    """
    unique: dict[str, Sale] = {}
    for row in rows:
        sale = parse_sale(row)
        if sale.sale_id in unique and unique[sale.sale_id] != sale:
            raise ValueError("Valores conflitantes para a mesma chave")
        unique[sale.sale_id] = sale
    return [unique[key] for key in sorted(unique)]
```

O contrato em `domain/sale.py` mantém identificadores como texto e valores como `Decimal`. A transformação em `processing/sales.py` valida dados externos sem arredondar nem preencher nulos implicitamente. Adaptadores e processamento dependem desse contrato, sem dependência do domínio em relação à infraestrutura.

## 4. Pipeline ETL

Criar `__init__.py` em `src/nome_projeto/` e em suas camadas `ingestion/`, `processing/`, `domain/` e `utils/`. Criar também `tests/__init__.py`, `tests/unit/__init__.py` e `tests/integration/__init__.py`. Os arquivos podem conter apenas uma docstring. Criar `README.md`, requerido pelo empacotamento. Criar `conftest.py` somente quando houver fixtures compartilhadas.

### `src/nome_projeto/ingestion/csv_sales.py`

```python
"""Extracao de CSV UTF-8 com contrato de cabecalho."""

import csv
from collections.abc import Generator
from pathlib import Path


def read_rows(path: Path) -> Generator[dict[str, str | None], None, None]:
    """Le linhas; rejeita cabecalho e quantidade de colunas invalidos."""
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter=",")
        if reader.fieldnames != ["sale_id", "amount"]:
            raise ValueError("Cabecalho esperado: sale_id,amount")
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError("Quantidade de colunas invalida")
            yield {"sale_id": row["sale_id"], "amount": row["amount"]}
```

### `src/nome_projeto/ingestion/json_sales.py`

```python
"""Publicacao local por substituicao atomica."""

import json
from collections.abc import Sequence
from pathlib import Path
from tempfile import NamedTemporaryFile

from nome_projeto.domain.sale import Sale


def write_sales(sales: Sequence[Sale], target: Path) -> None:
    """Publica JSON completo; remove temporario se a escrita falhar."""
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=target.parent, delete=False
        ) as stream:
            temporary = Path(stream.name)
            json.dump(
                [
                    {"sale_id": sale.sale_id, "amount": str(sale.amount)}
                    for sale in sales
                ],
                stream,
                ensure_ascii=False,
            )
            stream.write("\n")
        temporary.replace(target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
```

### `src/nome_projeto/processing/pipeline.py`

```python
"""Composicao das etapas sem configurar handlers de logging."""

import logging
from contextlib import closing
from pathlib import Path
from time import monotonic

from nome_projeto.ingestion.csv_sales import read_rows
from nome_projeto.ingestion.json_sales import write_sales
from nome_projeto.processing.sales import normalize_sales

logger = logging.getLogger(__name__)


def run_pipeline(source: Path, target: Path, *, run_id: str) -> int:
    """Executa ETL de uma particao pequena e retorna quantidade publicada."""
    if source.resolve() == target.resolve():
        raise ValueError("Origem e destino devem ser diferentes")
    started = monotonic()
    logger.info("pipeline_started", extra={"run_id": run_id, "stage": "extract"})
    with closing(read_rows(source)) as rows:
        sales = normalize_sales(rows)
    logger.info("transform_completed", extra={"run_id": run_id, "rows_out": len(sales)})
    write_sales(sales, target)
    logger.info(
        "pipeline_completed",
        extra={
            "run_id": run_id,
            "rows_out": len(sales),
            "duration_seconds": monotonic() - started,
        },
    )
    return len(sales)
```

Na entrada operacional, configurar logging e serialização de `extra`, gerar `run_id`, carregar `Settings`, chamar `run_pipeline` e registrar uma falha terminal com `logger.exception` antes de encerrar com status diferente de zero. Não capturar falhas para retornar sucesso.

**Limites explícitos:** este exemplo processa uma partição pequena em memória e substitui todo o destino. Reexecutar a mesma entrada produz o mesmo conteúdo lógico, sem append duplicado. Não é implementação incremental, não possui checkpoint e não resolve escritores concorrentes. A substituição pressupõe filesystem local com semântica de rename no mesmo volume; não promete durabilidade após queda de energia ou atomicidade em object storage. Para maior volume, deduplicar por partições/lotes ou no banco, publicar por transação/manifesto e só então avançar o checkpoint. `closing` fecha o gerador mesmo em falha de transformação.

## 5. Testes unitários correspondentes

### `tests/unit/test_sales.py`

```python
"""Contratos, conflitos, idempotencia e preservacao do destino."""

import json
from decimal import Decimal
from pathlib import Path

import pytest

from nome_projeto.processing.pipeline import run_pipeline
from nome_projeto.processing.sales import normalize_sales, parse_sale
from nome_projeto.utils.config import Settings


@pytest.mark.parametrize("amount", [None, "", "abc", "-1", "NaN", "Infinity"])
def test_rejects_invalid_amount(amount: str | None) -> None:
    with pytest.raises(ValueError):
        parse_sale({"sale_id": "001", "amount": amount})


@pytest.mark.parametrize("sale_id", [None, "", " "])
def test_requires_sale_id(sale_id: str | None) -> None:
    with pytest.raises(ValueError, match="sale_id"):
        parse_sale({"sale_id": sale_id, "amount": "0"})


def test_preserves_identifier_and_decimal() -> None:
    sale = parse_sale({"sale_id": "001", "amount": "0.10"})
    assert sale.sale_id == "001"
    assert sale.amount == Decimal("0.10")


def test_deduplicates_and_sorts() -> None:
    rows = [
        {"sale_id": "002", "amount": "2"},
        {"sale_id": "001", "amount": "1"},
        {"sale_id": "001", "amount": "1"},
    ]
    assert [sale.sale_id for sale in normalize_sales(rows)] == ["001", "002"]


def test_rejects_conflicting_duplicates() -> None:
    with pytest.raises(ValueError, match="conflitantes"):
        normalize_sales(
            [{"sale_id": "001", "amount": "1"}, {"sale_id": "001", "amount": "2"}]
        )


def test_pipeline_reexecution_is_idempotent(tmp_path: Path) -> None:
    source = tmp_path / "input.csv"
    target = tmp_path / "output.json"
    source.write_text("sale_id,amount\n001,0.10\n001,0.10\n", encoding="utf-8")
    assert run_pipeline(source, target, run_id="first") == 1
    initial = target.read_bytes()
    assert run_pipeline(source, target, run_id="second") == 1
    assert target.read_bytes() == initial
    assert json.loads(initial) == [{"sale_id": "001", "amount": "0.10"}]


@pytest.mark.parametrize("content", ["bad,header\n", "sale_id,amount\n001,invalid\n"])
def test_invalid_input_preserves_destination(tmp_path: Path, content: str) -> None:
    source = tmp_path / "input.csv"
    target = tmp_path / "output.json"
    source.write_text(content, encoding="utf-8")
    target.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError):
        run_pipeline(source, target, run_id="failure")
    assert target.read_text(encoding="utf-8") == "[]"


def test_settings_require_paths() -> None:
    with pytest.raises(ValueError, match="obrigatorios"):
        Settings.from_env({})
```

Estes testes usam filesystem temporário local, sem serviços externos, e pertencem à suíte unitária. Integrações reais devem ficar em `tests/integration/` com `@pytest.mark.integration`. Adicionar testes de falha no carregamento e recuperação conforme o destino real, sem presumir que apenas este exemplo cobre todos os riscos operacionais.

## 6. MkDocs Material

### `docs/mkdocs.yml`

```yaml
site_name: Nome Projeto
theme:
  name: material
  language: pt-BR
plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          options:
            docstring_style: google
nav:
  - Inicio: index.md
  - Arquitetura: architecture.md
  - Estrutura do Projeto: project-structure.md
  - Execucao Local: running-locally.md
  - Testes: running-tests.md
  - Contribuicao: contributing.md
  - Referencia Python: reference.md
```

Criar as sete páginas em `docs/docs/` antes do build. `index.md` apresenta objetivos e escopo; `architecture.md` descreve camadas e dependências; `project-structure.md` explica diretórios; `running-locally.md` cobre Poetry, configuração, variáveis, execução das pipelines e troubleshooting; `running-tests.md` descreve testes e cobertura; `contributing.md` cobre padrões, Git e revisão. `reference.md` gera a referência Python. O `docs_dir` padrão é relativo a `docs/mkdocs.yml`, portanto aponta para `docs/docs/`. Os módulos são localizados pelo pacote instalado com Poetry, sem manipular `sys.path`.

### `docs/docs/reference.md`

```markdown
# Referencia Python

::: nome_projeto.processing.sales

::: nome_projeto.processing.pipeline
```

```bash
poetry run mkdocs serve -f docs/mkdocs.yml
poetry run mkdocs build --strict -f docs/mkdocs.yml
```

## 7. GitHub Actions — `.github/workflows/quality.yml`

As versões major foram conferidas nos releases oficiais; em ambientes com exigência de supply chain, substituir tags por SHAs completos revisados e configurar atualização automática. O runner hospedado fornece suporte ao runtime das actions; runners próprios precisam respeitar os requisitos das versões utilizadas.

```yaml
name: Quality
on:
  pull_request:
  push:
    branches: [main]
permissions:
  contents: read
jobs:
  quality:
    name: quality
    runs-on: ubuntu-latest
    timeout-minutes: 15
    env:
      POETRY_VERSION: "2.5.1"
      POETRY_VIRTUALENVS_IN_PROJECT: "true"
      POETRY_NO_INTERACTION: "1"
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: "3.12"
      - name: Instalar Poetry isoladamente
        shell: bash
        run: |
          curl --fail --silent --show-error --location https://install.python-poetry.org -o /tmp/install-poetry.py
          python /tmp/install-poetry.py --version "$POETRY_VERSION"
          echo "$HOME/.local/bin" >> "$GITHUB_PATH"
      - name: Validar manifest e lock
        run: poetry check --lock
      - name: Sincronizar dependencias
        run: poetry sync --with dev,test,docs
      - name: Lint
        run: poetry run ruff check .
      - name: Formatacao
        run: poetry run ruff format --check .
      - name: Testes unitarios e cobertura de linhas
        run: poetry run pytest tests/unit --cov=nome_projeto --cov-report=term-missing --cov-fail-under=50
      - name: Tipagem
        run: poetry run mypy
      - name: Auditoria
        run: poetry run pip-audit
      - name: Documentacao
        run: poetry run mkdocs build --strict -f docs/mkdocs.yml
```

Este exemplo configura mypy e auditoria, portanto ambos são gates. A auditoria consulta o ambiente já instalado, sem `--fix`. Requer acesso ao serviço de vulnerabilidades e pode falhar por indisponibilidade ou novos findings; corrigir/avaliar achados com responsável e prazo, sem `continue-on-error`.

No GitHub, configurar `quality` como check obrigatório em ruleset/branch protection da branch principal, exigir code review conforme política e impedir bypass não autorizado. Ajustar o nome da branch se não for `main`. Integrações opcionais devem ter job próprio, segredos de teste e recursos descartáveis.

## 8. `.gitignore` recomendado

```gitignore
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.ruff_cache/
.mypy_cache/
.coverage
.coverage.*
htmlcov/
coverage.xml
site/
docs/site/
dist/
build/
*.egg-info/
.env
.env.*
!.env.example
data/
logs/
*.log
.ipynb_checkpoints/
.DS_Store
Thumbs.db
```

MUST versionar `poetry.lock`; não incluí-lo no ignore. Arquivos que já foram commitados continuam rastreados mesmo após adicionados ao `.gitignore`; se um segredo foi exposto, revogar/rotacionar e seguir o procedimento de incidente. Pequenas fixtures sintéticas podem ficar em `tests/fixtures/`, sem dados sensíveis.

## 9. Rotina padronizada

```bash
poetry --version
poetry config virtualenvs.in-project true --local
poetry env use 3.12
poetry lock
poetry check --lock
poetry sync --with dev,test,docs
poetry run ruff check . --fix
poetry run ruff format .
poetry run ruff check .
poetry run ruff format --check .
poetry run pytest
poetry run pytest --cov=nome_projeto --cov-report=term-missing --cov-fail-under=50
poetry run mypy
poetry run pip-audit
poetry run mkdocs build --strict -f docs/mkdocs.yml
```

`poetry lock` é usado na criação/alteração deliberada das dependências. No clone e no CI, usar o lock já versionado com `check --lock` e `sync`, sem regenerá-lo. Em produção: `poetry sync --only main`. Integrações, quando existirem: `poetry run pytest tests/integration -m integration` com infraestrutura de teste disponível.

## Fontes e manutenção

- [Poetry: instalação oficial](https://python-poetry.org/docs/#installation), [CLI](https://python-poetry.org/docs/cli/) e [pyproject](https://python-poetry.org/docs/pyproject/).
- [Ruff](https://docs.astral.sh/ruff/configuration/) e [pytest-cov](https://pytest-cov.readthedocs.io/en/latest/config.html).
- [MkDocs](https://www.mkdocs.org/user-guide/configuration/), [Material](https://squidfunk.github.io/mkdocs-material/) e [mkdocstrings Python](https://mkdocstrings.github.io/python/usage/).
- [mypy](https://mypy.readthedocs.io/en/stable/config_file.html) e [pip-audit](https://github.com/pypa/pip-audit).
- [Releases checkout](https://github.com/actions/checkout/releases) e [setup-python](https://github.com/actions/setup-python/releases).
- Metadados de versões: [PyPI Poetry](https://pypi.org/project/poetry/), [Ruff](https://pypi.org/project/ruff/), [pytest](https://pypi.org/project/pytest/) e demais projetos no PyPI.
