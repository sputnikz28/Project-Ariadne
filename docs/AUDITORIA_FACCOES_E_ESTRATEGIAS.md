# Auditoria/Arqueologia Técnica — Facções e Estratégias do Projeto

> Auditoria pura, sem alterações de código. Realizada antes do Commit 28,
> a pedido explícito, para mapear o estado real de todas as facções e
> estratégias do projeto — incluindo entidades não geridas pelo Campaign
> Runner (Commit 27), que continua Clérigos-only.

**Método**: código atual (`factions/`, `orders/`, `core/`, `artifacts/`) + arqueologia Git completa. Achado prévio importante: o repositório em `main` só remonta a **"V8.1 - Open Source Edition"** (commit `f3965931`) — antes disso existe apenas uma linhagem paralela de 3 commits em português (`master`/`claude`/`open`: `756c63e6` "V8 - Claude" → `f79d907a` "v8.1 Axiomantes" → `75ff25e9` "v8.1.1 Ritual dos 30 Ecos"), que é onde a "V8" foi traduzida para inglês e reorganizada. **Não existe história Git de V1-V7** — essas versões só existem como resumo narrativo no `CLAUDE.md`, nunca como código commitado. Toda a arqueologia abaixo usa isto como limite honesto, não fingido.

## Atenção especial — resolvido com evidência

**1. "Treefolks usaram redes neuronais"** — confirmado, mas não como pensavas: `'modelo': random.choice(['Random Forest', 'Rede Neural', 'LSTM', 'Bayesiano'])` em `factions/treefolks/algorithm.py:19` é **um rótulo narrativo sorteado**, nunca um modelo real — sem treino, sem pesos, sem `numpy`/`sklearn`/`tensorflow` em lado nenhum do projeto (busca exaustiva por essas strings, atual e em toda a história Git, zero resultados reais). O algoritmo é heurística de pontuação (`.45*freq_norm + .35*atraso_norm + .2*random()`). Esta string já existia no commit mais antigo disponível (`756c63e6`, `racas/extras.py`) — a "memória" é real, a rede neuronal nunca foi.

**2. Algoritmos genéticos além dos Clérigos** — `factions/melforks/algorithm.py` é um **algoritmo genético completo e independente**: população → `fitness()` → elite → crossover por união de genes dos pais → `geracoes_chaves` iterações (`core/services/fitness.py`, não o dos Clérigos). Confirmado desde o commit mais antigo (`melforks()` em `racas/extras.py`). Nenhuma outra facção implementa GA — Werewolves é Monte Carlo puro (heap top-100, sem cruzamento/seleção geracional), não GA.

**3. "Guardiões do Tempo" vs Cronomantes** — **não existe entidade "Guardiões do Tempo"** em código nem em git em lado nenhum (0 resultados para a frase exata, todas as branches). Existe só **"Guardião do Tempo" (singular)**, um epíteto narrativo aplicado a **Aion** numa citação de artefacto (`library/artifacts/entries/ART-CODEX-FORTUNA-ETERNA-0001.json`: *"Voto de Aion, Guardião do Tempo"*). Aion é gerado por `orders/pantheon/aion.py` (agrega Magos+Druidas+Djinns), não por Cronomantes — e o próprio `CLAUDE.md` está desatualizado aqui (diz que Aion vem de `factions/chronomancers/representatives.py`, ficheiro que **já não existe**). Não confundir: Cronomantes são uma facção real e ativa; "Guardiões do Tempo" nunca foi.

**4. Vampiros/Gárgulas/Melforks órfãos?** — **não estão órfãos**. Todos têm `manifest.json` (`votes: true`), são descobertos por `FactionRegistry.discover("factions")`, e o arquivo real (`arquivo_destino.json`, 42.527 registos) confirma execuções reais passadas: `melfork=190`, `vampiro=30`, `gargula=30`. Vampiros/Gárgulas leem `library/indexes/triplas.json`/`duplas.json` **diretamente por ficheiro**, nunca via Ariadne (duplicação já documentada no `CLAUDE.md`).

**5. Achado novo, não documentado antes: Lobisomens têm um buraco real na proveniência.** `factions/werewolves/manifest.json` tem `"id": "lobisomem"`, e `main.py:213-217` regista **toda** proposta de `all_proposals` externamente com `origem=p.origin` — mas `"lobisomem"` **não existe** na taxonomia fechada de `core/services/candidate_provenance.py` (18 valores, Commit 16). Confirmado no arquivo real: **zero registos `"lobisomem"` em 42.527** — nunca aconteceu de bater a condição de lua cheia (`LOBISOMENS.apenas_semana_lua_cheia=true`) num run real até agora. Mas no dia em que acontecer, `normalize_candidate_record()` vai levantar `ValueError` sobre um registo genuíno. Gap latente, nunca disparado.

## Tabela por entidade

| Entidade | Estratégia real | Caminho | Estado | Gera chaves | Entrypoint hoje | Ariadne/Histórico | RNG | Persistência | VERIFIED | CandidateKey (`origem`) | Campaign Runner |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Clérigos** | Genético, 9 raças + Minotauro (persistência) + Zombie (Monte Carlo territorial) | `factions/clerics/{algorithm,archetypes}.py` | ACTIVE | Sim | `main.py` explícito (`ctx['clerics_evo']`) + loop genérico | histórico via `ctx['historico']`, sem Ariadne | `random` global | Artefactos/Arca/Monges (gated) | **Único auditado e suportado** | `racas_antigas`→`evolutionary_individual` | **Único suportado** (orquestrador hardcoded) |
| **Melforks** | Genético (população/elite/crossover), independente | `factions/melforks/algorithm.py` | ACTIVE | Sim | loop genérico | não | `random` global | não | não auditado | `melfork`→`external_generator` | não |
| **Vampiros** | Triplas frequentes (`triplas.json` direto) | `factions/vampires/algorithm.py` | ACTIVE | Sim | loop genérico | ficheiro direto, não Ariadne | `random` global | não | não auditado | `vampiro`→`external_generator` | não |
| **Gárgulas** | Duplas frequentes (`duplas.json` direto) | `factions/gargoyles/algorithm.py` | ACTIVE | Sim | loop genérico | ficheiro direto, não Ariadne | `random` global | não | não auditado | `gargula`→`external_generator` | não |
| **Treefolks** | Heurística freq+atraso, rótulo "modelo" narrativo | `factions/treefolks/algorithm.py` | ACTIVE | Sim | loop genérico | não (usa `ctx['estatisticas']`) | `random` global | não | não auditado | `treefolk`→`external_generator` | não |
| **Kors de Elarion** | 4 sub-estratégias via Ariadne (atrasados/menos-frequentes/transição/ecos semanais) | `factions/kors/{white,red,green,black}.py` | ACTIVE | Sim | loop genérico | **Ariadne direto, LIVE**; `red.py` usa `least_frequent_numbers()` — um dos 4 métodos **estruturalmente não certificáveis** (Commit 23) | não observado | `black.py` cria papiros em disco | **Nunca poderá ser VERIFIED sem redesenhar `least_frequent_numbers()`** | `kors_elarion`→`external_generator` | não |
| **Cartógrafos do Caos** | 5 analistas (constelações/ciclos/tendências/aleatoriedade/markov) | `factions/chaos_cartographers/*.py` | ACTIVE (analítico) | **Não** (`votes:false`) | `main.py` explícito, antes dos Kors | `ariadne.full_history()` — **é** um dos métodos certificáveis por pergaminho (Commit 23) | não observado | escreve livros em `library/books/` | tecnicamente mais perto de VERIFIED que Kors, mas não gera `CandidateKey` (irrelevante ao Campaign Runner) | n/a (não regista candidato) | não |
| **Axiomantes de Nemerion** | Feistel determinístico (rank/unrank + 4 rondas), sem amostragem probabilística | `factions/axiomantes/{labyrinth,profile,ritual}.py` | ACTIVE | Sim | loop genérico | `ariadne.full_history()`/`last_known_key()` | **nenhum `random` — `seed` é parâmetro do Feistel, não entropia** | grava JSON em `experiments/axiomancers/runs/` se `guardar_experiencia` | não auditado (mas RNG-determinismo facilitaria) | `axiomantes_nemerion`→`external_generator` | não |
| **Esqueletos** | Janela móvel (largura configurável) sobre `range(1,51)` | `factions/skeletons/algorithm.py` | ACTIVE | Sim | loop genérico | não | `ctx['rng']` (um dos 3 já retrofitados, com Panteão+Cronomantes) | não | não auditado | `esqueleto`→`external_generator` | não |
| **Cronomantes** | Energia determinística dos eventos de extração (segundo+milissegundo+fase lunar) | `factions/chronomancers/algorithm.py` | ACTIVE | Sim | loop genérico | não | `ctx['rng']` injetado, usado só no fallback sem eventos | não | não auditado | `cronomante`→`external_generator` | não |
| **Anões** | Enumeração combinatória filtrada por soma sobre pool reduzida (20 números) — **não é wheeling clássico** (sem garantia de cobertura) | `factions/dwarves/algorithm.py` | ACTIVE | Sim | loop genérico | não | `random` global | não | não auditado | `cla_anao`→`external_generator` | não |
| **Fadas** | Amostragem ponderada (`random.choices` com pesos) + filtros narrativos, fallback aleatório | `factions/faeries/algorithm.py` | ACTIVE | Sim | loop genérico | não | `random` global | não | não auditado | `fada`→`external_generator` | não |
| **Lobisomens** | Monte Carlo puro (top-100 via heap, só na semana de lua cheia) | `factions/werewolves/algorithm.py` | ACTIVE, mas **nunca disparou num run real** (ver achado #5) | Sim | loop genérico (condicional à fase lunar) | não | `random` global | não | não auditado | `lobisomem` — **ausente da taxonomia**, ValueError latente | não |
| **Esquadrão Negro** | Score anti-popularidade + grimório roubado + diversificação gulosa por distância de conjunto simétrico (`^`) | `orders/black_squad/{black_mages,strategies,persistence}.py` | ACTIVE, fora do `FactionRegistry` por design | Sim (`create_mages`) | `main.py` explícito | não | não observado | **Grimório persistente, sem timestamp — irremediavelmente legado (Commit 21/24)** | **estruturalmente impossível** sem redesenho | `esquadrao_negro`→`external_generator` | não |
| **Ordem Élfica** | Missões de recuperação/purificação — não gera chave própria | `orders/elven_order/ninjas.py` | ACTIVE, fora do `FactionRegistry`, não vota | **Não** | `main.py` explícito | não | não observado | `estado_ordem.json` — mesmo problema do Grimório | n/a | n/a | não |
| **Guardiões do Tempo** | **Não existe** — só o epíteto narrativo de Aion (ver achado #3) | — | inexistente | — | — | — | — | — | — | — | — |

## Entidades não pedidas mas encontradas

| Entidade | Estado | Nota |
|---|---|---|
| **8 Mystics** (Druids, Moon Priests, Star Gazers, Bone Readers, Oracles, Seers, Shamans, Witches) | **LORE_ONLY / PARTIAL** — `council.py` sempre devolve `[]`; `strategy.py` é skeleton não referenciado | Registados, votam com peso zero de facto (abstenção válida por design, V10) |
| **Aion + Pantheon (Magos/Druidas/Djinns)** | ACTIVE, fora do `FactionRegistry` | `create_aion()` agrega os outros 3 por `Counter`; `origem`: `ser_superior`/`deus` |
| **Malphas / Corrupção Final** | ACTIVE, transformador (não gerador) | `origem=corrupcao_final`→`transformer`; corrompe a chave já escolhida pelo Conselho |
| **Necromancia (ressurreição de Lendas)** | ACTIVE | `origem=necromancia_estatistica`→`transformer`, distinto do `"Renascido X"` dos Clérigos (`CAMINHO_1000_ALMAS`) |
| **Monges e Escribas** | ACTIVE, gate de memória, não gera chaves | Código real em `artifacts/amulets/monastery.py` (`CLAUDE.md` refere `books.py`, desatualizado) |
| **Librarians/Scribes** (`orders/librarians`, `orders/scribes`) | ACTIVE, puramente arquivístico | `converter.py` só lê `draw["chave"]` de um sorteio já existente — nunca gera candidato novo |

## Estratégias antigas → quem as implementou (evidência)

| Estratégia pedida | Encontrada? | Onde |
|---|---|---|
| Covering/Wheeling clássico | **Não** (só "covering" em inglês num docstring, falso positivo) | Anões chegam perto (enumeração+filtro), mas sem garantia de cobertura |
| Simulated Annealing | **Nunca implementado**, código nem git | — |
| Maximum Coverage | **Nunca implementado** | — |
| Hamming/Jaccard | **Nunca por esse nome**; `Jaccard` só existe como campo `None` planeado em `dashboard_data.py` (`jaccard_medio_vs_geracao_anterior`, sem definição canónica) | — |
| Clustering/k-means | **Nunca implementado** | — |
| Anti-popularidade | **Real** | `orders/black_squad/strategies.py:penalizacao_popularidade()` |
| Monte Carlo | **Real, 3 sítios**: Lobisomens (heap top-100), Zombie dos Clérigos (`n_simulacoes=300`), Cartógrafos do Caos (`monte_carlo_simulacoes`) | — |
| Redes neuronais | **Nunca real** — só rótulo narrativo sorteado (Treefolks) | — |
| Diversificação gulosa por distância de conjunto | **Real, não documentada com este nome antes** | `orders/black_squad/strategies.py:diversificar()` — distância = `|A △ B|` (diferença simétrica), seleção gulosa max-min |

## "Se fizéssemos hoje um Campeonato do Universo com orçamento equivalente de candidatas por estratégia"

**Na arena, hoje, sem qualquer código novo:**
- **Clérigos** — já corre no Campaign Runner (Commit 27), 29 raças descobertas dinamicamente, VERIFIED auditado.
- Melforks, Vampiros, Gárgulas, Treefolks, Esqueletos, Cronomantes, Anões, Fadas, Kors, Axiomantes — **geram `CandidateKey` compatível** (taxonomia + testes já existem, Commit 16-18), mas **nenhum tem um orquestrador de backtest**: o `backtest_orchestrator.py` só sabe chamar `factions.clerics.algorithm.execute()`. Entrariam na arena de avaliação retrospetiva (`candidate_evaluation.py`/`candidate_performance.py`) hoje mesmo, **desde que alguém corra o algoritmo e lhes dê um alvo** — só o Campaign Runner automatizado (`run_campaign()`) é que os exclui, por hardcoding, não por incompatibilidade estrutural.

**Ficam de fora, mesmo com orçamento infinito, sem trabalho novo:**
- **Lobisomens** — o buraco de proveniência (`"lobisomem"` fora da taxonomia) rebentaria o pipeline assim que aparecesse um registo real.
- **Kors** — `red.py` depende de um método (`least_frequent_numbers()`) que o próprio Commit 23 provou **impossível de certificar temporalmente** sem reescrever a fonte de dados — VERIFIED nunca vai ser alcançável para Kors como estão hoje.
- **Esquadrão Negro / Ordem Élfica** — Grimório e `estado_ordem.json` são "irremediavelmente legado" (achado do Commit 21/24, reafirmado aqui): sem timestamp ao nível do facto agregado, nunca vão poder entrar numa arena VERIFIED.
- **Cartógrafos do Caos, Mystics (8), Aion/Pantheon, Malphas, Necromancia, Monges/Escribas, Librarians/Scribes** — **não geram `CandidateKey`** próprio (analíticos, agregadores, transformadores, ou abstêm-se por design) — não há "candidata" para medir, por definição, não por limitação técnica.
- **"Guardiões do Tempo"** — não há arena para quem não existe.

O campeonato mais honesto possível hoje, sem escrever uma linha de código, seria **Clérigos vs. os 10 outros geradores de chave** avaliados retrospetivamente (não via `run_campaign()`, que teria de ser generalizado primeiro) — e mesmo esse já teria dois membros (Kors, Esquadrão Negro/Ordem Élfica) estruturalmente impedidos de correr em modo VERIFIED, só em EXPLORATORY.
