# Arena Oficial — Temporada 2 / Guerra das Estrelas

- **Data de execução**: 2026-08-23T10:40:12.720766+00:00
- **Targets**: 54, regra mecânica pré-registada (ver `target_selection_rule` no JSON)
- **Seeds**: `20260821, 20260822, 20260823`
- **`arena_seed`**: `1`
- **Sistemas**: `asterias`, `acaso_puro`
- **Células**: 162/162 OK, 0 falhas
- **Duração real**: 54.0 s (0.9 min)
- **Total de candidatas avaliadas**: 9060
- **Manifests reais persistidos**: 324

Esta Temporada 2 é especializada nas Astérias vs. Acaso Puro — a Temporada 1 permanece congelada, nenhum ficheiro seu foi tocado.

## Prova das Estrelas (N=1/2/5)

### N=1

| Estratégia | n | 0★ | 1★ | 2★ | taxa 2★ | Wilson 95% | taxa ≥1★ | stdev/target | stdev/seed |
|---|---|---|---|---|---|---|---|---|---|
| Astéria Abissal | 129 | 83 | 45 | 1 | 0.0078 | [0.001, 0.043] | 0.3566 | 0.0502 | 0.0110 |
| Astéria das Marés [condicional] | 129 | 92 | 36 | 1 | 0.0078 | [0.001, 0.043] | 0.2868 | 0.0502 | 0.0110 |
| Astéria das Marés [backoff] | 33 | 20 | 13 | 0 | 0.0000 | [0.000, 0.104] | 0.3939 | 0.0000 | 0.0000 |
| Acaso Puro | 162 | 115 | 45 | 2 | 0.0123 | [0.003, 0.044] | 0.2901 | 0.0630 | 0.0087 |

### N=2

| Estratégia | n | 0★ | 1★ | 2★ | taxa 2★ | Wilson 95% | taxa ≥1★ | stdev/target | stdev/seed |
|---|---|---|---|---|---|---|---|---|---|
| Astéria Abissal | 258 | 182 | 71 | 5 | 0.0194 | [0.008, 0.045] | 0.2946 | 0.0534 | 0.0055 |
| Astéria das Marés [condicional] | 258 | 183 | 70 | 5 | 0.0194 | [0.008, 0.045] | 0.2907 | 0.0534 | 0.0110 |
| Astéria das Marés [backoff] | 66 | 51 | 14 | 1 | 0.0152 | [0.003, 0.081] | 0.2273 | 0.0479 | 0.0214 |
| Acaso Puro | 324 | 230 | 91 | 3 | 0.0093 | [0.003, 0.027] | 0.2901 | 0.0382 | 0.0076 |

### N=5

| Estratégia | n | 0★ | 1★ | 2★ | taxa 2★ | Wilson 95% | taxa ≥1★ | stdev/target | stdev/seed |
|---|---|---|---|---|---|---|---|---|---|
| Astéria Abissal | 645 | 450 | 185 | 10 | 0.0155 | [0.008, 0.028] | 0.3023 | 0.0316 | 0.0058 |
| Astéria das Marés [condicional] | 645 | 435 | 201 | 9 | 0.0140 | [0.007, 0.026] | 0.3256 | 0.0307 | 0.0066 |
| Astéria das Marés [backoff] | 165 | 113 | 49 | 3 | 0.0182 | [0.006, 0.052] | 0.3152 | 0.0297 | 0.0148 |
| Acaso Puro | 810 | 545 | 251 | 14 | 0.0173 | [0.010, 0.029] | 0.3272 | 0.0319 | 0.0063 |

## Abissal vs. Marés — participação

- Células com `n(P)>=5`: 129 / 162
- Abstenções da Abissal: 33 / 162
- Marés em modo condicional: 129 / 162
- Marés em modo backoff marginal: 33 / 162
- Marés em abstenção total (histórico<5): 0 / 162

## Star Contribution Trial — melhorou / igual / piorou

| Linhagem | melhorou | igual | piorou | n pares |
|---|---|---|---|---|
| Astéria Abissal | 583 | 1446 | 551 | 2580 |
| Astéria das Marés [condicional] | 579 | 1408 | 593 | 2580 |
| Astéria das Marés [backoff] | 166 | 366 | 128 | 660 |

## Categorias completas (métrica secundária — os números são neutros)

- **Astéria das Marés [backoff]** (n=660): 0+0:253, 1+0:151, 0+1:112, 1+1:76, 2+0:26, 2+1:21
- **Acaso Puro** (n=3240): 0+0:1249, 1+0:774, 0+1:547, 1+1:369, 2+0:166, 2+1:64
- **Astéria Abissal** (n=2580): 0+0:1008, 1+0:636, 0+1:427, 1+1:283, 2+0:125, 2+1:49
- **Astéria das Marés [condicional]** (n=2580): 0+0:1030, 1+0:565, 0+1:456, 1+1:299, 2+0:118, 2+1:55

## ArenaSystemAttendance / ArenaStrategySummary

- `acaso_puro`: ArenaSystemAttendance(system='acaso_puro', cells_attempted=162, cells_with_any_candidate=162, targets_observed=54, targets_with_participation=54, system_abstention_rate=0.0)
- `asterias`: ArenaSystemAttendance(system='asterias', cells_attempted=162, cells_with_any_candidate=162, targets_observed=54, targets_with_participation=54, system_abstention_rate=0.0)

- `('acaso_puro', 'Acaso Puro')`: cells_attempted=162 cells_participated=162 abstention_rate=0.000
- `('asterias', 'Astéria Abissal')`: cells_attempted=162 cells_participated=129 abstention_rate=0.204
- `('asterias', 'Astéria das Marés')`: cells_attempted=162 cells_participated=162 abstention_rate=0.000

## Nota metodológica

Nenhum parâmetro, código ou config.txt foi alterado em função destes resultados. Nenhum vencedor é declarado automaticamente aqui — os números acima ficam para leitura humana, com numerador/denominador sempre explícitos.
