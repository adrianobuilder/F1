# F1 — Dashboard histórico

[![Quality](https://github.com/adrianobuilder/F1/actions/workflows/quality.yml/badge.svg?branch=dev)](https://github.com/adrianobuilder/F1/actions/workflows/quality.yml)

Dashboard local em português para explorar sessões históricas da OpenF1: resultados, comparação de pilotos, stints, boxes, posições e clima. Dados desde 2023, sem assinatura para consultas históricas.

## Instalação

Requer Python 3.12 e Poetry. Na raiz do repositório:

```powershell
poetry config virtualenvs.in-project true --local
poetry env use 3.12
poetry check --lock
poetry sync --with dev,test,docs
poetry run streamlit run src/f1/dashboard/app.py
```

Abra http://localhost:8501. Selecione temporada, GP, sessão e até quatro pilotos. Cada visão busca apenas seus recursos; as respostas são armazenadas em `data/`. A primeira carga precisa de internet. Depois, as sessões já carregadas podem ser consultadas offline.

## Configuração

Consulte `.env.example`. As variáveis devem ser exportadas pelo shell; `.env` não é carregado automaticamente.

```powershell
$env:F1_DATA_DIR = 'data'
$env:F1_LOG_LEVEL = 'INFO'
```

Catálogos expiram em 24 horas. Sessões encerradas permanecem disponíveis até atualização manual ou mudança de schema. “Atualizar dados” atualiza os catálogos, participantes, resultados e recursos da visão aberta. Na falha, um snapshot válido anterior é preservado com aviso e data de coleta.

## Desenvolvimento

Após instalar as dependências, ative os hooks locais uma vez por clone:

```powershell
poetry run pre-commit install
poetry run pre-commit run --all-files
```

O pre-commit verifica lint, imports e formatação dos arquivos Python antes de cada commit. Os hooks usam o Ruff do ambiente Poetry; o CI continua executando a validação completa.

```powershell
poetry run ruff check .
poetry run ruff format --check .
poetry run mypy
poetry run pytest
poetry run pytest tests/integration
poetry run pip-audit
poetry run task docs-build
poetry run task docs
```

Cobertura mínima de linhas: 50% de todo o pacote `f1`. Testes unitários e de integração local não acessam a OpenF1. O pacote usa `ingestion`, `processing`, `domain`, `utils` e `dashboard`.

Veja o [plano](plan.md), os [padrões](SKILL.md), a [referência da API](doc_api.md) e o [guia de execução](docs/docs/running-locally.md).

## Limites

Aplicação individual local, sem tempo real, autenticação ou banco de dados. Ausência de registros não significa valor zero. A média das voltas não é um ritmo corrigido de corrida. O armazenamento usa snapshots locais com publicação atômica do manifesto; não coordena escritores simultâneos e não promete durabilidade após queda de energia. Atualizações mantêm gerações antigas para preservar a referência anterior; a limpeza automática não faz parte do MVP.

Fonte: [OpenF1](https://openf1.org/docs/), projeto não oficial e sem vínculo com as empresas da Fórmula 1.
