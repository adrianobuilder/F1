# Contribuição

Seguir o SKILL.md da raiz: Poetry exclusivamente; pacotes em src; funções públicas tipadas; docstrings Google; Ruff para lint, imports e formato. Contratos e regras de negócio não devem depender de Streamlit.

Use branches feat/tema, fix/tema ou docs/tema e commits claros, preferencialmente Conventional Commits. PRs devem incluir testes de mudanças de comportamento e atualização da documentação. Revisar o poetry.lock junto das dependências. Não versionar ambientes, snapshots, credenciais ou dados sensíveis.

## Hooks locais de pre-commit

A configuração `.pre-commit-config.yaml` executa lint/imports e verificação de formatação com Ruff nos arquivos Python do commit. Os hooks são locais (`language: system`) e usam `poetry run`, sem instalar ambientes paralelos ou versões diferentes das ferramentas.

Após `poetry sync --with dev,test,docs`, instalar uma vez em cada clone:

```bash
poetry run pre-commit install
poetry run pre-commit run --all-files
```

Se um hook falhar, corrija os problemas antes de repetir o commit. Para organizar imports e formatar, execute `poetry run ruff check . --fix` e `poetry run ruff format .`, revise as alterações e adicione os arquivos novamente ao stage. Os hooks apenas verificam; não alteram arquivos automaticamente. Eles complementam os gates do CI, que também executam testes, tipagem, auditoria e documentação.

## Integração contínua no GitHub

O workflow `Quality` roda em pushes e pull requests para `main` e `dev`, além de permitir execução manual quando a versão com `workflow_dispatch` estiver na branch padrão. Execuções anteriores do mesmo PR ou branch são canceladas quando uma nova começa.

O job `quality` usa Ubuntu 24.04, Python 3.12 e Poetry 2.5.1. Sincroniza os grupos `dev`, `test` e `docs` pelo lockfile e executa:

1. Validação de `pyproject.toml` e `poetry.lock`.
2. Ruff: lint, imports e formatação.
3. mypy: contratos de tipos.
4. pytest: unitários e integração local, com cobertura de linhas mínima de 50% de todo o pacote.
5. pip-audit: vulnerabilidades conhecidas nas dependências.
6. MkDocs: build estrito via `poetry run task docs-build`.

Nenhuma etapa obrigatória ignora falhas. Testes não acessam a OpenF1. Os relatórios JUnit e XML de cobertura ficam no artefato `quality-reports` por sete dias, inclusive quando os testes falham. O cache contém downloads do Poetry; a instalação sempre é sincronizada com o lockfile.

Acompanhe em [GitHub Actions](https://github.com/adrianobuilder/F1/actions/workflows/quality.yml). Para execução manual: Actions → Quality → Run workflow. Para reproduzir os testes com relatórios:

```bash
poetry run pytest tests/unit tests/integration --cov-report=xml:reports/coverage.xml --junitxml=reports/pytest.xml
```

O check `quality` deve ser obrigatório na proteção de `main`, com code review conforme política da equipe. O YAML sozinho não impede merge. Não há publicação ou deploy automático.

Antes da entrega, informar os comandos realmente executados, seus resultados e limitações. Não ignorar falhas ou declarar testes aprovados sem execução. O projeto deve funcionar em Windows e no runner Linux.
