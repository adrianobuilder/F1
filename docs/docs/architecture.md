# Arquitetura e contratos

Fluxo: Streamlit → serviços → snapshot ou HTTP → validação → JSON/Parquet → consultas → gráficos e CSV.

`domain` define endpoints permitidos, proveniência, tipos JSON e exceções. Não importa UI nem adaptadores. `ingestion` implementa HTTP e armazenamento, sem importar processamento. `processing` aplica contratos, valida chaves, normaliza tipos e coordena as cargas. `dashboard` recebe tabelas e proveniência dos serviços. `utils` centraliza configuração e logging.

## Publicação

Cada dataset possui arquivos imutáveis JSON bruto e Parquet normalizado em uma nova geração. O manifesto é substituído atomicamente somente após ambos os arquivos estarem completos. O leitor consulta a geração indicada pelo manifesto, verifica checksum, contagem e versão de schema. Uma falha mantém a geração anterior referenciada; arquivos órfãos podem permanecer. Sem coordenação entre múltiplos escritores e sem garantia de fsync em queda de energia.

Catálogos são particionados por ano; dados de análise, por sessão. Catálogos expiram em 24 horas. Datasets de sessões encerradas são reutilizados até atualização explícita ou mudança do schema. Durante falha, somente snapshots previamente válidos servem de fallback. Se o cache estiver inválido e a fonte falhar, o erro fica visível.

Chaves: evento (`meeting_key`); sessão (`session_key`); piloto e resultado (`driver_number`); volta (piloto, volta); stint (piloto, stint); boxes/posição (piloto, data); clima (data). Duplicatas idênticas são removidas; conflitos interrompem publicação. Novos campos são preservados no bruto. Estruturas JSON adicionais são serializadas como texto no Parquet. Tempos de classificação são expandidos em colunas Q1/Q2/Q3.

O cliente faz até três tentativas totais em falhas transitórias, timeout por operação de 20 segundos e espera com backoff/jitter. Respeita Retry-After até 60 segundos; esperas maiores retornam aviso ao usuário, sem repetir antes do prazo. Outros erros HTTP não são repetidos. Não há coleta em paralelo.
