# Plano de Criação — Dashboard F1 (OpenF1)

## Contexto e objetivo

Dashboard local para analisar sessões históricas de Fórmula 1 desde 2023, comparando resultados, voltas, setores, pneus, boxes, posições e clima. Guiado por [doc_api.md](doc_api.md) e [SKILL.md](SKILL.md).

## Stack e decisões

Python 3.12; Poetry e lockfile; Streamlit; Plotly; HTTPX síncrono; Pandas; JSON bruto e Parquet com PyArrow. Ruff, mypy, pytest/pytest-cov, MkDocs Material/mkdocstrings e GitHub Actions. Sem banco, autenticação, tempo real ou publicação na primeira versão.

## Arquitetura

Pacote f1 em src, dividido em domain, ingestion, processing, utils e dashboard. UI acessa apenas serviços; regras de negócio e contratos não importam infraestrutura ou Streamlit. Dados carregados sob demanda e armazenados por endpoint e sessão; catálogos por ano.

Cada carga gera arquivos imutáveis e publica manifesto atomicamente após conclusão. Catálogos expiram em 24 horas; sessões encerradas são reutilizadas até atualização manual/schema novo. Falha preserva snapshot válido anterior com aviso. Até três tentativas totais, timeout de 20 segundos, backoff e Retry-After. Consultas sequenciais.

## Funcionalidades

- Filtros temporada → GP → sessão → até quatro pilotos, com limpeza dos dependentes.
- Resumo: meetings, sessions, drivers e session_result.
- Comparação: laps, melhor volta, média e setores.
- Estratégia: stints e pit, separando tempo parado de pit lane.
- Posições: position ao longo da sessão.
- Clima: weather.
- Horários locais do evento na apresentação, UTC no armazenamento.
- Dados nulos preservados; Q1/Q2/Q3 separados; CSV com o mesmo recorte exibido.

## Etapas e critérios de aceite

1. Fundação: ambiente Poetry reproduzível, estrutura e qualidade.
2. Integração: cliente restrito aos nove endpoints, contratos e tratamento de falhas.
3. Persistência: JSON, Parquet, manifesto, idempotência e fallback.
4. Processamento: cálculos e filtros comprovados por testes.
5. Dashboard: cinco visões, filtros encadeados, gráficos e exportação.
6. Documentação/CI: instalação, operação, testes e gates obrigatórios.

Testes devem cobrir HTTP simulado, nulos, conflitos, reexecução, publicação malsucedida, fallback, resultados de classificação, cálculos, filtros e UI. Cobertura mínima de linhas de todo o pacote: 50%. O CI bloqueia o job em falhas de Ruff, mypy, testes, auditoria ou documentação; configurar proteção da branch separadamente.

Aceite final: selecionar sessão encerrada, comparar pilotos, explorar estratégias e clima, exportar tabelas e reabrir dados persistidos sem nova coleta. Execução: `poetry run streamlit run src/f1/dashboard/app.py`.
