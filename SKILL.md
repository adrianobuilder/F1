---
name: python-data-engineering
description: Criar, modificar e revisar projetos Python de Engenharia de Dados com Poetry, arquitetura src, Ruff, pytest, cobertura e MkDocs Material. Aplicar em pipelines ETL/ELT, integrações e manutenção de código Python do time.
---

# Engenharia de Dados com Python

## Objetivo e escopo

Orientar desenvolvedores e agentes na construção e manutenção de projetos Python de Engenharia de Dados. Aplicar a código, configuração, testes e documentação; adaptar projetos existentes de forma incremental, sem reestruturar componentes alheios à tarefa.

**MUST** indica obrigação. **SHOULD** indica recomendação cuja exceção exige justificativa registrada no PR. **MAY** indica opção conforme necessidade demonstrada. Uma exceção a MUST exige decisão explícita do responsável pelo projeto; não deve ser presumida pelo agente.

Este arquivo é o padrão central do repositório. Para criar configurações ou consultar código executável, ler [exemplos completos](references/python-data-engineering-examples.md), que contém `pyproject.toml`, MkDocs, ETL tipado, testes, CI e `.gitignore`. Os exemplos são modelos para adaptação, não instrução para sobrescrever arquivos existentes. Manter esse arquivo de referência junto da skill ao reutilizá-la.

## Regras inegociáveis

- MUST usar **Poetry exclusivamente** para ambientes e dependências do projeto, com `pyproject.toml` e `poetry.lock` versionado. Nunca editar o lock manualmente.
- MUST NOT executar `pip install` diretamente, gerenciar o projeto por `requirements.txt`, criar ambientes com `python -m venv`, Conda, Pipenv ou uv. Instalar o próprio Poetry pelo instalador oficial isolado é bootstrap da ferramenta, não gerenciamento das dependências do projeto.
- MUST executar ferramentas do projeto com `poetry run`, organizar produção em `src/<pacote>/` e separar responsabilidades.
- MUST usar Ruff para lint, imports e formatação; pytest e pytest-cov para testes; MkDocs Material para documentação técnica.
- MUST garantir **cobertura de linhas de pelo menos 50% de todo o pacote de produção**, incluindo módulos não importados pelos testes. Não limitar a medição aos arquivos alterados.
- MUST NOT reduzir o limite, excluir código de produção, remover testes válidos ou ignorar falhas para obter aprovação.
- MUST NOT incluir credenciais no código, exemplos, Git ou logs. MUST NOT usar `print()` como logging de produção, `except: pass` ou ocultar falhas críticas.
- MUST justificar dependências novas e manter configurações coerentes. Não impor Pandas, Polars, PyArrow, SQLAlchemy ou um orquestrador sem requisito real.

## 1. Arquitetura e Estrutura do Projeto

### 1.1 Estrutura de referência

Usar a estrutura abaixo como referência. Criar somente diretórios necessários, com `__init__.py` nos pacotes Python convencionais.

```text
projeto/
├── pyproject.toml              # Configuração central do projeto e dependências
├── poetry.lock                 # Lockfile gerado pelo Poetry; não editar manualmente
├── .env.example                # Variáveis de ambiente sem valores reais
├── .gitignore                  # Arquivos e diretórios ignorados pelo Git
├── .pre-commit-config.yaml     # Hooks de pré-commit, quando adotados pelo time
├── README.md                   # Visão geral e guia de início rápido
├── SKILL.md                    # Padrões obrigatórios para humanos e agentes
├── references/                 # Exemplos complementares desta skill
│   └── python-data-engineering-examples.md
├── .github/
│   └── workflows/
│       └── quality.yml         # Gates de qualidade no GitHub Actions
├── src/
│   └── nome_projeto/
│       ├── __init__.py
│       ├── ingestion/          # Entrada e saída de dados; adaptadores externos
│       │   ├── __init__.py
│       │   ├── csv_sales.py    # Exemplo de extração CSV
│       │   └── json_sales.py   # Exemplo de carga JSON
│       ├── processing/         # Transformações e composição dos pipelines
│       │   ├── __init__.py
│       │   ├── sales.py        # Validação e transformação determinística
│       │   └── pipeline.py     # Coordenação de extração, transformação e carga
│       ├── domain/             # Regras de negócio e entidades de domínio
│       │   ├── __init__.py
│       │   └── sale.py         # Contrato de venda do exemplo
│       └── utils/              # Utilitários transversais: logging, config, helpers
│           ├── __init__.py
│           └── config.py       # Configuração centralizada e validada
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Fixtures compartilhadas quando necessárias
│   ├── unit/                  # Testes unitários isolados
│   │   ├── __init__.py
│   │   └── test_sales.py
│   └── integration/           # Testes com dependências externas
│       └── __init__.py
└── docs/
    ├── mkdocs.yml             # Configuração do MkDocs
    └── docs/                  # Páginas Markdown; docs_dir padrão do MkDocs
        ├── index.md           # Visão geral, objetivos e escopo
        ├── architecture.md    # Camadas e direção das dependências
        ├── project-structure.md
        ├── running-locally.md # Instalação, configuração e execução
        ├── running-tests.md   # Testes e cobertura
        ├── contributing.md    # Padrões de código, Git e revisão
        └── reference.md       # Referência técnica gerada por mkdocstrings
```

### 1.2 Responsabilidades das camadas

| Módulo | Responsabilidade e limites |
| --- | --- |
| `domain` | Regras de negócio independentes de arquivos, HTTP, banco e orquestrador |
| `ingestion` | Extração e carga em módulos separados; clientes de APIs/bancos, arquivos, transações e validação estrutural nas fronteiras |
| `processing` | Transformações determinísticas e coordenação do ETL/ELT em módulos distintos; não misturar transformação pura com I/O |
| `utils` | Configuração, logging e helpers técnicos pequenos e coesos; sem regras de negócio ou execução ao importar |
| `tests` | Cenários unitários e de integração separados |
| `docs` | Documentação versionada com MkDocs |

### 1.3 Dependências e modularização

- MUST manter `domain` independente de `ingestion`, `processing` e detalhes de configuração. Adaptadores e transformações podem depender dos contratos de domínio.
- MUST manter adaptadores de `ingestion` sem dependência de `processing`; a coordenação em `processing/pipeline.py` compõe extração, transformação e carga.
- MUST manter `utils` independente das camadas de negócio. Quando necessário, separar subpacotes `extractors`/`loaders` dentro de `ingestion` e `transformers`/`pipelines` dentro de `processing`, sem criar camadas vazias.
- MUST evitar ciclos. Inverter dependências com interfaces pequenas (`Protocol`, quando necessário) e injetar clientes/recursos em vez de importar implementações em ambos os sentidos.
- SHOULD usar imports absolutos a partir do pacote principal, funções coesas e SOLID, DRY e KISS sem hierarquias ou abstrações antecipadas.
- MUST manter notebooks apenas para exploração; promover lógica reutilizável para `src/`. Não concentrar produção em notebook ou script monolítico.

## 2. Gerenciamento de Ambiente com Poetry

### 2.1 Obrigatoriedade

O uso do **Poetry é obrigatório** para gerenciar dependências e ambientes virtuais. O uso direto de `pip install` é **estritamente proibido** no projeto, assim como ambientes administrados por outras ferramentas.

> **Razão:** o Poetry centraliza dependências no `pyproject.toml`, registra a resolução no `poetry.lock` e permite sincronizar ambientes reproduzíveis.

Baseline dos exemplos: Python **3.12** e Poetry **2.5.1**, consultados em 22/10/2026. Em projetos existentes, respeitar a versão declarada e avaliar migração separadamente. MUST alinhar `requires-python`, alvo do Ruff, tipagem, documentação e matriz de CI.

### 2.2 Instalação do Poetry

Instalar a ferramenta com o instalador oficial isolado, sem usar `pip install`. Em Linux/macOS:

```bash
curl --fail --silent --show-error --location https://install.python-poetry.org -o install-poetry.py
python3 install-poetry.py --version 2.5.1
```

No Windows, com PowerShell:

```powershell
Invoke-WebRequest -Uri https://install.python-poetry.org -OutFile install-poetry.py
py install-poetry.py --version 2.5.1
```

Seguir a orientação do instalador para adicionar o executável ao `PATH`. Verificar a instalação:

```bash
poetry --version
```

### 2.3 Criação, instalação e atualização do projeto

```bash
# Projeto novo, somente quando solicitado
poetry new --src nome-projeto
cd nome-projeto
poetry config virtualenvs.in-project true --local
poetry env use 3.12

# Projeto existente: instalar exatamente a resolução versionada
poetry check --lock
poetry sync --with dev,test,docs

# Adicionar dependências somente quando necessárias
poetry add httpx
poetry add --group dev ruff
poetry add --group test pytest pytest-cov
poetry add --group docs mkdocs mkdocs-material "mkdocstrings[python]"

# Atualização deliberada: revisar diff e validar novamente
poetry update httpx
poetry lock

# Produção: inclui o pacote do projeto, exclui grupos opcionais
poetry sync --only main
```

- MUST separar grupos opcionais `dev`, `test` e `docs`; usar `--with` explicitamente. `poetry sync` remove pacotes fora da seleção: executar apenas no ambiente do projeto.
- MUST gerar `poetry.lock` com Poetry e revisar suas mudanças. `poetry lock` resolve o necessário; `poetry update` atualiza dentro dos limites declarados. Não resolver/atualizar versões durante o CI normal.
- MUST fixar a versão do Poetry no CI e usar o mesmo lock. SHOULD fixar também a imagem/runtime e a versão patch do Python na implantação. Lock reproduz resolução de dependências, não garante equivalência entre sistemas operacionais.
- SHOULD manter `.venv` local. Versionar `poetry.toml` se contiver somente a preferência local de ambiente; nunca credenciais. Não depender de ativação manual nem de `poetry shell`.

## 3. Implementação e Contratos

- MUST tipar parâmetros e retornos de funções públicas, métodos e interfaces relevantes; usar tipos modernos compatíveis com o Python declarado.
- MUST evitar `Any` sem necessidade; representar dados externos inicialmente como desconhecidos e validá-los antes de convertê-los para contratos internos.
- SHOULD usar `dataclass` para entidades simples, `TypedDict` para estruturas de dicionário e `Enum` para conjuntos fechados. MAY usar Pydantic para validação complexa, quando justificar a dependência.
- MUST separar validação de entrada de regras de negócio, declarar unidades, timezone, precisão e semântica dos campos opcionais.
- SHOULD usar **mypy** como verificador adicional por integrar-se ao Python/Poetry e verificar contratos entre módulos. Configurar no projeto antes de torná-lo gate; não substitui o Ruff. Pyright MAY substituí-lo por decisão do time, sem manter verificadores redundantes.
- SHOULD escrever docstrings Google em interfaces públicas: propósito, `Args`, `Returns`, `Raises` e exemplos relevantes; não repetir apenas os type hints.

## 4. Padrões de ETL e ELT

| Tema | Regra operacional |
| --- | --- |
| Separação | MUST isolar extração, transformação e carga. Em ELT, manter SQL de transformação testável e separado da ingestão |
| Idempotência | MUST definir chave, escopo da execução e política de reprocessamento: upsert, substituição de partição ou publicação atômica |
| Incremental | MUST definir cursor/watermark, fuso e desempate; persistir checkpoint somente após confirmação da carga; prever atrasos e reprocessamento |
| Duplicidades | MUST definir chaves e resolução determinística; conflitos não podem desaparecer silenciosamente |
| Schema | MUST validar colunas, tipos, unidades e compatibilidade antes de publicar; mudança incompatível deve falhar ou ir para quarentena explícita |
| Nulos | MUST distinguir ausente, vazio e inválido; não preencher com zero sem regra de negócio |
| Integridade | MUST verificar obrigatoriedade, unicidade e referências aplicáveis; registrar quantidades aceitas, rejeitadas e duplicadas |
| Rastreabilidade | MUST registrar origem, janela/partição, identificador da execução e versão de schema/código; não registrar payload sensível |
| Recursos | MUST fechar arquivos, respostas e conexões com context managers ou `finally`; usar transações e rollback |
| Volume | SHOULD trabalhar com iteradores, lotes e projeção de colunas; evitar carregar toda a fonte em memória e operações linha a linha em DataFrames |
| Configuração | MUST manter caminhos, tamanhos de lote e endpoints fora da lógica; usar `pathlib.Path`, caminhos relativos ou recebidos por configuração |

### 4.1 Formatos e integrações

- **CSV:** MUST declarar encoding, delimitador, cabeçalho, tipos e política para linhas inválidas; identificadores com zeros iniciais são texto.
- **JSON:** MUST validar estrutura e tipos; distinguir documento JSON de JSON Lines. Usar JSON Lines/streaming quando o volume exigir.
- **Parquet:** SHOULD explicitar schema, tipos decimais e timezone; planejar partições e compactação para evitar muitos arquivos pequenos. Selecionar PyArrow/Pandas/Polars por volume, interoperabilidade e consumo de memória.
- **REST:** MUST usar timeouts, checar status e schema, tratar paginação, limites e término. Retry somente em falhas transitórias, com backoff exponencial, jitter, máximo de tentativas/tempo e respeito a `Retry-After`.
- **SQL:** MUST parametrizar valores, controlar transações e devolver conexões ao pool. Identificadores dinâmicos exigem allowlist/quoting apropriado, não interpolação livre. Cargas em lotes/upsert devem respeitar chaves e limites do banco.
- MUST não repetir automaticamente operações de escrita sem garantia de idempotência. Erros de contrato, autorização ou dados inválidos exigem correção, não retry indiscriminado.
- MAY usar orquestrador quando dependências, agenda, escala e operação o justificarem; uma CLI simples é suficiente em projetos menores.

## 5. Configuração e Segurança

- MUST centralizar configuração por variáveis de ambiente e validar valores essenciais no início da execução; falhar com mensagem sem revelar segredo.
- MUST fornecer `.env.example` somente com nomes e valores fictícios. Um arquivo `.env` não é carregado automaticamente por Python: usar exportação pelo ambiente ou um carregador explicitamente configurado.
- MUST separar desenvolvimento, homologação e produção; aplicar menor privilégio e impedir escrita no ambiente errado por configuração ambígua.
- MUST manter `.env`, tokens, dados sensíveis e credenciais fora do Git. Revisar também outputs, fixtures, notebooks e documentação antes de entregar.
- MUST manter dependências suportadas e auditadas. Quando `pip-audit` estiver configurado, executar `poetry run pip-audit`; o nome da ferramenta não autoriza `pip install`. Avaliar findings, não ocultá-los com ignores globais.
- SHOULD usar secret manager na implantação e fixtures sintéticas. Não incluir URLs com senha em mensagens de erro.

## 6. Logging e Tratamento de Erros

- MUST usar `logging.getLogger(__name__)`; configurar handlers na entrada da aplicação, nunca em cada módulo. Usar formato estruturado/JSON quando o consumidor operacional exigir.
- MUST registrar início, fim e falha das etapas com `run_id`, etapa, origem lógica, duração, contagens e resultado. O formatter/handler deve serializar os campos de `extra`; o formatter padrão não faz isso sozinho.
- MUST usar DEBUG para diagnóstico sem dados sensíveis, INFO para progresso, WARNING para desvio recuperável, ERROR para etapa malsucedida e CRITICAL para indisponibilidade que impeça a operação.
- MUST capturar exceções específicas e preservar causa com `raise ErroDeDominio(...) from exc`. Não registrar o mesmo erro em todas as camadas.
- MUST interromper publicação em falha de contrato, integridade ou carga. Quarentena só é recuperação válida quando política, destino e métricas estão definidos.
- SHOULD medir volume, duração, rejeições, retries e falhas. Logs não substituem métricas e alertas quando houver exigência operacional.

## 7. Testes e Quality Gates

```bash
poetry run ruff check .
poetry run ruff check . --fix
poetry run ruff format .
poetry run ruff format --check .
poetry run pytest
poetry run pytest --cov=nome_projeto --cov-report=term-missing --cov-fail-under=50
poetry run mkdocs serve -f docs/mkdocs.yml
poetry run mkdocs build --strict -f docs/mkdocs.yml
```

- MUST revisar autofixes e executar novamente os checks sem alterações. Ruff organiza imports com regras `I` e detecta imports não usados com `F`; não adicionar Black, isort ou Flake8 em paralelo sem justificativa técnica.
- SHOULD adotar linha de 88 caracteres, complexidade ciclomática máxima 10 e regras `E4`, `E7`, `E9`, `F`, `I`, `B`, `UP`, `SIM`, `C90`, `RUF`, conforme exemplo. O formatter trata comprimento como alvo, não limite absoluto; configurar `E501` separadamente somente se necessário.
- MUST medir cobertura de **linhas**, com `branch = false` e limite 50. Cobertura de branches MAY ser um gate adicional separado. SHOULD buscar cobertura maior para regras críticas; 50% é piso, não objetivo.
- MUST criar/atualizar testes de mudanças de comportamento: sucesso, falha, ausência, limites, duplicidade e reexecução quando pertinentes. Cobertura não substitui asserções relevantes.
- MUST manter unitários rápidos, determinísticos e sem serviços reais. Usar fixtures, `tmp_path`, parametrização e mocks/fakes nas fronteiras; controlar relógio, aleatoriedade e variáveis de ambiente.
- MUST espelhar módulos em `tests/unit/` e separar integrações em `tests/integration/`, com marca e execução explícita. Integrações usam ambiente descartável e nunca produção.
- MUST falhar o CI em lint, formatação, testes, cobertura ou documentação inválidos; se mypy/auditoria forem habilitados, suas falhas também bloqueiam entrega.

## 8. Documentação com MkDocs Material

MUST usar MkDocs Material, com configuração versionada em `docs/mkdocs.yml` e páginas em `docs/docs/`. Executar comandos da raiz com `-f docs/mkdocs.yml`, inclusive `poetry run mkdocs build --strict -f docs/mkdocs.yml` no CI. O diretório gerado é `docs/site/`. SHOULD habilitar `mkdocstrings[python]` quando a referência de interfaces públicas justificar geração automática a partir de docstrings.

A documentação MUST cobrir visão geral, objetivos/escopo, arquitetura, instalação Poetry, variáveis de ambiente sem segredos, guia de desenvolvimento, execução das pipelines, testes, padrões de código, exemplos, troubleshooting e referência dos módulos/funções relevantes. README MUST orientar o primeiro uso e apontar para `docs/`.

MUST atualizar instruções quando mudar configuração, contrato, comportamento ou operação. Não publicar documentação automaticamente sem tarefa de publicação autorizada.

## 9. Git, CI e Colaboração

- SHOULD usar branches `feat/<tema>`, `fix/<tema>`, `docs/<tema>` e `chore/<tema>`, commits objetivos e PRs pequenos.
- SHOULD adotar Conventional Commits, por exemplo `feat(pipeline): adiciona carga incremental`, `fix(loader): preserva destino em falha` e `docs: descreve variáveis de ambiente`.
- MUST revisar alterações de lock, testes e documentação no mesmo PR. Code review MUST cumprir a política de responsáveis do time.
- MUST NOT versionar `.venv`, caches, artefatos gerados, segredos ou dados sensíveis. MAY usar pre-commit via Poetry quando útil; hooks não substituem CI.
- MUST configurar o workflow de referência para Python → Poetry fixado → validação do lock → sincronização → Ruff → testes unitários/cobertura → MkDocs → verificações adicionais configuradas.
- MUST proteger a branch com o check obrigatório do job e revisão conforme política do time. O YAML sozinho **não bloqueia merge**; configurar ruleset/branch protection no GitHub. Não publicar nem fazer deploy como efeito colateral do gate.

## 10. Fluxo Operacional do Agente

1. Ler instruções aplicáveis, arquitetura, `pyproject.toml`, lock, testes e convenções existentes antes de editar.
2. Identificar mudança mínima e impactos em contratos, volume, estado, compatibilidade e operação. Não interpretar exemplos como autorização para migrar o projeto inteiro.
3. Reutilizar lógica existente; não duplicar implementação nem criar módulos gigantes. Justificar bibliotecas antes de adicioná-las com Poetry.
4. Implementar mudança, testes pertinentes e documentação; manter imports organizados e compatibilidade declarada.
5. Executar validações disponíveis com `poetry run`. Não mascarar falhas, remover testes válidos sem justificativa ou reduzir cobertura.
6. Revisar diff e segredos. Informar verificações executadas, resultados e limitações concretas. Se não puder executar um gate, dizer que ficou pendente; nunca afirmar aprovação sem execução.

## 11. Checklist Obrigatório de Entrega

- [ ] Arquitetura e modularização respeitadas.
- [ ] Dependências e ambientes gerenciados exclusivamente pelo Poetry; lock revisado.
- [ ] Código com type hints e contratos apropriados.
- [ ] Imports organizados pelo Ruff.
- [ ] Lint aprovado.
- [ ] Formatação aprovada.
- [ ] Testes unitários relevantes aprovados.
- [ ] Cobertura de linhas de todo o pacote de produção de pelo menos 50% validada.
- [ ] Idempotência, integridade, segurança e tratamento de erros verificados quando aplicáveis.
- [ ] Documentação atualizada e build estrito aprovado.
- [ ] Nenhum segredo exposto ou artefato indevido versionado.
- [ ] Tipagem/auditoria aprovadas quando configuradas.
- [ ] Alterações revisadas e prontas para integração; limitações informadas.

## 12. Exemplos e Referências Oficiais

- [Poetry: comandos](https://python-poetry.org/docs/cli/) e [grupos de dependências](https://python-poetry.org/docs/managing-dependencies/).
- [Ruff: configuração](https://docs.astral.sh/ruff/configuration/).
- [pytest-cov: configuração](https://pytest-cov.readthedocs.io/en/latest/config.html).
- [MkDocs: configuração](https://www.mkdocs.org/user-guide/configuration/) e [mkdocstrings Python](https://mkdocstrings.github.io/python/usage/).
- [GitHub setup-python](https://github.com/actions/setup-python) e [checkout](https://github.com/actions/checkout).
