# Execução local e troubleshooting

## Instalação

Requer Python 3.12 e Poetry. Execute da raiz:

```bash
poetry config virtualenvs.in-project true --local
poetry env use 3.12
poetry check --lock
poetry sync --with dev,test,docs
poetry run streamlit run src/f1/dashboard/app.py
```

Acesse http://localhost:8501. A sidebar escolhe temporada, GP, sessão encerrada e pilotos. O padrão é a sessão mais recente do catálogo do ano escolhido, com os dois primeiros classificados disponíveis. Trocar filtros superiores limpa seleções dependentes.

## Variáveis de ambiente

| Variável | Padrão | Uso |
| --- | --- | --- |
| F1_DATA_DIR | data | Base dos arquivos locais |
| F1_LOG_LEVEL | INFO | DEBUG, INFO, WARNING, ERROR ou CRITICAL |
| F1_HTTP_TIMEOUT | 20 | Timeout HTTP em segundos, maior que zero e até 120 |
| F1_HTTP_ATTEMPTS | 3 | Tentativas totais, de 1 a 3 |
| F1_CATALOG_TTL_HOURS | 24 | Validade do catálogo, positiva |

Exporte variáveis pelo shell. `.env.example` documenta opções; arquivos `.env` não são carregados automaticamente. Em PowerShell: `$env:F1_DATA_DIR = 'data'`. Para ambientes distintos, use diretórios distintos.

## Operação

Abrir a visão inicia as etapas necessárias: extração, validação, publicação e cálculo. “Atualizar dados” força a seleção atual; mudar de visão não atualiza silenciosamente os datasets históricos. Horários são armazenados em UTC e exibidos com o deslocamento do evento. Logs JSON incluem identificador da execução, endpoint, volume, duração e resultado.

## Problemas comuns

- **Sem sessões:** selecione outro ano; sessões futuras/canceladas não são exibidas.
- **Sem registros:** pode ser limitação da fonte, não necessariamente erro. Não substituir por zero.
- **Erro 429/indisponibilidade:** aguarde e tente atualizar; dados locais já carregados continuam disponíveis.
- **Snapshot inválido:** tente atualizar com rede; arquivos corrompidos não são apresentados como válidos.
- **Erro de escrita:** verifique permissão e espaço no diretório de dados; a geração anterior permanece referenciada.
- **Python incompatível:** selecione o interpretador 3.12 com `poetry env use`.
- **Offline:** apenas recursos previamente armazenados estarão disponíveis; avisos de atualização mostram a coleta original.

Não exponha a aplicação na rede pública sem um projeto separado de hospedagem e segurança.
