# OpenF1 API — Documentação Resumida

> Fonte oficial: [https://openf1.org/docs](https://openf1.org/docs/)  
> Consulta: 22/10/2026

---

## Visão Geral

A **OpenF1** é uma API aberta e não oficial que fornece dados de telemetria e temporização da Fórmula 1 em **JSON** ou **CSV**.

- **Dados históricos:** disponíveis a partir de 2023, gratuitos e sem autenticação.
- **Dados em tempo real:** exigem assinatura paga.
- **URL base:** `https://api.openf1.org/v1/`
- **Método das consultas:** `GET`.

---

## Autenticação

Nenhuma autenticação é necessária para consultar o histórico. Para acesso em tempo real, é necessária uma assinatura; consulte as condições e instruções de acesso no [site oficial](https://openf1.org/docs/).

---

## Filtragem e Dicas de Consulta

Os resultados podem ser filtrados por atributos na query string, exceto atributos que sejam arrays. Combine os filtros com `&`.

| Operador | Exemplo |
| --- | --- |
| Igual | `driver_number=44` |
| Maior ou igual | `speed>=300` |
| Menor ou igual | `lap_duration<=90` |
| Maior que | `rpm>12000` |
| Menor que | `throttle<50` |

**Dicas úteis:**

- Use `session_key=latest` ou `meeting_key=latest` para selecionar a sessão ou etapa mais recente/atual. O acesso em tempo real continua sujeito à assinatura.
- Adicione `csv=true` à consulta para exportar em CSV; o padrão é JSON.
- Prefira datas ISO 8601. Os timestamps retornados são UTC.
- Ao montar URLs, codifique `>` como `%3E`, `<` como `%3C` e espaços como `%20`. Um deslocamento com `+` deve usar `%2B`.
- Para telemetria e localização, delimite sessão, piloto e período para reduzir o volume retornado.

**Exemplo de intervalo de datas:** sessões iniciadas em setembro de 2023, com limite superior exclusivo.

```http
GET /v1/sessions?date_start%3E=2023-09-01&date_start%3C2023-10-01
```

**Exemplo de exportação CSV:**

```http
GET /v1/sessions?year=2023&csv=true
```

### Identificadores e Campos Comuns

| Campo | Descrição |
| --- | --- |
| `meeting_key` | Identificador do evento: GP ou período de testes, com várias sessões |
| `session_key` | Identificador da sessão: treino, classificação, sprint ou corrida |
| `driver_number` | Número do piloto na temporada |
| `date` | Instante do registro em UTC, no formato ISO 8601 |

Esses campos aparecem em diversos endpoints. As tabelas seguintes destacam os campos específicos de cada recurso.

---

## Endpoints

Os exemplos usam o host `https://api.openf1.org`. Cada seção apresenta a URL completa do recurso e uma consulta de referência.

### 1. Car Data — Telemetria do Carro

> **URL:** `https://api.openf1.org/v1/car_data`

Telemetria amostrada a aproximadamente **3,7 Hz**.

| Campo | Descrição |
| --- | --- |
| `brake` | Freio: `100` pressionado ou `0` solto |
| `date` | Timestamp UTC |
| `driver_number` | Número do piloto |
| `drs` | Código do estado do DRS |
| `n_gear` | Marcha de 1 a 8; `0` indica neutro/nenhuma marcha |
| `rpm` | Rotações do motor por minuto |
| `speed` | Velocidade em km/h |
| `throttle` | Percentual de potência máxima utilizado, conforme a documentação |

**Estados do DRS:** interpretação aproximada apresentada pela fonte.

| Código | Interpretação |
| --- | --- |
| `0`, `1` | Desativado |
| `8` | Detectado; elegível na zona de ativação |
| `10`, `12`, `14` | Ativado |
| `2`, `3`, `9` | Significado não definido |

```http
GET /v1/car_data?driver_number=55&session_key=9159&speed%3E=315
```

---

### 2. Drivers — Informações dos Pilotos

> **URL:** `https://api.openf1.org/v1/drivers`

Informações dos pilotos participantes de uma sessão.

| Campo | Descrição |
| --- | --- |
| `broadcast_name` | Nome exibido na transmissão |
| `driver_number` | Número do piloto |
| `first_name`, `last_name` | Nome e sobrenome |
| `full_name` | Nome completo |
| `name_acronym` | Sigla de três letras, como VER |
| `team_name` | Nome da equipe |
| `team_colour` | Cor hexadecimal da equipe, no formato RRGGBB |
| `headshot_url` | URL da foto do piloto |

```http
GET /v1/drivers?session_key=9158&driver_number=1
```

---

### 3. Intervals — Diferenças entre Pilotos

> **URL:** `https://api.openf1.org/v1/intervals`

Disponível somente em corridas, com atualização aproximada a cada **4 segundos**.

| Campo | Descrição |
| --- | --- |
| `gap_to_leader` | Diferença para o líder, em segundos |
| `interval` | Diferença para o carro à frente, em segundos |
| `date` | Instante da medição |

As diferenças também podem ser texto, como `+1 LAP`, ou `null` para o líder.

```http
GET /v1/intervals?session_key=9165&driver_number=1
```

---

### 4. Laps — Voltas e Setores

> **URL:** `https://api.openf1.org/v1/laps`

Tempos e medições de cada volta.

| Campo | Descrição |
| --- | --- |
| `lap_number` | Número da volta, começando em 1 |
| `date_start` | Início aproximado da volta em UTC |
| `lap_duration` | Tempo total em segundos |
| `duration_sector_1`, `duration_sector_2`, `duration_sector_3` | Tempos dos três setores, em segundos |
| `i1_speed`, `i2_speed` | Velocidades nos pontos intermediários, em km/h |
| `st_speed` | Velocidade no speed trap, em km/h |
| `is_pit_out_lap` | Indica volta de saída dos boxes |
| `segments_sector_1`, `segments_sector_2`, `segments_sector_3` | Arrays dos estados dos minissetores |

**Minissetores:** `0` indisponível; `2048` amarelo; `2049` verde; `2051` roxo; `2064` pit lane. Outros códigos têm significado não definido. Não estão disponíveis em corridas e podem divergir das cores da transmissão.

```http
GET /v1/laps?session_key=9161&driver_number=63&lap_number=8
```

---

### 5. Location — Localização dos Carros

> **URL:** `https://api.openf1.org/v1/location`

Posição aproximada no circuito, a cerca de **3,7 Hz**. Não permite determinar com precisão o posicionamento lateral; a origem das coordenadas é arbitrária.

| Campo | Descrição |
| --- | --- |
| `x`, `y`, `z` | Coordenadas cartesianas aproximadas |
| `date` | Instante da posição |
| `driver_number` | Número do piloto |

```http
GET /v1/location?session_key=9161&driver_number=81&date%3E2023-09-16T13:03:35.200&date%3C2023-09-16T13:03:35.800
```

---

### 6. Meetings — Etapas e Eventos

> **URL:** `https://api.openf1.org/v1/meetings`

Informações dos GPs e períodos de testes. Atualização diária à meia-noite UTC.

| Campo | Descrição |
| --- | --- |
| `meeting_key` | Identificador do evento |
| `meeting_name`, `meeting_official_name` | Nome curto e oficial |
| `year` | Ano |
| `country_name`, `country_code`, `country_key` | País e identificadores |
| `location` | Localidade |
| `circuit_key`, `circuit_short_name` | Identificador e nome do circuito |
| `circuit_type` | Tipo de circuito |
| `circuit_image`, `country_flag` | URLs de imagens |
| `circuit_info_url` | URL de informações adicionais do circuito |
| `date_start`, `date_end` | Início e fim em UTC |
| `gmt_offset` | Diferença do horário local em relação ao GMT |
| `is_cancelled` | Indica cancelamento |

```http
GET /v1/meetings?year=2023&country_name=Singapore
```

---

### 7. Overtakes — Trocas de Posição

> **URL:** `https://api.openf1.org/v1/overtakes`

Somente corridas. Inclui trocas por ultrapassagem na pista, boxes ou penalidades posteriores; a cobertura pode ser incompleta.

| Campo | Descrição |
| --- | --- |
| `overtaking_driver_number` | Piloto que ganhou a posição |
| `overtaken_driver_number` | Piloto que perdeu a posição |
| `position` | Posição de quem ultrapassou após a troca |
| `date` | Instante registrado |

```http
GET /v1/overtakes?session_key=9636&overtaking_driver_number=63&overtaken_driver_number=4&position=1
```

---

### 8. Pit — Passagens pelos Boxes

> **URL:** `https://api.openf1.org/v1/pit`

Registra passagens pelo pit lane e duração da parada.

| Campo | Descrição |
| --- | --- |
| `driver_number` | Número do piloto |
| `lap_number` | Volta da passagem |
| `date` | Timestamp UTC |
| `lane_duration` | Tempo no pit lane, em segundos |
| `stop_duration` | Tempo parado, em segundos; disponível desde o GP dos EUA de 2024 |

```http
GET /v1/pit?session_key=9877&stop_duration%3C2.3
```

---

### 9. Position — Posições na Sessão

> **URL:** `https://api.openf1.org/v1/position`

Posicionamento inicial e mudanças ao longo da sessão.

| Campo | Descrição |
| --- | --- |
| `driver_number` | Número do piloto |
| `position` | Posição, começando em 1 |
| `date` | Instante do registro |

```http
GET /v1/position?meeting_key=1217&driver_number=40&position%3C=3
```

---

### 10. Race Control — Direção de Prova

> **URL:** `https://api.openf1.org/v1/race_control`

Mensagens sobre bandeiras, incidentes, safety car e estado da sessão.

| Campo | Descrição |
| --- | --- |
| `category` | Categoria, como `Flag`, `SafetyCar` ou `SessionStatus` |
| `message` | Texto da mensagem |
| `flag` | Bandeira, como `GREEN`, `YELLOW` ou `CHEQUERED` |
| `scope` | Abrangência, como `Track`, `Driver` ou `Sector` |
| `driver_number` | Piloto relacionado |
| `lap_number` | Volta em corrida |
| `qualifying_phase` | Fase da classificação: 1, 2 ou 3 |
| `sector` | Segmento associado; interpretação incerta na fonte |
| `date` | Timestamp da mensagem |

```http
GET /v1/race_control?session_key=9165&flag=YELLOW
```

---

### 11. Sessions — Sessões do Evento

> **URL:** `https://api.openf1.org/v1/sessions`

Treinos, classificações, sprints e corridas. Atualização diária à meia-noite UTC.

| Campo | Descrição |
| --- | --- |
| `session_key`, `meeting_key` | Identificadores da sessão e evento |
| `session_name` | Nome, como `Practice 1`, `Qualifying` ou `Race` |
| `session_type` | Tipo da sessão |
| `year` | Ano |
| `country_name`, `country_code`, `country_key` | País e identificadores |
| `circuit_key`, `circuit_short_name` | Circuito |
| `location` | Localidade |
| `date_start`, `date_end` | Início e fim em UTC |
| `gmt_offset` | Diferença para o horário local |
| `is_cancelled` | Indica cancelamento |

```http
GET /v1/sessions?country_name=Belgium&session_name=Sprint%20Qualifying&year=2023
```

---

### 12. Session Result — Resultado da Sessão

> **URL:** `https://api.openf1.org/v1/session_result`

Resultado disponibilizado alguns minutos após a publicação oficial pela Fórmula 1.

| Campo | Descrição |
| --- | --- |
| `position` | Posição final |
| `driver_number` | Número do piloto |
| `duration` | Melhor volta em treino/classificação ou tempo total de corrida, em segundos |
| `gap_to_leader` | Diferença em segundos ou texto `+N LAP(S)` |
| `number_of_laps` | Total de voltas completadas |
| `dnf` | Não terminou; pode ser verdadeiro em classificação/corrida |
| `dns` | Não largou; pode ser verdadeiro em classificação/corrida |
| `dsq` | Desclassificado |

Na classificação, `duration` e `gap_to_leader` são arrays com valores de Q1, Q2 e Q3.

```http
GET /v1/session_result?session_key=7782&position%3C=3
```

---

### 13. Starting Grid — Grid de Largada

> **URL:** `https://api.openf1.org/v1/starting_grid`

Grid da corrida, disponibilizado alguns minutos após a publicação oficial.

| Campo | Descrição |
| --- | --- |
| `position` | Posição no grid |
| `driver_number` | Número do piloto |
| `lap_duration` | Tempo da volta de classificação, em segundos |

```http
GET /v1/starting_grid?session_key=7783&position%3C=3
```

---

### 14. Stints — Sequências de Voltas e Pneus

> **URL:** `https://api.openf1.org/v1/stints`

Períodos contínuos de pilotagem de um piloto na sessão.

| Campo | Descrição |
| --- | --- |
| `stint_number` | Número sequencial do stint, começando em 1 |
| `driver_number` | Número do piloto |
| `compound` | Composto: `SOFT`, `MEDIUM`, `HARD`, entre outros |
| `lap_start` | Primeira volta do stint |
| `lap_end` | Última volta completada no stint |
| `tyre_age_at_start` | Voltas já completadas com o pneu antes do stint |

```http
GET /v1/stints?session_key=9165&tyre_age_at_start%3E=3
```

---

### 15. Team Radio — Rádio das Equipes

> **URL:** `https://api.openf1.org/v1/team_radio`

Seleção de comunicações entre pilotos e equipes. Não representa o rádio completo; a disponibilidade varia por sessão e a documentação alerta para cobertura reduzida desde 2026.

| Campo | Descrição |
| --- | --- |
| `driver_number` | Número do piloto |
| `date` | Instante do registro |
| `recording_url` | URL da gravação de áudio |

```http
GET /v1/team_radio?session_key=9158&driver_number=11
```

---

### 16. Weather — Condições Meteorológicas

> **URL:** `https://api.openf1.org/v1/weather`

Condições no circuito, atualizadas a cada **minuto**.

| Campo | Descrição |
| --- | --- |
| `air_temperature` | Temperatura do ar em °C |
| `track_temperature` | Temperatura da pista em °C |
| `humidity` | Umidade relativa em % |
| `pressure` | Pressão em mbar |
| `rainfall` | Indicação de chuva |
| `wind_direction` | Direção do vento, de 0° a 359° |
| `wind_speed` | Velocidade do vento em m/s |
| `date` | Instante da medição |

```http
GET /v1/weather?meeting_key=1208&wind_direction%3E=130&track_temperature%3E=52
```

---

### 17. Drivers Championship — Campeonato de Pilotos (Beta)

> **URL:** `https://api.openf1.org/v1/championship_drivers`

Classificação do campeonato, disponível somente para sessões de corrida.

| Campo | Descrição |
| --- | --- |
| `driver_number` | Número do piloto |
| `points_start` | Pontos antes da corrida |
| `points_current` | Pontos durante/após a corrida, conforme o momento da consulta |
| `position_start` | Posição no campeonato antes da corrida |
| `position_current` | Posição durante/após a corrida |

```http
GET /v1/championship_drivers?session_key=9839&driver_number=4&driver_number=81
```

---

### 18. Teams Championship — Campeonato de Equipes (Beta)

> **URL:** `https://api.openf1.org/v1/championship_teams`

Classificação das equipes no campeonato, disponível somente para sessões de corrida.

| Campo | Descrição |
| --- | --- |
| `team_name` | Nome da equipe |
| `points_start`, `points_current` | Pontos antes e durante/após a corrida |
| `position_start`, `position_current` | Posições antes e durante/após a corrida |

```http
GET /v1/championship_teams?session_key=9839&team_name=McLaren
```

---

## Exemplo em Python

Consulta histórica com a biblioteca padrão, sem dependências externas:

```python
import json
from urllib.parse import urlencode
from urllib.request import urlopen

params = urlencode(
    {
        "session_key": 9161,
        "driver_number": 63,
        "lap_number": 8,
    }
)
url = f"https://api.openf1.org/v1/laps?{params}"

with urlopen(url, timeout=30) as response:
    laps = json.load(response)

for lap in laps:
    print(lap["lap_number"], lap.get("lap_duration"))
```

---

## Observações de Compatibilidade

- `drivers.country_code` está obsoleto, com remoção prevista ao final da temporada de 2026.
- `pit.pit_duration` está obsoleto; use `lane_duration`. A remoção também está prevista ao final de 2026.
- Campos podem ter formatos diferentes conforme a sessão: confira especialmente diferenças para o líder e resultados da classificação.
- Os exemplos usam sessões históricas; não pressupõem a participação atual dos pilotos ou equipes citados.

Para a lista completa de atributos e atualizações, consulte a [documentação oficial da OpenF1](https://openf1.org/docs/).
