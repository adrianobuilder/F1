# Dashboard histórico F1

Aplicação local em Streamlit para explorar resultados, voltas, estratégias, posições e clima de sessões encerradas da Fórmula 1 desde 2023. Fonte: [OpenF1](https://openf1.org/docs/), uma API não oficial.

Selecione temporada, GP e sessão na barra lateral. Compare até quatro pilotos. O dashboard busca apenas os recursos da visão selecionada; dados locais válidos são reutilizados. Tabelas podem ser baixadas em CSV com o mesmo recorte apresentado.

## Objetivos e limites

Oferecer análises históricas reproduzíveis e uma base modular de Engenharia de Dados. Não inclui assinatura, coleta ao vivo, autenticação, banco servidor, inferências causais, telemetria de alta frequência ou publicação automática.

## Medidas

- Melhor volta: menor duração positiva, não nula, excluindo voltas de saída dos boxes.
- Média: média aritmética das mesmas voltas, acompanhada da quantidade considerada; não é ritmo corrigido de corrida.
- Setores: tempos disponibilizados pela fonte para essas voltas.
- Stints: intervalos inclusivos entre primeira e última volta, por composto.
- Boxes: tempo no pit lane separado de tempo parado. Campo ausente permanece ausente.
- Resultados: Q1/Q2/Q3 em colunas distintas, preservando valores indisponíveis.

Dados podem ter cobertura parcial. A aplicação mostra quando um recurso está vazio e quando utiliza dados anteriores por falha de atualização.
