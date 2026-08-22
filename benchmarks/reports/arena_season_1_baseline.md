# Arena Oficial — Temporada 1 / Baseline

Campanha oficial de recolha experimental. **Não declara campeão** — comparação agregada e normalizada contra Acaso Puro, tal como acordado. Executada com `main` no estado do commit `b67a5200`.

## Configuração

- **Targets** (8, um por mês civil de 2026, regra pré-registada antes de observar qualquer resultado — ver nota de metodologia): `001/2026`, `010/2026`, `018/2026`, `027/2026`, `036/2026`, `044/2026`, `053/2026`, `062/2026`
- **Seeds**: `20260821, 20260822, 20260823`
- **`arena_seed`**: `1`
- **Generations (Clérigos)**: `20, 100, 520`
- **Sistemas** (6, todos os registados em `GENERATORS`): `clerics, skeletons, melforks, axiomantes, pantheon, acaso_puro`
- **`acaso_puro_quantidade`**: `20`
- **Categorias relevantes**: `5+2, 5+1, 5+0, 4+2, 4+1, 4+0, 3+2, 3+1`
- **`config.txt` real**, com cópia VERIFIED-compatível (`ARTEFACTOS_VIVOS`/`ARCA_ARTEFACTOS`/`MONGES_E_ESCRIBAS` desligados só na cópia usada pela campanha — `config.txt` no disco nunca foi tocado)

## 1. Confirmação de execução

**192/192 células produzidas, `expected_cells=192`, `unexpected=[]`.** Nenhuma falha, nenhuma célula em falta, nenhuma duplicada.

## 2. Duração e volume

- **Duração real da campanha**: 830,40 s (~13,84 min) — **muito acima da estimativa de calibração (~3,2 min)**. Ver secção 11 (comportamentos inesperados) para a causa identificada.
- **Total de candidatas produzidas**: 1.106.796 (muito próximo da estimativa de ~1,1M).

## 3. Participação / Abstenção por sistema

`ArenaSystemAttendance` (célula = alvo×seed; idêntico nas 3 vistas de `generations`, exceto Clérigos):

| Sistema | células tentadas | células c/ candidata | targets observados | targets c/ participação | taxa abstenção |
|---|--:|--:|--:|--:|--:|
| Clérigos | 24 | 24 | 8 | 8 | 0,0% |
| Esqueletos | 24 | 24 | 8 | 8 | 0,0% |
| Melforks | 24 | 24 | 8 | 8 | 0,0% |
| **Axiomantes** | 24 | **12** | 8 | **7** | **50,0%** |
| Panteão | 24 | 24 | 8 | 8 | 0,0% |
| Acaso Puro | 24 | 24 | 8 | 8 | 0,0% |

**Axiomantes é o único sistema com abstenção real** — o Portal fechou em metade das células, e num dos 8 alvos (não especificado individualmente aqui, disponível no JSON) o Portal esteve fechado nas 3 seeds simultaneamente. É comportamento legítimo, não falha — confirmado pelo próprio `system_abstention_rate=0.5`.

### Participação por estratégia (amostra — G20; tabela completa nos 3 valores de `generations` no JSON)

`success_rate_when_participating` e `success_rate_over_all_cells` aqui **não são normalizados por orçamento** — são descritivos, ver aviso na secção 5.

| Sistema\|Estratégia | tentadas | participou | sucesso | taxa particip. | sucesso quando participa | sucesso s/ tudo |
|---|--:|--:|--:|--:|--:|--:|
| acaso_puro\|Acaso Puro | 24 | 24 | 1 | 100% | 4,2% | 4,2% |
| axiomantes\|Axiomante | 24 | 12 | 1 | 50% | 8,3% | 4,2% |
| clerics\|Goblin | 24 | 24 | 8 | 100% | 33,3% | 33,3% |
| clerics\|Vidente | 24 | 24 | 8 | 100% | 33,3% | 33,3% |
| clerics\|Esqueleto | 24 | 24 | 5 | 100% | 20,8% | 20,8% |
| clerics\|Cronomante | 24 | 24 | 4 | 100% | 16,7% | 16,7% |
| clerics\|Chefe Tribal | 24 | 24 | 4 | 100% | 16,7% | 16,7% |
| clerics\|Elfo | 24 | 24 | 4 | 100% | 16,7% | 16,7% |
| clerics\|Bruxa | 24 | 24 | 2 | 100% | 8,3% | 8,3% |
| clerics\|Zombie | 24 | 24 | 2 | 100% | 8,3% | 8,3% |
| clerics\|Minotauro | 24 | 24 | 1 | 100% | 4,2% | 4,2% |
| clerics\|Shaman | 24 | 24 | 0 | 100% | **0,0%** | 0,0% |
| melforks\|Melfork | 24 | 24 | 0 | 100% | 0,0% | 0,0% |
| pantheon\|Mago/Druida/Djinn/Aion | 24 | 24 | 0 | 100% | 0,0% | 0,0% |
| skeletons\|Esqueleto das Catacumbas | 24 | 24 | 0 | 100% | 0,0% | 0,0% |
| clerics\|**"Renascido X"** (9 variantes) | 24 | 6–15 | 0 (exceto Bruxa=1@G100) | 25–63% | 0,0% quase sempre | ~0,0% |

**`success_rate_when_participating=None` nunca ocorreu nesta campanha** porque toda estratégia observada participou pelo menos uma vez — o caso `None` só surge com abstenção total, que não aconteceu para nenhuma (sistema, estratégia) descoberta (só ao nível do sistema, Axiomantes, que continua a participar noutras células).

## 4. Chave Oficial por estratégia

Uma por `(sistema, estratégia, alvo, seed)` — 8×3 = 24 por estratégia (Axiomantes: 12 reais + 12 `None`). Amostra, alvo `001/2026`, seed `20260821`, vista G20:

| Sistema | Estratégia | Chave Oficial |
|---|---|---|
| Acaso Puro | Acaso Puro | 16-30-40-41-43 \| 9-10 |
| Axiomantes | Axiomante | **None (Portal fechado nesta célula)** |
| Clérigos | Vidente | 17-23-28-36-38 \| 2-8 |
| Clérigos | Goblin | 4-21-22-27-45 \| 1-9 |
| Clérigos | Shaman | 14-29-32-37-47 \| 2-11 |
| Clérigos | **Renascido Shaman** | **14-29-32-37-47 \| 2-11 — idêntica à do Shaman-base** |
| Melforks | Melfork | 10-25-29-42-50 \| 10-12 |
| Panteão | Mago | 1-21-23-42-50 \| 3-9 |
| Panteão | Aion | 10-17-21-23-50 \| 6-8 |
| Esqueletos | Esqueleto das Catacumbas | 11-12-17-20-24 \| 4-7 |

Conjunto completo (192 células × estratégias observadas) no JSON, chave `official_keys`.

## 5. Orçamento Igual N=1 e N=2 (comparação principal)

**Aviso de leitura, obrigatório**: nesta secção, `req`=candidatas pedidas somadas nas 24 células, `used`=candidatas realmente usadas, `full`=células onde `n_used == N` (orçamento cheio). `rel`=acertos em categoria relevante dentro da amostra orçamentada — **este é o número comparável entre sistemas**, nunca `relevant_rate` da secção 3 ou 9 (que não é normalizado).

### N=1 (G20; ver JSON para G100/G520)

| Sistema\|Estratégia | pedidas | usadas | relevantes |
|---|--:|--:|--:|
| **Acaso Puro** | 24 | 24 | **0** |
| **Axiomantes** | 24 | 12 | **1** |
| Clérigos (todas as 10 raças-base) | 24 cada | 24 cada | **0** em todas |
| Melforks | 24 | 24 | 0 |
| Panteão (4 arquétipos) | 24 cada | 24 cada | 0 em todas |
| Esqueletos | 24 | 24 | 0 |

A N=1, com 24 tentativas por estratégia, **só Axiomantes teve 1 sucesso** — mas em só 12 tentativas reais (Portal fechado nas outras 12), o que é exatamente o tipo de resultado que este relatório não pode transformar em "Axiomantes ganha": 1 sucesso em 12 tentativas reais não é estatisticamente distinguível de 0 sucessos em 24, dado o tamanho da amostra.

### N=2 (G20)

| Sistema\|Estratégia | pedidas | usadas | relevantes |
|---|--:|--:|--:|
| Acaso Puro | 48 | 48 | 0 |
| Axiomantes | 48 | 12 | 1 |
| Clérigos (Zombie) | 48 | 48 | **1** |
| Clérigos (restantes 9 raças-base) | 48 cada | 48 cada | 0 |
| Panteão\|Aion | 48 | **24** — nunca chega a N=2 (só produz 1/célula) | 0 |
| Restantes sistemas | 48 cada | 48 (exceto Aion) | 0 |

**Nenhum sistema domina N=1/N=2 de forma clara** — os poucos sucessos observados (Axiomantes×1, Clérigos-Zombie×1) estão dentro do que se espera de ruído estatístico com tão poucas tentativas por categoria relevante (8 categorias de 18 possíveis, sobre alvos reais).

## 6. N=5 — complementar, sub-orçamento explícito

`fully_budgeted_cells` (de 24) mostra quem chega a N=5 sempre, às vezes, ou nunca:

| Sistema\|Estratégia | células com orçamento cheio (N=5) |
|---|--:|
| Acaso Puro, Melforks, Clérigos (Goblin/Esqueleto/Vidente/Minotauro) | 24/24 (sempre cheio) |
| Clérigos (Bruxa/Chefe Tribal/Elfo/Shaman/Zombie) | 17–22/24 (quase sempre) |
| Esqueletos | **0/24 — nunca chega a N=5** (produção fixa = 4/célula) |
| Panteão\|Djinn/Druida/Mago | **0/24** (produção fixa = 2/célula) |
| Panteão\|Aion | **0/24** (produção fixa = 1/célula) |
| Axiomantes | **0/24** (produção = 0 ou 1/célula) |
| Clérigos "Renascido X" (9 variantes) | 0–1/24 (quase sempre sub-orçamento) |

Confirma exatamente o desenho: Esqueletos/Panteão/Axiomantes ficam estruturalmente abaixo de N=5 por desenho da própria facção, nunca por falha — reportado, nunca escondido.

## 7. Distribuição de categorias e melhor categoria (`[HEROIS_TIERS]`)

Melhor categoria observada (pooled, `category_rank()` — tier primeiro, depois mais números, depois mais estrelas):

| Sistema\|Estratégia | melhor categoria |
|---|---|
| Clérigos\|Elfo | **4+0** |
| Clérigos\|Goblin, Vidente, Chefe Tribal, Cronomante, Esqueleto, Bruxa | **4+1** |
| Clérigos\|Zombie | 3+2 |
| Acaso Puro, Axiomantes, Clérigos\|Minotauro/Bruxa-Renascida | 3+1 |
| Melforks, Esqueletos, Panteão\|Mago | 2+1 |
| Panteão\|Druida/Djinn/Aion | 2+0 |
| **Clérigos\|Shaman** | **`None`** — nenhuma categoria pooled do Shaman atinge sequer o tier mais baixo listado em `[HEROIS_TIERS]` (13 categorias reais do `config.txt`; as restantes 5 — `0+0..1+1` — não têm tier) |

## 8. Estabilidade entre targets e seeds (desvio-padrão de `relevant_rate`, G20)

| Estratégia | stdev entre 8 targets | stdev entre 3 seeds |
|---|--:|--:|
| **Axiomantes** | **0,1750** — de longe o mais instável | 0,0786 |
| Acaso Puro | 0,0055 | 0,0029 |
| Clérigos\|Zombie | 0,0045 | 0,0039 |
| Clérigos\|Bruxa..Vidente (restantes raças-base) | 0,0010–0,0040 | 0,0001–0,0016 |
| Melforks, Panteão, Esqueletos, Clérigos\|Shaman/Renascido-X | 0,0000 | 0,0000 |

**Nota de leitura**: `stdev=0,0000` aqui reflete, na maioria dos casos, zero sucessos observados em todo o lado (uma taxa constante de 0% não é "estável" no sentido interessante, é "nunca aconteceu nada") — não interpretar como sinal de qualidade. **Axiomantes é claramente a estratégia mais instável entre alvos**, consistente com a sua natureza condicional (Portal aberto/fechado depende do histórico específico de cada alvo).

## 9. Todas as Chaves — bruto, sempre com custo

Topo por volume (top 10 de 40 pares sistema\|estratégia observados; tabela completa no JSON):

| Sistema\|Estratégia | total (custo) | únicas | repeat | relevantes | relevant % | melhor |
|---|--:|--:|--:|--:|--:|---|
| Clérigos\|Goblin | 176.091 | 142.608 | 19,0% | 265 | 0,15% | 4+1 |
| Clérigos\|Esqueleto | 169.284 | 96.766 | 42,8% | 313 | 0,18% | 4+1 |
| Clérigos\|Vidente | 144.939 | 116.114 | 19,9% | 166 | 0,11% | 4+1 |
| Clérigos\|Chefe Tribal | 131.832 | 103.638 | 21,4% | 370 | 0,28% | 4+1 |
| Clérigos\|Zombie | 113.564 | 32.301 | 71,6% | 31 | 0,03% | 3+2 |
| Acaso Puro | 480 | 60 | 87,5% | 1 | 0,21% | 3+1 |
| Panteão\|Aion | 24 | 23 | 4,2% | 0 | 0,00% | 2+0 |
| **Axiomantes** | **12** | 12 | 0,0% | **1** | **8,33%** | 3+1 |

**Aviso explícito**: `relevant_rate=8,33%` dos Axiomantes é o mais alto de toda a campanha — e é exatamente o número que este relatório recusa a usar como vencedor. Com só 12 candidatas totais, 1 acerto é uma amostra demasiado pequena para significar seja o que for; a versão comparável é a da secção 5 (Orçamento Igual), onde o mesmo 1 acerto aparece lado a lado com o mesmo esforço de amostragem de todas as outras estratégias.

## 10. Acaso Puro — controlo, sempre presente

Acaso Puro aparece em todas as tabelas acima, ao mesmo N, nos mesmos alvos/seeds que qualquer outra estratégia — participação 100%, sem abstenção, 0 sucessos a N=1/N=2, 1 sucesso em 480 tentativas brutas (0,21%), a segunda pior taxa bruta de toda a campanha depois de várias variantes "Renascido X". Nenhuma estratégia mostrou, nesta Temporada 1, uma vantagem clara e sustentada sobre o Acaso Puro nas comparações de orçamento igual.

## 11. Comportamentos inesperados

1. **Duração 4,3× acima da calibração** (830 s reais vs. ~193 s estimados). Causa provável: `run_system_campaign()` chama `prepare_backtest_run()` uma vez por `(sistema, alvo, seed)` — 144 vezes nesta campanha — cada uma a carregar/filtrar o dataset histórico real completo (1.974 sorteios) e os pergaminhos reais; a calibração anterior só exercitou isto 3 vezes sobre 1 alvo. Nenhuma alteração de código foi feita por causa disto, como combinado — só reportado.
2. **Tripla ressurreição** — `"Renascido Renascido Renascido Vidente"` observada pela primeira vez, só na vista G520 (1 candidata, 1 chave única). Consistente com o achado de dupla-ressurreição da Baseline dos Clérigos original, agora um nível mais fundo.
3. **Shaman e Renascido Shaman produziram a Chave Oficial idêntica** na amostra mostrada (mesma fase lunar, mesmo último sorteio visível) — confirma o achado arqueológico de que o Shaman nunca teve estratégia própria (cai sempre no ramo de deslocamento por fase lunar), agora visível diretamente na Chave Oficial.
4. **`relevant_rate` bruto dos Axiomantes (8,33%) é o mais alto da campanha apesar de terem a segunda menor taxa de participação** — o exemplo mais claro, nesta campanha, do problema de orçamento desigual que a Arena existe para neutralizar.

## 12. `git status --short` final e decomposição

```
?? benchmarks/rankings/arena_season_1_baseline.json
?? benchmarks/reports/arena_season_1_baseline.md
?? datasets/generated/simulations/runs/
```

- `benchmarks/rankings/arena_season_1_baseline.json` — dados brutos completos (todas as vistas de `generations`, todas as chaves oficiais, todos os orçamentos, estabilidade completa)
- `benchmarks/reports/arena_season_1_baseline.md` — este relatório
- `datasets/generated/simulations/runs/` — **192 manifestos reais** (0 incompletos), autorizados explicitamente para esta campanha oficial
- `experiments/axiomancers/runs/` — **sem alterações**, confirmado (nenhum ficheiro mais recente que o início da sessão)
- Nenhum ficheiro de código, config ou facção foi alterado antes, durante ou depois desta execução.

Nenhum destes ficheiros foi adicionado ao staging — aguardo autorização separada para `git add`.
