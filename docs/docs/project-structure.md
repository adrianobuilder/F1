# Estrutura do projeto

```text
src/f1/
├── domain/       # Tipos, endpoints, proveniência e exceções
├── ingestion/    # Cliente HTTP e armazenamento de snapshots
├── processing/   # Validação, coordenação e consultas analíticas
├── utils/        # Ambiente e logging JSON
└── dashboard/    # Entrada Streamlit, visões e gráficos Plotly
tests/
├── unit/         # HTTP simulado, contratos, cálculos, arquivos e UI
└── integration/  # Fluxo completo local, sem serviços reais
docs/
├── mkdocs.yml
└── docs/         # Páginas Markdown
data/            # Gerado localmente; fora do Git
├── raw/
├── processed/
└── manifests/
```

Os manifests referenciam a geração completa de cada dataset. Novas atualizações não fazem append sobre a anterior. Versões antigas e arquivos órfãos não são removidos automaticamente. Para descartar todos os dados locais, encerre a aplicação e remova deliberadamente o diretório configurado em F1_DATA_DIR; a próxima consulta precisará de rede.
