# Arena Oficial — Temporada 3 / A Guerra das Florestas

- **Data de execução**: 2026-08-23T16:37:27.477502+00:00
- **Commit base (hiperparâmetros congelados)**: `747f12dd6f12a353fd99e137c27e0e80806f9972`
- **Targets**: 54, mesma regra mecânica da Temporada 2 (idênticos)
- **Seeds**: `20260821, 20260822, 20260823`
- **`arena_seed`**: `1`
- **Sistema**: `treefolks_v2` — 5 florestas, Fangorn fora
- **Células**: 162/162 OK, 0 falhas
- **Duração real**: 207.3 s (3.5 min)
- **Total de candidatas avaliadas**: 16140
- **Manifests reais persistidos**: 162

## Orçamento Igual (N=1/2/5) por floresta

### N=1

| Floresta | n | relevantes | taxa | Wilson 95% |
|---|---|---|---|---|
| Yggdrasil — LSTM-v1 | 159 | 0 | 0.0000 | [0.000, 0.024] |
| Dodona — Bayes-v1 | 162 | 0 | 0.0000 | [0.000, 0.023] |
| Brocéliande — Markov-v1 | 162 | 0 | 0.0000 | [0.000, 0.023] |
| Tír na nÓg — MonteCarlo-v1 | 162 | 0 | 0.0000 | [0.000, 0.023] |
| Fortuna — Controlo-v1 | 162 | 0 | 0.0000 | [0.000, 0.023] |

### N=2

| Floresta | n | relevantes | taxa | Wilson 95% |
|---|---|---|---|---|
| Yggdrasil — LSTM-v1 | 318 | 0 | 0.0000 | [0.000, 0.012] |
| Dodona — Bayes-v1 | 324 | 0 | 0.0000 | [0.000, 0.012] |
| Brocéliande — Markov-v1 | 324 | 0 | 0.0000 | [0.000, 0.012] |
| Tír na nÓg — MonteCarlo-v1 | 324 | 1 | 0.0031 | [0.001, 0.017] |
| Fortuna — Controlo-v1 | 324 | 0 | 0.0000 | [0.000, 0.012] |

### N=5

| Floresta | n | relevantes | taxa | Wilson 95% |
|---|---|---|---|---|
| Yggdrasil — LSTM-v1 | 795 | 1 | 0.0013 | [0.000, 0.007] |
| Dodona — Bayes-v1 | 810 | 2 | 0.0025 | [0.001, 0.009] |
| Brocéliande — Markov-v1 | 810 | 3 | 0.0037 | [0.001, 0.011] |
| Tír na nÓg — MonteCarlo-v1 | 810 | 1 | 0.0012 | [0.000, 0.007] |
| Fortuna — Controlo-v1 | 810 | 1 | 0.0012 | [0.000, 0.007] |

## Comparações primárias — cada floresta vs. Fortuna (N=5)

| Floresta | rel/n | taxa | Wilson 95% | Fortuna rel/n | Fortuna taxa | Fortuna Wilson 95% | diff. absoluta |
|---|---|---|---|---|---|---|---|
| Yggdrasil — LSTM-v1 | 1/795 | 0.0013 | [0.000,0.007] | 1/810 | 0.0012 | [0.000,0.007] | +0.0000 |
| Dodona — Bayes-v1 | 2/810 | 0.0025 | [0.001,0.009] | 1/810 | 0.0012 | [0.000,0.007] | +0.0012 |
| Brocéliande — Markov-v1 | 3/810 | 0.0037 | [0.001,0.011] | 1/810 | 0.0012 | [0.000,0.007] | +0.0025 |
| Tír na nÓg — MonteCarlo-v1 | 1/810 | 0.0012 | [0.000,0.007] | 1/810 | 0.0012 | [0.000,0.007] | +0.0000 |

## Head-to-head exploratório entre florestas (N=5)

| Par | A rel/n | A taxa | B rel/n | B taxa | diff. absoluta |
|---|---|---|---|---|---|
| Yggdrasil — LSTM-v1 vs Dodona — Bayes-v1 | 1/795 | 0.0013 | 2/810 | 0.0025 | -0.0012 |
| Yggdrasil — LSTM-v1 vs Brocéliande — Markov-v1 | 1/795 | 0.0013 | 3/810 | 0.0037 | -0.0024 |
| Yggdrasil — LSTM-v1 vs Tír na nÓg — MonteCarlo-v1 | 1/795 | 0.0013 | 1/810 | 0.0012 | +0.0000 |
| Dodona — Bayes-v1 vs Brocéliande — Markov-v1 | 2/810 | 0.0025 | 3/810 | 0.0037 | -0.0012 |
| Dodona — Bayes-v1 vs Tír na nÓg — MonteCarlo-v1 | 2/810 | 0.0025 | 1/810 | 0.0012 | +0.0012 |
| Brocéliande — Markov-v1 vs Tír na nÓg — MonteCarlo-v1 | 3/810 | 0.0037 | 1/810 | 0.0012 | +0.0025 |

## Attendance (participação/abstenção)

- `treefolks_v2`: {'system': 'treefolks_v2', 'cells_attempted': 162, 'cells_with_any_candidate': 162, 'targets_observed': 54, 'targets_with_participation': 54, 'system_abstention_rate': 0.0}

- `treefolks_v2` / `Yggdrasil — LSTM-v1`: cells_participated=159/162 abstention_rate=0.019 success_rate_when_participating=0.025157232704402517
- `treefolks_v2` / `Fortuna — Controlo-v1`: cells_participated=162/162 abstention_rate=0.000 success_rate_when_participating=0.024691358024691357
- `treefolks_v2` / `Brocéliande — Markov-v1`: cells_participated=162/162 abstention_rate=0.000 success_rate_when_participating=0.043209876543209874
- `treefolks_v2` / `Tír na nÓg — MonteCarlo-v1`: cells_participated=162/162 abstention_rate=0.000 success_rate_when_participating=0.037037037037037035
- `treefolks_v2` / `Dodona — Bayes-v1`: cells_participated=162/162 abstention_rate=0.000 success_rate_when_participating=0.06172839506172839

## Diagnóstico Yggdrasil

- Participou em 159/162 células
- Absteve-se em 3/162 células
- Pares de treino por célula: min=31, max=1886, média=958.5

## Categorias completas (secundário)

- **Dodona — Bayes-v1** (n=3240): 0+0:1312, 1+0:758, 0+1:563, 1+1:349, 2+0:136, 2+1:55
- **Brocéliande — Markov-v1** (n=3240): 0+0:1256, 1+0:731, 0+1:598, 1+1:371, 2+0:153, 2+1:65
- **Tír na nÓg — MonteCarlo-v1** (n=3240): 0+0:1268, 1+0:811, 0+1:558, 1+1:338, 2+0:147, 2+1:54
- **Fortuna — Controlo-v1** (n=3240): 0+0:1264, 1+0:799, 0+1:547, 1+1:368, 2+0:142, 2+1:66
- **Yggdrasil — LSTM-v1** (n=3180): 0+0:1229, 1+0:778, 0+1:553, 1+1:349, 2+0:154, 2+1:62

## Nota metodológica

Nenhum parâmetro, código, seed ou config.txt foi alterado em função destes resultados. Nenhum vencedor é declarado automaticamente aqui. Fangorn/Ensemble está fora desta Temporada por design. Comparações head-to-head são exploratórias, nunca a base de uma declaração de vantagem isolada.

**Primeira tentativa abortada**: uma execução anterior desta mesma campanha (mesmos 54 targets, mesmas 3 seeds, mesmo commit `747f12dd`) escreveu 162 manifests reais e depois falhou por um bug de pós-processamento no script de campanha (`c.race` em vez de `c.candidate.race`, `AttributeError` em todas as 162 células, nenhum resultado de análise perdido porque nunca chegou a ser calculado) — intervalo de `run_id`/`started_at` **2026-08-23T16:03:17Z a 16:05:58Z**. Esses 162 manifests foram preservados intencionalmente, nunca apagados, e estão claramente fora do intervalo de tempo desta execução (bem-sucedida). Não fazem parte dos resultados abaixo — nenhum dos números deste relatório os inclui.
