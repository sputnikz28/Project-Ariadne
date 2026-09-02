# The Eternal Library

> A multi-agent statistical simulation framework where fantasy-inspired factions analyse historical lottery data using competing statistical philosophies — with full backtesting under identical conditions.

**No magic. No predictions. Just agents, data, and reproducible experiments.**

---

## What is this?

The Eternal Library is an experimental Python framework built around one central idea: **what happens when many independent agents, each following a different statistical strategy, compete on the same historical dataset under identical, reproducible conditions?**

The agents are factions from a fictional universe. The dataset is 1,974 real Euromillions draws (2004–2026). The strategies range from genetic algorithms and Markov chains to combinatorial permutations and frequency analysis.

The result is something between a simulation engine, a statistical workbench, and a strategy game — with lore.

---

## Why is it interesting?

Most lottery analysis tools are either:

- Simplistic frequency counters with no competitive framework
- Black-box ML models with no interpretability
- Pure gambling tools marketed as prediction systems

This project is none of those. It is a **laboratory for statistical strategies**, where:

- Every faction is an independent agent with its own philosophy
- All agents compete under **identical historical conditions**
- Results are **fully reproducible** (deterministic seed)
- The framework includes a persistent **knowledge library** (Ariadne) shared by all agents
- Backtesting is built in from the start

> **Important:** Historical patterns do not increase the probability of predicting a future draw. Any key has the exact same mathematical probability: 1 in 139,838,160. This project explores strategies as objects of study, not as prediction tools.

---

## Current Status (V13 + Commits 25-27 + Campaign Runner V2 + Arena + Astérias + Treefolks V2)

A quick map of what actually exists in this repository today, kept separate from ideas — see [Roadmap / Future Vision](#roadmap--future-vision) for what is *not* built yet, and [Historical/Recovered Documentation](#historicalrecovered-documentation) for archaeology that is neither implemented code nor a roadmap idea.

**✅ Core simulation engine** — plugin architecture (`core/registry.py`, `core/plugin_loader.py`, `core/strategy.py`), 21 auto-discovered voting factions, Ariadne as sole data broker, Council (filtering, weighted voting, Malphas corruption), 21 lore-only races, i18n (6 languages).

**✅ Historical dataset pipeline** — 1,974 real Euromillions draws (2004–2026), immutable annual datasets, plus `core/services/historical_dataset.py`, `historical_astronomy.py`, `historical_statistics.py`, `historical_scroll.py` and `historical_draw_generator.py` (used by `register_official_draw.py`, a full transactional CLI — staged → validated → installed, with rollback — for registering new official draws).

**✅ Heroes & Legends** — `library/heroes/` and `library/legends/` registries (`entries/*.json` as source of truth, derived `LIVRO_DOS_HEROIS.json`/`LIVRO_DAS_LENDAS.json` indices), plus `core/services/hero_evaluation.py`/`legend_evaluation.py` and their CLIs (`evaluate_heroes.py`, `evaluate_legends.py`).

**✅ Dashboard Dataset** — `core/services/dashboard_data.py`, a pure data-assembly layer: Heroes, Legends, Base de Chaves (draws), Characters, Houses, Executive Summary, Economy, Prize Categories, Generations and Frequencies are all implemented and tested against real data (see [Dashboard Dataset](#dashboard-dataset) below).

**✅ Dashboard Excel Export** — `dashboard/excel_export.py` turns an already-built `DashboardDataset` into a `.xlsx` workbook (Executive Summary, Heroes, Legends, Characters, Houses, Key Base, Economy, Prize Categories). Tested, including against the project's real data. No CLI or script wires this to live data yet — see [Dashboard Dataset](#dashboard-dataset) below.

**✅ Shared Statistical Primitives & Rolling Windows** — `core/services/statistical_profiles.py` (frequency, delay, parity, low/high, decade buckets, key gaps, repeated values) and `core/services/rolling_windows.py` (last-N-draws / last-N-Tuesdays-or-Fridays selection). Pure infrastructure — **not a prediction strategy, does not generate keys**, just reshaping/counting/selecting over data the caller already loaded.

**✅ Biblioteca dos Artefactos (Artifact Library)** — `core/services/artifact_schema.py`, `artifact_registry.py` and `artifact_inspiration.py`; 15 founding narrative artifacts, every one verified to have zero effect on algorithms, results or probabilities (see [The Artifact Library](#the-artifact-library-biblioteca-dos-artefactos) below).

**✅ Candidate Provenance, Evaluation & Performance** — `core/services/candidate_provenance.py` (normalizes any already-persisted candidate record into one canonical `CandidateKey`, across the 18 real `origem` values found in the archive), `candidate_evaluation.py` and `candidate_performance.py` (strictly retrospective measurement/aggregation against a caller-supplied target — never generation, fitness, Council or selection; see [Candidate Analysis Layer](#candidate-analysis-layer-commits-15-19) below).

**✅ Minotauros** — a new Clerics lineage (Commit 19) with **key persistence** instead of exploration: survivors keep exactly the same key every generation, and a bred descendant can inherit its Minotauro parent's key. Not a new voting faction — see [Candidate Analysis Layer](#candidate-analysis-layer-commits-15-19) below.

**✅ Backtest Lab & Temporal Safety** — `core/services/backtest_lab.py` (Commit 20) certifies that a candidate provably existed before a target draw's official reveal; `historical_simulation_source.py` (Commit 22) and `historical_ariadne_source.py` (Commit 23, plus a new `Ariadne(scrolls=...)` temporal mode) extend the same timezone-aware cutoff to the versioned historical dataset and to Ariadne's pergaminho-based methods; `temporal_memory_boundary.py` (Commit 24) extends it again to persistent memory (Heroes/Legends recognition, legacy Legend resurrection). See [Temporal Safety and Backtest Lab](#temporal-safety-and-backtest-lab-commits-20-24) below.

**✅ Backtest Orchestrator V1** (Commit 25, `6504425`) — `core/services/backtest_orchestrator.py`: the first real, end-to-end retrospective run — builds a temporally-scoped context from a `HistoricalBacktestBoundary` (draw_id + draw_datetime only, no numeros/estrelas field exists on the type at all), runs the real, unmodified Clerics genetic algorithm, freezes the result, and only then reveals the target's key for evaluation. `VERIFIED` mode structurally requires uncertified persistent memory (Artefactos Vivos, Arca, Monges e Escribas) to be unreachable; `EXPLORATORY` mode opts out explicitly. Clerics-only in V1. See [Backtest Orchestrator & Campaign Runner](#backtest-orchestrator--campaign-runner-commits-25-27--v2--arena) below.

**✅ Zombie** (Commit 26, `71be259`) — a new Clerics lineage with **territorial Monte Carlo**: each Zombie is born with a small, heritable, mutable pool of numbers/stars (its "territory") and explores it via Monte Carlo (300 simulations by default) using the same `fitness()` already used by Werewolves. Not a new voting faction, like Minotauro. Clerics now has **10** archetypal lineages, not 9.

**✅ Campaign Runner V1** (Commit 27, `6308fc1`) — `core/services/backtest_campaign.py`: runs a grid of independent historical backtests over `target × seed × generations` for Clerics, aggregating results by race with purely descriptive statistics — no scores, no p-values. Race discovery is fully dynamic, never a fixed list.

**✅ Campaign Runner V2 — multi-system** (`cb5087e`) — `core/services/backtest_generators.py` generalizes the Campaign Runner to 6 systems (Clerics, Skeletons, Melforks, Axiomantes, Pantheon, and a new Acaso Puro/Pure Chance baseline) via external adapters that call each faction's original function unmodified — zero changes to any faction algorithm or to `backtest_orchestrator.py`. System/strategy discovery is dynamic (a `GENERATORS` registry, not an enumeration); `generations=None` is represented honestly for systems without that axis (Skeletons, Axiomantes, Pantheon, Acaso Puro).

**✅ Arena layer** (`88bfb28`) — `core/services/backtest_arena.py`: normalized cross-system/cross-strategy comparison. Official Key (neutral RNG selection, one per `system × strategy × target × seed` cell, never aggregated across seeds), Equal Budget sampling (N candidates without replacement, within one cell), and abstention/participation accounting (`cells_attempted`/`cells_participated`/`cells_succeeded` vs. coarser `targets_observed`/`targets_with_participation`, so a strategy that rarely participates can never look like it "always succeeds"). See [Backtest Orchestrator & Campaign Runner](#backtest-orchestrator--campaign-runner-commits-25-27--v2--arena) below.

**✅ Astérias de Thalássia + `attempted_races`** (`cf22d7e7`) — two conditional lineages testing a star-pair-transition hypothesis (Astéria Abissal, Astéria das Marés with marginal backoff), plus a generic contract extension so a strategy that abstains in 100% of cells is still discoverable in `ArenaStrategySummary` instead of silently disappearing. **[IMPLEMENTED]**

**✅ Star Contribution Trial** (`d9b8c104`) — `core/services/star_contribution_trial.py`: a paired experiment holding the 5 neutral numbers fixed and swapping only the stars, isolating the star-selection hypothesis's real effect. **[IMPLEMENTED]**

**✅ Arena Oficial — Temporada 2 / Guerra das Estrelas** (`e4624e65`) — real campaign, 54 targets × 3 seeds, 324/324 cells, 0 failures, 9060 candidates. Hypothesis tested, **not confirmed** — no statistically clear advantage over Acaso Puro. **[EXPERIMENTALLY TESTED]** — see [Arena Seasons](#arena-oficial--temporadas-1-3) below.

**✅ Treefolks V2 — As Grandes Florestas** (`f32b63b3` + `747f12dd`) — 5 real Florestas (Yggdrasil/LSTM, Dodona/Bayes, Brocéliande/Markov, Tír na nÓg/Monte Carlo, Fortuna/control), a shared scores contract and key constructor, per-Floresta namespaced RNG. Yggdrasil's optional PyTorch dependency (`torch==2.13.0`, CPU-only) is validated for real — the LSTM trains and produces scores. **[IMPLEMENTED]** — see [Treefolks V2](#treefolks-v2--as-grandes-florestas) below.

**✅ Arena Oficial — Temporada 3 / Guerra das Florestas** (`85a65fec`) — real campaign, same 54 targets × 3 seeds, 162/162 valid cells, 0 failures, 16140 candidates. No Floresta showed a statistically clear advantage over the Fortuna control; Fangorn/Ensemble remains unbuilt roadmap, not auto-unlocked by these results. **[EXPERIMENTALLY TESTED]** — see [Arena Seasons](#arena-oficial--temporadas-1-3) below.

**✅ Testing** — 1125 tests across 46 modules (`python -m unittest discover -s tests`), zero skipped.

---

## Architecture

```
Ariadne (data broker)
    │
    ├── Eternal Library (persistent knowledge)
    │       ├── Scrolls        — one JSON per real draw (1,974 total)
    │       ├── Books          — derived analytics (frequencies, pairs, triples)
    │       ├── Sources        — immutable annual datasets (2004–2026)
    │       ├── Indices        — pairs and triples index
    │       └── Relics         — artefacts that persist across simulation runs
    │
    ├── Factions (independent agents)
    │       ├── Each faction queries Ariadne — never reads raw data directly
    │       ├── Each faction generates a candidate key using its own strategy
    │       └── Each faction submits its candidate with a confidence weight
    │
    └── Council (consensus mechanism)
            ├── Filters candidates
            ├── Votes (weighted)
            └── Produces the final key
```

---

## Factions

Each faction represents a distinct statistical philosophy:

| Faction | Strategy |
|---------|---------|
| **Clerics** | Genetic algorithm — 72 individuals evolve over 14 generations across 10 archetypal lineages, including Minotauro's key-persistence lineage (Commit 19) and Zombie's territorial Monte Carlo lineage (Commit 26) |
| **Melforks** | Specialised genetic algorithm for balanced key generation |
| **Vampires** | Linhagem Sanguínea: frequent triples + balance; Linhagem Sombria: consecutive triples |
| **Gargoyles** | Linhagem de Pedra: consistent pairs; Linhagem do Espelho: symmetry and consecutive numbers |
| **Treefolks** | Hypothesis testing against Ariadne — measures "statistical ghosts" (low-confidence patterns) |
| **Dwarves** | Combinatorial analysis by clan |
| **Faeries** | Weighting by everyday number patterns |
| **Werewolves** | Monte Carlo fitness simulation (lunar phase influence) |
| **Skeletons** | Moving window of the 25 most relevant numbers |
| **Chronomancers** | Temporal energy of the simulated draw instant |
| **Black Squad** | Anti-popularity strategy using a stolen grimoire |
| **Elven Order** | Recovery missions — retrieves corrupted artefacts and scrolls |
| **Kors de Elarion** | Four observers consulting exclusively Ariadne (V7.2) |
| **Cartographers of Chaos** | Five analysts producing analytical books for other factions (V8) |
| **Axiomantes de Nemerion** | Feistel permutation over 139M combinations — finds inédita keys by statistical profile (V8.1) |
| **Druids, Moon Priests, Star Gazers, Shamans, Witches, Seers, Oracles, Bone Readers** | Mystics (V10) — placeholders only, always abstain. See [Mystics](#mystics-v10) below |

### Kors de Elarion (V7.2)

Four named observers, each with a different lens on historical data:

| Kor | Name | Strategy |
|-----|------|---------|
| White | Aelyra dos Silêncios | 15 most overdue numbers |
| Red | Kael da Chama Fria | Least frequent numbers (full history) |
| Green | Sylvara das Passagens | Penultimate → last draw transition pattern |
| Black | Nyxara das Sombras | Weekly ISO echo — writes weekly papyrus to library |

### Cartographers of Chaos (V8)

Five analysts that **do not generate keys** — they produce analytical books consulted by other factions:

| Cartographer | Book | Analyses |
|-------------|------|---------|
| Eldran | Stellar Constellations | Co-occurrence network, centrality, top pairs |
| Vesara | Eternal Cycles | Average/max/min delay per number, full cycles |
| Lirien | Trends and Currents | Window trends (50/100/200), lows vs highs, digit endings |
| Thalvos | Expected Chance | Monte Carlo (100K) — real vs random expected |
| Oryn | Sequential Echoes | Markov transitions, neighbourhood, consecutive sequences |

### Axiomantes de Nemerion (V8.1)

Guardians of the Labyrinth of 139,838,160 chambers. They traverse the full Euromillions combinatorial universe using a reproducible Feistel permutation — without iterating 139M entries in memory.

**The Ritual of Thirty Echoes:**
1. Ask Ariadne for the last known draw — the **marco** (anchor)
2. Compute the marco's position in the Feistel sequence (seed-dependent)
3. For each draw in the period: compute position → split into echoes (before marco) vs after
4. Compare observed coverage against a pure random process baseline
5. **Portal of Undrawn Keys** — opens if coverage ≥ 50% and excess ≥ 0%
6. If Portal opens: compute **Echo Profile** and score N candidate inédita keys

**Scoring (0–100 pts):**

| Criterion | Points |
|---------|--------|
| Sum within preferred range | 20 |
| Dominant parity (even/odd) | 15 |
| Dominant low/high split | 15 |
| Affinity with top-5 frequent numbers (peak at 3/5) | 20 |
| Affinity with frequent stars | 15 |
| Gap average close to profile | 10 |
| Amplitude close to profile | 5 |
| Bonus: 1–2 rarely seen numbers | +5 |

**Mathematics:**

| Concept | Value |
|---------|-------|
| Universe | C(50,5) × C(12,2) = 139,838,160 combinations |
| Algorithm | Feistel (_H=11826, 4 rounds, Wang hash) |
| Complexity | O(H) — H = number of historical draws; no 139M iteration |
| Default candidates evaluated | 50,000 per run |

---

### Mystics (V10)

A new race, `races/mystics/`, restoring Project Ariadne's original V1
spirit: intuition, rituals and ancient tradition alongside statistics.
Two lineages, eight orders, all currently **architecture and lore
only — no prediction algorithm implemented yet**:

| Lineage | Orders | Future analytical role |
|---|---|---|
| 🌿 Nature Mystics | Druids, Moon Priests, Star Gazers | lunar phases, seasons, solstices/equinoxes, ISO week cycles, celestial symbolism |
| 🔮 Prophecy Mystics | Shamans, Witches, Seers, Oracles, Bone Readers | rare events, ensemble/hybrid strategies, trend detection, proposal meta-analysis, ritual pseudo-randomness |

Every order has a matching `factions/<order>/` plugin (`manifest.json`
+ `council.py` + `strategy.py` + `README.md`) that registers correctly
through `FactionRegistry` and **always abstains** — the same valid,
non-error abstention behaviour as Axiomantes with a closed portal.
Lore, characters (16, two per order) and artifacts (16, two per order)
live in `races/mystics/{lore.md, orders.json, characters.json,
artifacts.json}`, with a short README per order under
`races/mystics/nature/` and `races/mystics/prophecy/`.

**By design, these factions must never outperform the mathematical
ones** — they're alternative methodologies, not a shortcut, and every
proposal (mystical or mathematical) is filtered, voted and backtested
through exactly the same Council, Judges and Backtesting engine. See
[`races/mystics/lore.md`](races/mystics/lore.md) for the full history.

---

## Ariadne — the data broker

All factions query data exclusively through Ariadne. No faction reads raw datasets directly. This enforces clean data access and makes all queries cacheable and reproducible.

```python
from library.ariadne.engine import Ariadne

a = Ariadne()

# Scrolls (real draws)
a.full_history()                    # full history
a.full_history(desde="2024-01-01") # since date
a.full_history(ultimos=100)         # last N draws
a.last_known_key()                  # most recent draw

# Indices
a.pairs(limite=10)          # most frequent pairs
a.triples(limite=10)        # most frequent triples

# Number analysis
a.overdue_numbers(15)               # 15 most overdue numbers
a.least_frequent_numbers(20)        # 20 least frequent
a.transition_pattern()              # penultimate→last transition pattern
a.weekly_echoes(semana_iso=28)      # weekly echoes (ISO week)

# 2026 scrolls (with astronomy metadata)
a.scroll_state(55)
a.search_moon("Lua cheia")

# Kors papyrus
a.create_papyrus(semana_iso=28, dados={...})
```

**Temporal mode (Commit 23):** `Ariadne(scrolls=<already-loaded, cutoff-filtered collection>)` — when `scrolls` is given, the seven pergaminho-based methods above operate exclusively over that frozen collection, with zero further reads of `library/scrolls/`. Omit `scrolls` and behaviour is exactly LIVE/NORMAL, unchanged. `pairs()`/`triples()`/`numero()`/`least_frequent_numbers()` (backed by `library/indexes/*.json`, which carry no timestamp at all) raise `RuntimeError` on a temporal instance rather than silently answering from an uncut global index. See [Temporal Safety and Backtest Lab](#temporal-safety-and-backtest-lab-commits-20-24) below.

---

## The Eternal Library (persistent knowledge)

```
library/
├── ariadne/            ← Ariadne engine (engine.py)
├── sources/            ← immutable annual datasets 2004–2026
├── scrolls/
│   ├── 2004/ … 2025/   ← compact format (1,929 scrolls)
│   └── 2026/           ← full format with astronomy (67 scrolls)
├── books/
│   └── cartographers/  ← 5 analytical books (Cartographers)
├── indices/            ← pairs, triples, frequencies, moon phases
├── cache/              ← Ariadne query cache
└── black_kors/
    └── papyri/         ← Nyxara's weekly papyri
```

---

## Dashboard Dataset

`core/services/dashboard_data.py` is a pure data-transformation layer for research/analysis. It never reads a file, never touches a Registry, and never computes randomness — every function takes already-loaded plain data (the result of a Registry's `load_all()`, or an already-parsed historical dataset JSON) and reshapes it into small, frozen dataclasses (tuples, not lists, so a produced row can never be mutated through a reference into the source data).

| Row / builder | Produces | Source |
|---|---|---|
| `build_heroes_rows()` | `HeroRow` | `HeroRegistry().load_all()` |
| `build_legends_rows()` | `LegendRow` | `LegendRegistry().load_all()` |
| `build_key_base_rows()` | `DrawRow` | `sorteios` from the 2026 historical dataset |
| `build_characters_rows()` | `CharacterRow` | `races/*/characters.json` |
| `build_houses()` | `HouseEntry` | `races/*/lineages.json` cross-referenced with the population archive |
| `build_executive_summary()` | `ExecutiveSummary` | Heroes/Legends counts + Economy |
| `build_economy_rows()` / `build_economy_summary()` | `EconomyDrawRow` / `EconomySummary` | `estatisticas_financeiras`/`premios` in the 2026 dataset |
| `build_prize_category_rows()` / `build_prize_category_summary()` | `PrizeCategoryRow` / `PrizeCategorySummary` | `premios.categorias` in the 2026 dataset |
| `build_generations_rows()` | `GenerationRow` | a single execution's per-individual generation records (caller-scoped) |
| `build_frequencies_rows()` | `FrequenciesRow` | any already-loaded set of draws — the same shape `build_key_base_rows()` reads |
| `build_dashboard_dataset()` | `DashboardDataset` | Composes all of the above — never calls the builders itself |

**Economy and Prize Categories are real, not synthetic.** The official 2026 dataset only has complete financial/prize-category data for 15 of its 67 draws — confirmed via the dataset's own `qualidade_dados` flags, never inferred from whether a value happens to be non-null. Every sum, mean, minimum and maximum in `EconomySummary`/`PrizeCategorySummary` is computed only over the draws that actually have that field; a field with zero real observations resolves to `None`, never an invented `0` or an estimate. `PrizeCategoryRow` always emits exactly 13 rows per draw — the fixed, official Euromillions prize-tier table, a game rule rather than a per-draw fact — with only the observed winner counts ever `None`.

`GenerationRow.fitness_medio`/`fitness_maximo`/`fitness_minimo` are always `None` — the real prediction archive never persisted a per-individual score, so there is nothing honest to compute. `GenerationRow.jaccard_medio_vs_geracao_anterior` is also still always `None` — deliberately deferred until the project defines a canonical similarity metric. `FrequenciesRow.atraso_atual` **is now computed** (0 in the most recent draw, N draws ago, `None` if never observed) via `current_delay()` from `core/services/statistical_profiles.py` — this requires `draw_records` to be chronologically ordered (oldest → newest); frequency fields remain order-independent. Both builders take data the caller already scoped (which execution, which draws) — neither decides that on its own.

### Excel Export

`dashboard/excel_export.py` consumes an already-built `DashboardDataset` — never Heroes/Legends/datasets/registries directly — and produces a `.xlsx` workbook with 8 sheets (Executive Summary, Heroes, Legends, Characters, Houses, Key Base, Economy, Prize Categories):

```python
from dashboard.excel_export import export_to_excel

export_to_excel(dataset, "dashboard.xlsx", project_version="V13", generated_at="2026-08-19")
```

`Generations`/`Frequencies` have real builders (above) but no sheet of their own yet. There is currently no script in the project that assembles a real `DashboardDataset` from live Heroes/Legends/datasets/races and calls `export_to_excel()` — that wiring doesn't exist yet; only tests and one-off validation construct a real dataset today.

---

## The Artifact Library (Biblioteca dos Artefactos)

A **purely narrative, cerimonial** collection, distinct from the older `artifacts/` package (`ark.py`/`living.py`/`relics/`/`amulets/`, V4-era, mechanically tied to simulation state). `library/artifacts/` never influences a key, a vote, or a probability — every one of its 15 founding entries carries `altera_algoritmo`, `altera_resultados` and `altera_probabilidades`, all explicitly `false`, verified structurally at every layer below, not just asserted in prose.

- **`library/artifacts/entries/*.json`** — the only primary source, 15 founding artifacts (Coin of Midas, Ladybug of Sylvaris, Star of Lyra, Rainbow Fragment of Iris, Clover of Aethoria, five Horseshoes, Daruma of Perseverance, Imperial Victory Brandy, Celestial Blue Panties, Lotus of Tranquility, Codex of Eternal Fortune). Never rewritten by any code in this layer.
- **`core/services/artifact_schema.py`** — `normalize_artifact()` reshapes any of the 15 genuinely heterogeneous, independently-authored source shapes into one small `ArtifactRecord`: a fixed core (id, nome, tipo, raridade, estado, criador, energia, lore, historia, tags…) plus two escape hatches that guarantee nothing is ever lost — `extras` (every non-core field, verbatim) and `raw` (the untouched original dict). Never invents a default for an absent field; missing means `None`, never a guess.
- **`core/services/artifact_registry.py`** — `load_all_artifacts()` (duplicate-id and filename/id-mismatch detection), `ArtifactRegistry` (`by_id`/`by_type`/`by_tag`/`by_creator` queries, no randomness anywhere), and `build_index()`/`write_index()`, which derive `library/artifacts/LIVRO_DOS_ARTEFACTOS.json` — always regenerated from `entries/`, never hand-edited, never a source of truth itself.
- **`core/services/artifact_inspiration.py`** — `generate_inspiration(record, seed)`, a deterministic (`random.Random(seed)`, never the global `random`) narrative "inspiration seed" generator for brand-new character concepts loosely inspired by an artifact. Explicitly forbidden — and defensively filtered, not just documented — from suggesting number/star picks, predicting a draw, or referencing algorithm/result/probability changes; never creates or edits a Hero or a Legend; performs no file I/O at all.

---

## Candidate Analysis Layer (Commits 15-19)

A small family of pure services, separate from both the Dashboard
Dataset and the Artifact Library, for reasoning about candidate keys
that already exist — never for generating one.

| Service | Does |
|---|---|
| `core/services/statistical_window_profile.py` | Composes `statistical_profiles.py` + `rolling_windows.py` over one already-selected window — zero new formulas |
| `core/services/candidate_provenance.py` | `normalize_candidate_record()` — normalizes an already-persisted record (any of the 18 real `origem` values in the archive) into one canonical `CandidateKey` |
| `core/services/candidate_evaluation.py` | `evaluate_candidate()`/`evaluate_candidates()` — measures a `CandidateKey` against a caller-supplied target |
| `core/services/candidate_performance.py` | `summarize_candidate_performance()` — pure aggregation over already-produced `(CandidateKey, CandidateEvaluation)` pairs |

**Mandatory temporal boundary:**

```
historical data up to X-1 → train/evolve/generate → freeze candidates → reveal draw X → evaluate → summarize performance
```

`candidate_evaluation.py` and `candidate_performance.py` have no concept of a draw, a date, or a dataset — they only ever see whatever target the caller already resolved and passed in explicitly. This is what makes look-ahead structurally impossible: they are **strictly retrospective/experimental** and never influence generation, fitness, the Council, or key selection.

**Minotauros (Commit 19)** — a new Clerics lineage, not a new voting faction. Survivors keep exactly the same key every generation (`h.keys[-1]`); a bred descendant can inherit a Minotauro parent's key at reproduction time (deterministic p1-over-p2 precedence, no extra randomness, no mutable aliasing between generations); a non-Minotauro child never inherits; a founder without an inherited key generates its own, the same way other lineages do; Minotauros never go through `aplicar_conhecimento()`; fitness, elimination and provenance (`race="Minotauro"`, `source_type="evolutionary_individual"`) are all unchanged. See `CLAUDE.md`'s "Camada de Proveniência, Avaliação e Desempenho de Candidatos (Commits 15–19)" for the full specification.

**The Backtest Experiment Lab now exists** (Commit 20, see [Temporal Safety and Backtest Lab](#temporal-safety-and-backtest-lab-commits-20-24) below) — it is no longer on the "not implemented" list. **Zombie also now exists** (Commit 26, see [Current Status](#current-status-v13--commits-25-27--campaign-runner-v2--arena) above) — no longer an idea either. Still ideas only, none exists as code or a closed spec today: future Necromancer lineages (which must first be audited against the existing `necromancia_estatistica` Legend-resurrection mechanism in `main.py` to avoid duplicating it, and against the temporal-safety work already done for legacy Legend resurrection in Commit 24), and a lab/hybrid-"superspecies" concept.

---

## Temporal Safety and Backtest Lab (Commits 20-24)

Five sequential commits answering a different question from the Candidate Analysis Layer above: given an already-revealed historical target X, how do you build and measure an experiment without letting information from after X leak in. Two distinct guarantees run through all of them:

- **Fronteira A** ("training/evolution/fitness/Council only ever saw history strictly before X") — **not** certified by any of this; it's an upstream problem in `world/engine/builder.py`, audited in Commit 21, not yet fixed.
- **Fronteira B** ("the candidate/memory provably existed before X was revealed") — what every service below actually certifies, always via `< cutoff_datetime` (never `<=`), always requiring a timezone-aware cutoff (`ValueError` on naive), never inferring availability from anything but an honest timestamp already on the record.

| Commit | Service | Certifies |
|---|---|---|
| 20 | `core/services/backtest_lab.py` | `freeze_backtest_candidates()`/`evaluate_backtest_candidates()`/`summarize_backtest()` — a candidate existed before the target's official reveal. `freeze_backtest_candidates()` never even receives the target's numbers/stars as a parameter — the winning key structurally cannot leak into the freezing step. |
| 21 | — (audit only) | Found the real gaps the next three commits close: `main.py` never reads the versioned dataset; Ariadne reads `library/scrolls/`/`library/indexes/` with no cutoff; a real look-ahead bug in Legend resurrection. |
| 22 | `core/services/historical_simulation_source.py` | `available_at()`/`visible_draws()`/`build_historical_context_for_backtest()` — the same guarantee over `datasets/historical/euromillions/`, adapted to the flat shape the simulator expects. Not wired into `main.py`/`world/engine/builder.py` yet. |
| 23 | `core/services/historical_ariadne_source.py` + `Ariadne(scrolls=...)` | The same guarantee for `library/scrolls/` — a new temporal mode on the `Ariadne` class itself (see the "Ariadne — the data broker" section above). |
| 24 | `core/services/temporal_memory_boundary.py` | The same taxonomy (`verified`/`legacy`/`ineligible`/`unresolved`) for persistent memory — Heroes/Legends recognition timestamps, legacy Legend resurrection. |

**A key distinction audited in Commit 24**: `candidate existed_at` (when a predicted key was generated) ≠ `recognition/promoted_at` (when the system recognised it was good) ≠ `memory_record available_at` (when that recognition was actually written to disk) — no system in this project tracked the third one before this commit. `evaluate_heroes.py` now writes `recognized_at`; `legend_evaluation.py:evaluate_group()` now requires a caller-supplied `promoted_at`. Both are forward-only — existing Hero/Legend records have neither field and stay `legacy` forever, no retroactive dating.

**Necromancy** (`orders/black_squad/black_mages.py:tentar_ressuscitar_lenda(config, events, cutoff_datetime=None)`) is the first real consumer: omit `cutoff_datetime` and behaviour is exactly LIVE/unchanged; supply it and no Legend recorded (`registado_em`) after the cutoff can ever be resurrected.

**Explicitly not certified, by decision** — the Black Squad's grimoire, the Elven Order's `estado_ordem.json`, and artifacts' current top-level state (`artifacts/relics/*.json`) are cumulative aggregates with no timestamp at the fact level actually consulted during generation, even though the individual events feeding them do have real timestamps. `artifacts/living.py`, `artifacts/ark.py`, `orders/black_squad/persistence.py` and `orders/elven_order/ninjas.py` never import `temporal_memory_boundary` — a standing, tested proof, not just documentation.

**Not wired into `main.py`** — each commit is a standalone, tested service. A real backtest orchestrator **does** now exist and consumes several of them directly (Commit 25) — see the next section.

---

## Backtest Orchestrator & Campaign Runner (Commits 25-27 + V2 + Arena)

Four sequential pieces, built on top of the Temporal Safety layer above, answering a new question: not just "can we certify a candidate existed before X", but "let's actually run the retrospective experiment, at scale, across systems, and compare the results fairly".

### Backtest Orchestrator V1 (Commit 25, `6504425`)

`core/services/backtest_orchestrator.py` — the first real end-to-end retrospective run. `prepare_backtest_run(cfg, boundary, *, mode, ...)` builds a temporally-scoped context (reusing Commits 22/23 unmodified) from a `HistoricalBacktestBoundary(draw_id, draw_datetime)` — a type with **no `numeros`/`estrelas` field at all**, so the winning key is structurally unreachable during preparation, not just unlikely to leak. `run_clerics_backtest()` then runs the real, unmodified `factions.clerics.algorithm.execute()`. Only `reveal_and_evaluate()` — called after freezing — ever receives the full target.

Two modes: `mode="verified"` raises `ValueError` (listing every violation) unless Artefactos Vivos, a Redescoberta-enabled Arca, and every Monges e Escribas access list are structurally disabled — `mode="exploratory"` opts out of that check explicitly, never silently. Clerics-only in V1; every other faction was audited and found out of scope (see [Campaign Runner V2](#campaign-runner-v2--multi-system-cb5087e) below for which of them can join later, and why some structurally cannot).

### Zombie (Commit 26, `71be259`)

A new Clerics lineage — not a new voting faction, like Minotauro. Each Zombie is born with a small, heritable, mutable territory (a pool of numbers/stars) and explores it via Monte Carlo (300 simulations by default, same `fitness()` Werewolves already use). Clerics now has **10** archetypal lineages.

### Campaign Runner V1 (Commit 27, `6308fc1`)

`core/services/backtest_campaign.py` — `CampaignSpec`/`run_campaign()` run a grid of independent historical backtests over `target × seed × generations` for Clerics, reusing the orchestrator above unmodified. `summarize_by_race()`/`summarize_by_race_and_generations()` aggregate the pooled results by race — **no fixed race list anywhere**: a race is discovered the moment it appears in a `CandidateKey.race`, including races that don't exist in the real project (proven with synthetic races in tests) and double-resurrected `"Renascido Renascido X"` individuals (a genuine finding from the first real baseline campaign against 065-067/2026).

### Campaign Runner V2 — multi-system (`cb5087e`)

`core/services/backtest_generators.py` generalizes the Campaign Runner beyond Clerics via external adapters — **zero changes to any faction algorithm and zero changes to `backtest_orchestrator.py`**. Each adapter calls the faction's original function exactly as it exists, preserving its own RNG contract (global `random` for Melforks, `ctx['rng']` for Skeletons/Pantheon, no RNG at all for Axiomantes' Feistel walk).

| System | Adapter calls | Notes |
|---|---|---|
| Clerics | `run_clerics_backtest()` (Commit 25, unmodified) | Only system with a `generations` axis |
| Skeletons | `factions.skeletons.algorithm.create_representatives()` | No history/Ariadne dependency at all |
| Melforks | `factions.melforks.algorithm.melforks()` | Reports its own real `geracoes_chaves`, never swept as a campaign axis |
| Axiomantes | `factions.axiomantes.ritual.execute_ritual()`, given the **temporal** Ariadne only | `[AXIOMANTES] guardar_experiencia` forced off — a campaign never writes to `experiments/axiomancers/runs/` |
| Pantheon | `orders.pantheon.{mages,druids,djinns,aion}` | Mago/Druida/Djinn/Aion become individually distinguishable via `CandidateKey.race`, purely inside this adapter — the real archive still collapses the first three under `origem="ser_superior"`, unchanged |
| Acaso Puro | pure `random.Random(seed)` sampling, no history/Ariadne at all | The statistical-floor baseline `benchmarks/random/README.md` had reserved since early in the project, never implemented until now |
| Astérias (`cf22d7e7`) | Conditional star-pair transition model, `ctx['historico']` only | Two lineages, Astéria Abissal (abstains under `n(P)<5`) and Astéria das Marés (explicit marginal backoff); see [Arena Seasons](#arena-oficial--temporadas-1-3) below |
| Treefolks V2 (`f32b63b3`/`747f12dd`) | 5 real Florestas, each with its own namespaced RNG stream | LSTM (optional PyTorch, CPU-only), Bayes, Markov, Monte Carlo, and a Fortuna control; see [Treefolks V2](#treefolks-v2--as-grandes-florestas) below |
| Academia (Tyche) | `core.services.academia.tyche.run_tyche()`, uniform control | Permanent generator key `"academia"`; see [Academia Arcana de Nemerion](#academia-arcana-de-nemerion) below |
| Academia (Mnemosyne) | `core.services.academia.mnemosyne.run_mnemosyne()`, Laplace α=1 frequency weighting | Generator key `"academia_mnemosyne"`; see [Academia Arcana de Nemerion](#academia-arcana-de-nemerion) below |

Vampires, Gargoyles, Kor Vermelho and Werewolves were explicitly audited and are **not** registered — see [Roadmap](#roadmap--future-vision) below for why.

### Arena layer (`88bfb28`)

`core/services/backtest_arena.py` — normalized comparison across systems/strategies with unequal candidate budgets, so a strategy that produces thousands of candidates never automatically "wins" over one that produces five.

- **Official Key** — one neutral, RNG-selected key per `(system, strategy, target, seed)` **cell**, never aggregated across seeds (each seed is an independent experimental repetition). The Arena's own RNG (`_arena_rng`, SHA-256-derived, namespaced by purpose) never touches or is touched by any generator's own random stream.
- **Equal Budget** — samples exactly N candidates without replacement, within one cell; `n_used` is always reported next to `n_requested`, never padded.
- **Abstention accounting** — `ArenaSystemAttendance` (system-level, catches total abstention — e.g. Axiomantes' Portal closed at every target — even when no strategy label was ever produced) and `ArenaStrategySummary` (`cells_attempted/participated/succeeded` vs. coarser `targets_observed/targets_with_participation`). `success_rate_when_participating` is `None`, never `0.0`, when a strategy never participated — an undefined rate is never rendered as "tried and failed".
- **Campeão do Tesouro** (financial ranking) is a documented **contract only** — no prize-value-per-category table exists anywhere in the project, and 065-067/2026 (like most real draws) have no financial data at all.

---

## Treefolks V2 — As Grandes Florestas

**[IMPLEMENTED]**, commits `f32b63b3` (implementation) + `747f12dd` (Yggdrasil validated with PyTorch actually installed). A genuinely new system (`"treefolks_v2"`, eighth entry in `GENERATORS`) — **not** a migration of the original Treefolks: `factions/treefolks/algorithm.py` (the original voting faction, unchanged) is 100% narrative — `"modelo"` was only a randomly-sampled text label, the key itself always came from the same frequency+delay+noise heuristic regardless of which label was drawn. Treefolks V2 lives entirely in `core/services/treefolks_v2/`.

**Sistema → Floresta → Treefolk architecture**, expressed through the existing `CandidateKey` shape with zero new fields: `system="treefolks_v2"` (fixed), `source_name="treefolks_v2"` (fixed), `race="Floresta — Treefolk"` (a single composed string, e.g. `"Yggdrasil — LSTM-v1"`).

**Shared scores contract**: `TreefolkScores(number_scores: {1..50}, star_scores: {1..12})` — never a real physical probability, an "experimental belief". **Single shared key constructor** (`build_key_from_scores()` in `common.py`) used by all 5 Florestas without exception — differences in Arena performance come from the model, never from the constructor. **Per-Floresta namespaced RNG** (`forest_rng()`, SHA-256) — a deliberate departure from the single-shared-stream convention Astérias/Pantheon use, because Yggdrasil's training consumes a variable amount of randomness that would otherwise silently desynchronize every other Floresta.

| Floresta | Method | Frozen V1 hyperparameters | Dependencies |
|---|---|---|---|
| **Yggdrasil — LSTM-v1** | Real LSTM, official `torch.nn.LSTM`/`nn.Linear` (never hand-rolled backward) | `W=20, hidden_size=32, epochs=25, min_training_pairs=60, Adam(lr=1e-3, betas=(0.9,0.999))`, full-batch, `BCEWithLogitsLoss` | **Optional PyTorch**, isolated to `yggdrasil.py`, CPU-only, `torch==2.13.0` (pinned; the original `2.4.1` pin had no build for this environment's Python 3.14.6, updated after discovering that for real) |
| **Dodona — Bayes-v1** | Beta(α,α) prior per number/star, posterior mean | `α=1` | None |
| **Brocéliande — Markov-v1** | State = one single number/star from the previous draw (never the full combination); per-query distribution, arithmetic mean across the previous draw's 5 numbers/2 stars | `α=1`; abstains at `len(historico)<2` (structural, not a chosen threshold) | None |
| **Tír na nÓg — MonteCarlo-v1** | Empirical frequency+delay weights → simulation → real scoring via `core.services.fitness.fitness()` (reused, proven VERIFIED-safe) → score = elite frequency | `N_SIMULACOES=1000`, `TOP_FRACTION=0.10` (`ELITE_SIZE=100`), canonical `(numeros, estrelas)` tie-break, never RNG order | None |
| **Fortuna — Controlo-v1** | Uniform scores → pure uniform sampling | — | None |

**Fangorn / Ensemble** — roadmap only, no module, no placeholder, blocked until real results exist for all 5 Florestas (Temporada 3 running does **not** auto-unlock it).

**Anti-look-ahead**: same `range(len(historico)-1)` discipline as Astérias; Yggdrasil specifically uses `range(_W-1, len(historico)-2)` — `historico[-1]` is structurally never a training label, only the final inference window — proven by a sentinel test. `fitness()`/`calculate()` were proven VERIFIED-safe by inspection + test **before** Tír na nÓg was implemented (pure functions, zero I/O, zero access to Ariadne/persistent memory).

**`attempted_races`** reused with zero extension — every Floresta always declares itself, even in full abstention (Yggdrasil without PyTorch installed, or insufficient history; Brocéliande at `len(historico)<2`).

**Piloto das Florestas** (isolated smoke test, real data, mocked `RUNS_DIR`, zero official manifests): all 5 Florestas ran the full pipeline, determinism confirmed (repeated cell → identical candidates/`attempted_races`), zero real manifests created.

**Tests**: 73 new (62 isolated `test_treefolks_v2_*.py` + 11 integration in `test_backtest_generators.py`). At `f32b63b3`: 1126/1126 OK, 6 skipped (no PyTorch installed yet). After installing `torch==2.13.0` and fixing 2 tests that depended on ambient environment state instead of `mock.patch`-forcing it (`747f12dd`): **1125/1125 OK, zero skipped** — Yggdrasil validated actually training, deterministic, correctly restoring global `torch.use_deterministic_algorithms` state.

---

## Arena Oficial — Temporadas 1-3

Three real, executed campaigns, each with a mechanically pre-registered target rule (never chosen by anticipated result), persisted real run manifests, and a written report — no campaign ever declared a winner.

| Temporada | Question | What it actually concluded |
|---|---|---|
| **1 — Baseline multissistema** (`ae9ccd81`) | Do the 6 original systems differ under normalized comparison? | At Equal Budget N=1, **0/240 relevant hits** across every Clerics generation tested — the apparent "more generations = better" trend in raw numbers was a volume artifact (coupon-collector effect), not real signal. |
| **2 — Guerra das Estrelas** (`e4624e65`) | Does the Astérias conditional star-pair-transition hypothesis beat Acaso Puro on stars? | Hypothesis tested, **not confirmed** — Wilson intervals overlap at every N; Star Contribution Trial's melhorou/piorou ratio sits close to 50/50 in all 3 lineages. |
| **3 — Guerra das Florestas** (`85a65fec`) | Do 5 real, distinct methodologies (LSTM, Bayes, Markov, Monte Carlo) beat the Fortuna control on the full key? | No statistically clear advantage over Fortuna, in any of the 5 Florestas, across any of the 10 comparisons (4 primary + 6 exploratory). |

**Temporada 2** ran 54 targets × 3 seeds × `{asterias, acaso_puro}` — 324/324 cells, 0 failures, 9060 candidates, 324 real manifests. Abissal participated in 129/162 cells, abstained in 33/162 (real abstention, not just theoretical); Marés used its conditional model in 129/162 and marginal backoff in 33/162 — always reported as two separate lines, never a single pooled "Marés X%". Artifacts: `benchmarks/reports/arena_season_2_star_wars.md`, `benchmarks/rankings/arena_season_2_star_wars.json`.

**Temporada 3** ran the same 54 targets × 3 seeds × `treefolks_v2` (5 Florestas), base commit `747f12dd`. A first attempt wrote 162 real manifests and then failed entirely (`AttributeError`, a campaign-script post-processing bug — `c.race` instead of `c.candidate.race` — `cells_ok=0`); those 162 manifests were **preserved intentionally, never deleted**, and are explicitly excluded from the official results below (confirmed by a dedicated read-only audit: clean time-range separation, zero `run_id` overlap). The corrected re-run: **162/162 valid cells, 0 failures**, 16140 candidates, 162 real manifests. Yggdrasil participated in 159/162, abstained in 3/162 (insufficient history at the oldest 2005-era targets); the other 4 Florestas never abstain. Equal Budget N=5: Yggdrasil 1/795, Dodona 2/810, Brocéliande 3/810, Tír na nÓg 1/810, Fortuna 1/810 — every Floresta's Wilson interval overlaps Fortuna's. Artifacts: `benchmarks/reports/arena_season_3_forest_wars.md`, `benchmarks/rankings/arena_season_3_forest_wars.json`.

**Methodological note kept separate deliberately**: Temporada 2 is specifically about **stars** (Astérias model only the star hypothesis, numbers always neutral); Temporada 3 tests the **full key** (numbers + stars) — the two are not directly comparable number-for-number, only at the level of "was there any detectable signal at all". Neither campaign demonstrates or implies real predictive capability over the Euromillions draw — both compare a hypothesis against a neutral control (Acaso Puro/Fortuna), never against a future draw's actual result.

---

## Historical/Recovered Documentation

Two documents that are neither implemented code nor a roadmap idea — pure archaeology, reconstructing intent from the current code and from Git history (as far back as it goes, which is `756c63e6`, "V8 - Claude" — there is no V1-V7 history in this repository).

- **[`docs/AUDITORIA_FACCOES_E_ESTRATEGIAS.md`](docs/AUDITORIA_FACCOES_E_ESTRATEGIAS.md)** — every faction/order/organization's real algorithm, state (`ACTIVE`/`IMPLEMENTED_ORPHAN`/`PARTIAL`/`LORE_ONLY`/`SUPERSEDED`), RNG, Ariadne/history dependencies, persistence, VERIFIED-mode compatibility.
- **[`docs/BESTIARIO_ALGORITMICO_RECUPERADO.md`](docs/BESTIARIO_ALGORITMICO_RECUPERADO.md)** — a fact sheet per race/lineage/archetype (strategy, key construction, distinguishing trait, implicit experimental hypothesis), with every claim tagged `CONFIRMADO NO CÓDIGO ATUAL` / `CONFIRMADO NO HISTÓRICO GIT` / `DOCUMENTADO-LORE SEM IMPLEMENTAÇÃO` / `INFERÊNCIA`, never presented as fact when it isn't. **Recovered so far: V8 → today only** — pre-Git archaeology (V1/V2/V3, an evolutionary tree of strategies) is an explicitly scoped, not-yet-done second pass, noted in the document itself.

---

## Academia Arcana de Nemerion

*Schola Aeterna Artium Probabilitatis* — "O acaso não se domina. Estuda-se." A separate initiative from the Campaign Runner/Arena above: it reuses the same `GENERATORS` adapter mechanism as a technical plumbing choice, but asks a different narrative question — not "which system produces better candidates", but "which Doctrine does a persistent Student follow over time". **An Academia Piloto Oficial is not an Arena Season** — no Equal Budget, no Wilson intervals, no declared winner; it runs over Students with persistent identity (`library/academy/students/`, `library/academy/enrollments/`), not anonymous per-cell candidates.

Each Cátedra (classroom) caps at exactly 5 active Students (`CLASSROOM_ACTIVE_STUDENT_CAPACITY`, scoped per `(institution_id, classroom_id)` — never per doctrine version). Student identity has zero algorithmic power over the Doctrine in V1 — `run_tyche()`/`run_mnemosyne()` receive only `historico` and an `rng`, never the Student record itself.

| Cátedra | Generator key | Doctrine | Hypothesis |
|---|---|---|---|
| **Tyche — Fundamentos do Acaso** | `academia` (permanent — never renamed, already baked into 15 published manifests) | `tyche/v1` | Uniform control — no historical information influences selection |
| **Mnemosyne — Memória da Frequência** | `academia_mnemosyne` | `mnemosyne/v1` | `weight(v) = count_historico(v) + 1` (Laplace α=1) — more frequently observed numbers/stars get proportionally higher selection weight |

Naming convention (binding for all future Cátedras): `academia_<slug>` — one generator key = one identifiable experimental hypothesis, never a dynamic multi-classroom dispatcher.

**Two Piloto Oficiais completed** — same 5 historical targets (`002/2004`, `049/2012`, `020/2017`, `096/2021`, `067/2026`) × 3 seeds × 5 Students = 75 Candidates/AcademicEvents per Cátedra:

| Category | Tyche (`33c2e8db`) | Mnemosyne (`8708dadb`) |
|---|---|---|
| 0+0 / 0+1 / 1+0 / 1+1 | 29 / 16 / 12 / 13 | 32 / 14 / 17 / 8 |
| 2+0 / 2+1 / 3+1 / 1+2 / 0+2 | 4 / 1 / 0 / 0 / 0 | 1 / 0 / 1 / 1 / 1 |
| **≥1 hit** | **46/75** | **43/75** |

Purely descriptive — small sample, no significance calculated, no Doctrine declared superior.

Known debts: no algorithmic power for Student identity/name; no `active → withdrawn/completed` transition API (only `create()` sets a status); capacity enforcement is single-writer, not concurrency-safe; no `ClassroomRegistry` (each Doctrine module self-declares its own identity); Hi-Lo/Ecos classes remain blocked on `ordem_saida` availability (see Roadmap below). Personality, Knowledge, Books, Skills, CandidateTransformation, Rebels, Codex Bruxinorum, Codex Infinitum remain roadmap-only, unimplemented.

---

## File structure

```
Project-Ariadne/
│
├── main.py                     ← simulation entry point
├── register_official_draw.py   ← CLI: register new official draws (staged → validated → installed, with rollback)
├── evaluate_heroes.py           ← CLI: Hero Evaluation Engine
├── evaluate_legends.py          ← CLI: Legend Evaluation Engine
├── config.txt                  ← all parameters
├── requirements.txt            ← minimal, no ML libs — tzdata (Commit 25), see below
├── requirements-dashboard.txt  ← optional: openpyxl, used by dashboard/excel_export.py
│
├── core/                        ← framework engine
│   ├── strategy.py / registry.py / plugin_loader.py  ← FactionRegistry + plugin architecture
│   ├── i18n/                    ← translations.py — 6 languages × 25 translation keys
│   ├── data/                    ← loaders.py — reusable historical/jackpot/moon data access
│   └── services/                ← shared, pure transformation/validation services
│       ├── combinations.py, fitness.py         ← shared candidate-key helpers
│       ├── atomic_io.py                        ← atomic JSON writes (temp-then-replace)
│       ├── historical_dataset.py, historical_astronomy.py,
│       │   historical_statistics.py, historical_scroll.py,
│       │   historical_draw_generator.py        ← official-draw registration pipeline
│       ├── hero_evaluation.py, legend_evaluation.py  ← deterministic Hero/Legend classification
│       ├── run_manifest.py                     ← per-run provenance manifest
│       ├── dashboard_data.py                   ← Dashboard Dataset (see above)
│       ├── statistical_profiles.py             ← shared statistical primitives (frequency, delay, parity...)
│       ├── rolling_windows.py                  ← last-N-draws / last-N-weekday window selection
│       ├── artifact_schema.py, artifact_registry.py,
│       │   artifact_inspiration.py             ← Biblioteca dos Artefactos (see above)
│       ├── backtest_lab.py                     ← Backtest Experiment Lab (Commit 20)
│       ├── historical_simulation_source.py     ← temporal cutoff over the versioned dataset (Commit 22)
│       ├── historical_ariadne_source.py        ← temporal cutoff over library/scrolls/ (Commit 23)
│       ├── temporal_memory_boundary.py         ← temporal cutoff over persistent memory (Commit 24)
│       ├── backtest_orchestrator.py            ← Backtest Orchestrator V1, Clerics-only (Commit 25)
│       ├── backtest_campaign.py                ← Campaign Runner V1 (Commit 27) + V2 multi-system
│       ├── backtest_generators.py              ← Campaign Runner V2 adapters (6 systems)
│       └── backtest_arena.py                   ← Arena — Official Key, Equal Budget, abstention accounting
├── council/                     ← Grand Council filter + vote
├── factions/                    ← executable faction plugins (package format) — 21 factions, one per race
│   ├── clerics/                 ← Clérigos (V11) — genetic algorithm engine, 8-archetype dispatcher
│   ├── kors/                    ← Kors de Elarion (V7.2)
│   ├── chaos_cartographers/     ← Cartographers of Chaos (V8)
│   └── axiomantes/              ← Axiomantes de Nemerion (V8.1)
│       ├── labyrinth.py         ← combinadic rank/unrank + Feistel
│       ├── profile.py           ← Echo Profile + scoring
│       ├── ritual.py            ← Ritual of Thirty Echoes
│       └── council.py           ← Council integration
├── races/                       ← lore only (README/lore.md/characters.json/artifacts.json/lineages|orders.json) — no executable code, 21 races
│   ├── clerics/                 ← Clérigos (V11) — the 10 ancestral lineages (incl. Minotauro Commit 19, Zombie Commit 26), 6 houses
│   └── mystics/                 ← Mystics (V10) — lore, characters, artifacts; nature/ + prophecy/ lineages
├── orders/                      ← organisations and guilds
│   ├── black_squad/             ← Black Squad + grimoire + dark_library
│   ├── elven_order/             ← Elven Order + missions
│   ├── scribes/                 ← scribes + chronicles + atlas + museum
│   └── librarians/              ← scroll conversion utilities
├── library/                     ← Eternal Library and knowledge
│   ├── ariadne/                 ← Ariadne engine
│   ├── scrolls/                 ← per-draw views (2004–2026)
│   ├── books/                   ← reconstructable books
│   ├── indexes/                 ← pairs/triples/frequencies + normalized draw index
│   ├── heroes/                  ← HeroRegistry — entries/ + derived LIVRO_DOS_HEROIS.json
│   ├── legends/                 ← LegendRegistry — entries/ + derived LIVRO_DAS_LENDAS.json
│   ├── artifacts/               ← Biblioteca dos Artefactos — entries/ + derived LIVRO_DOS_ARTEFACTOS.json
│   ├── catalogue/, cache/, black_kors/
├── artifacts/                   ← OLDER, distinct system: mechanical relics/amulets tied to simulation state (V4)
│   ├── ark.py / living.py       ← relics + living artifacts
│   ├── relics/                  ← persistent relics (ART-*.json)
│   └── amulets/                 ← amulets, monastery, generated books
├── world/                       ← world engine + world presets
│   ├── engine/                  ← builder, extraction, celestial energy, dark conviction, council war, Malphas virus
│   └── presets/                 ← world profiles (config variants) + central loader
├── datasets/                    ← historical and generated data
│   ├── historical/euromillions/<year>/  ← immutable annual datasets
│   ├── imports/                 ← raw import files (xlsx)
│   └── generated/                ← simulations/ · campaigns/ · world_state/ · temporary/
├── experiments/                 ← simulation outputs and research
│   ├── axiomancers/runs/        ← per-run Axiomantes ritual reports (JSON)
│   ├── reports/                 ← report writer + generated/ .txt reports
│   ├── figures/                 ← plots/visualisations (empty — structure only)
│   ├── notebooks/               ← exploratory analysis notebooks (empty — structure only)
│   └── benchmarks/              ← ad-hoc benchmark research sessions (empty — structure only)
├── dashboard/                   ← Excel export over an already-built DashboardDataset
│   ├── __init__.py
│   └── excel_export.py          ← build_workbook() (pure) + export_to_excel() (only I/O)
├── benchmarks/                  ← durable strategy-vs-baseline comparison results (empty — structure only)
│   ├── random/                  ← random-baseline runs
│   ├── reports/                 ← human-readable comparison reports
│   └── rankings/                ← machine-readable leaderboards
├── docs/                        ← documentation
│   ├── AUDITORIA_FACCOES_E_ESTRATEGIAS.md    ← historical/recovered — every faction's real algorithm/state
│   ├── BESTIARIO_ALGORITMICO_RECUPERADO.md   ← historical/recovered — per-race strategy fact sheets (V8→today)
│   └── lore/                    ← canon bible (canon_index, timeline, relationships, geography,
│       │                          factions, artifacts, characters, locations, glossary, architecture)
│       └── legends/             ← legendary characters registry (runtime, not canon)
└── tests/                       ← unittest suite for the framework (registry, plugin_loader, council, models, backtesting)
```

---

## Quick start

**Requirements:** Python 3.10+. Almost entirely stdlib — the one
exception is `tzdata` (see [Timezone data](#timezone-data) below).

```bash
git clone https://github.com/your-username/eternal-library.git
cd eternal-library
pip install -r requirements.txt

# Run the simulation
python main.py

# Consult Ariadne directly (CLI subcommands are Portuguese; see below)
python query_ariadne.py duplas --limite 10
python query_ariadne.py numero 17
python query_ariadne.py lua "Lua cheia"
python query_ariadne.py pergaminho 55

# Multi-era campaign
python campaign_v6.py

# Validate config
python validate_config.py

# Run the test suite
python -m unittest discover -s tests
```

---

## Timezone data

Python's standard library handles timezones via `zoneinfo`, but
`zoneinfo` itself needs an IANA timezone database to resolve named
zones (e.g. `"Europe/Paris"`) from — many systems don't ship one built
in, notably Windows. `tzdata` is the official, CPython-maintained
package that supplies it portably; it's the one non-stdlib dependency
in `requirements.txt`. Required for portable IANA timezone resolution
used by the temporal backtest boundary
(`core/services/backtest_orchestrator.py`, Commit 25), which converts
a backtest boundary's UTC instant into `[MUNDO].timezone`'s local time
— that local time then feeds the historical context construction,
including the moon phase. An unrecognized or missing timezone raises
`ValueError` in both VERIFIED and EXPLORATORY mode, never a silent
fallback.

---

## Configuration

Everything is in `config.txt`. Key sections:

```ini
[SIMULACAO]
semente = 2026          # fixed seed for reproducibility (or use modo_semente = aleatorio)
geracoes = 14
conselho_final = 10

[MUNDO]
lang = en               # pt · es · fr · nl · de · en · gb

[AXIOMANTES]
ativos = true
peso_conselho = 0.75
periodo_anos = 1        # comparison window (years)
limiar_cobertura = 0.50 # portal opens if coverage >= this
n_candidatos = 50000    # inédita candidates evaluated per run
guardar_experiencia = true
```

---

## Language support

The simulation output supports 6 languages covering all 9 Euromillions participating countries:

| Code | Language | Countries |
|------|---------|----------|
| `pt` | Portuguese | Portugal 🇵🇹 |
| `es` | Spanish | Spain 🇪🇸 |
| `fr` | French | France 🇫🇷 · Belgium 🇧🇪 · Luxembourg 🇱🇺 · Switzerland 🇨🇭 |
| `nl` | Dutch | Belgium 🇧🇪 |
| `de` | German | Austria 🇦🇹 · Switzerland 🇨🇭 · Luxembourg 🇱🇺 |
| `en` / `gb` | English | UK 🇬🇧 · Ireland 🇮🇪 |

Set `lang = en` in `config.txt`. Invalid codes fall back silently to `pt`.

**What changes with `lang`:** faction verdicts, the mandatory disclaimer, Portal status, all `main.py` print labels.  
**What does not change:** fictional proper nouns (Kors de Elarion, Axiomantes de Nemerion, Ariadne, etc.) — these are narrative names, not translated.

---

## Dataset

- **1,974 real Euromillions draws** (2004–2026) stored as individual JSON scrolls (`library/scrolls/`)
- **67 full 2026 scrolls** with astronomy metadata, statistics, and SHA-256 signature
- **Immutable annual datasets** 2004–2026 in `datasets/historical/euromillions/<year>/`
- **Raw imports** (e.g. spreadsheet exports) in `datasets/imports/`
- **Frequency indices** for pairs, triples and the normalized number index in `library/indexes/`
- **Generated/runtime data** (simulation ledgers, world-state snapshots, campaign runs, disposable caches) in `datasets/generated/` — never committed as source data, always reproducible by re-running the simulator

All data is stored locally. No API calls, no external services.

---

## Plugin lifecycle

A faction is a directory under `factions/<name>/`. `main.py` never
references any specific faction by name — it only talks to
`core.registry.FactionRegistry`:

```python
registry = FactionRegistry().discover("factions")
for faction in registry.all():
    proposals = faction.propose(context)   # -> list[Proposal]
```

**Adding a new faction never requires changing `main.py`.**

1. Create `factions/<name>/manifest.json` — `id`, `name`, `home`,
   `config_section`, `weight_key`, `default_weight`, `votes` (`false`
   marks it analytical/non-voting, like `chaos_cartographers`).
2. Implement the strategy, either:
   - `council.py` with `FACTION_META = {...}` + `def council(ariadne, seed, cfg, ctx)`
     returning a list of dicts, a dwarves-style clan list (`carteira`),
     or a werewolves-style `{'ativo', 'simulacoes', 'finalistas'}` dict
     — `core.plugin_loader.CompatFaction` normalizes all three shapes
     into `Proposal` objects; **or**
   - `strategy.py` with a class inheriting `core.strategy.Faction`,
     implementing `propose(self, context) -> list[Proposal]` directly,
     referenced by `"class"` in `manifest.json`.
3. Query data exclusively through `ariadne` (the `Ariadne` instance in
   `context`) — never read `library/` or `datasets/` files directly.

`FactionRegistry.discover("factions")` walks `factions/` alphabetically
at startup, skips `_`-prefixed directories, and silently skips any
directory without a working `council.py`/`strategy.py` (analytical
factions like `chaos_cartographers` are skipped this way, not treated
as errors). A faction returning `[]` — a **valid abstention** (portal
closed, inactive this run, etc.) — is not a failure; `main.py` only
logs a warning when `propose()` raises an actual exception.

Look at `factions/kors/council.py` for the simplest `council.py`
example, or `factions/axiomantes/council.py` for a full implementation
with config, logging and Council integration.

---

## Testing

`tests/` uses Python's stdlib `unittest` — no external test framework.
Run the suite with:

```bash
python -m unittest discover -s tests
```

**Philosophy:** tests target the *framework*, not the narrative
content — `FactionRegistry`, `plugin_loader`, `council` (filtering,
voting, corruption), the shared `Proposal`/`Faction` models, and the
backtesting/scoring logic. Each test file covers exactly one module's
responsibility so that a future refactor of the plugin architecture
fails loudly and locally instead of silently breaking a faction three
layers away. Faction-specific narrative logic (the 21 `factions/*/`
strategies) is not under test — it doesn't affect framework stability
and its "correctness" is largely narrative, not mechanical.

**Current suite:** 1125 tests across 46 modules, zero skipped, also
covering the historical dataset pipeline, Hero/Legend evaluation, the
Dashboard Dataset layer, the Dashboard Excel Export, the Artifact
Library, the Candidate Analysis Layer (provenance, evaluation,
performance, Minotauros, Zombie), the Temporal Safety / Backtest Lab
(Commits 20-24), the Backtest Orchestrator / Campaign Runner V1+V2 /
Arena layer (Commits 25-27 and after), Astérias de Thalássia +
`attempted_races`, the Star Contribution Trial, and Treefolks V2 — As
Grandes Florestas (including Yggdrasil's optional-PyTorch path,
validated with `torch==2.13.0` actually installed) — each with
dedicated tests against real, on-disk data
(`datasets/historical/euromillions/`, `library/artifacts/entries/`,
`library/scrolls/`,
`datasets/generated/simulations/arquivo_destino.json`), not just
synthetic fixtures.

---

## Benchmarks

`benchmarks/` is scaffolding for comparing faction/strategy
performance against a random baseline (`benchmarks/random/`) with
comparison reports (`benchmarks/reports/`) and machine-readable
leaderboards (`benchmarks/rankings/`). No runner exists yet — the
structure exists so that future benchmark tooling has a stable home
from day one, instead of being bolted onto `experiments/` after the
fact. `experiments/benchmarks/` is a related but distinct location for
ad-hoc benchmark research sessions, as opposed to the durable/canonical
results that belong in the top-level `benchmarks/`.

---

## Roadmap / Future Vision

Everything below is a documented idea, not implemented code — nothing
here affects the simulation, a key, a vote, or a probability today. See
[Current Status (V13)](#current-status-v13) above for what actually
exists.

- **Dashboard wiring** — no script yet assembles a real `DashboardDataset`
  from live Heroes/Legends/datasets/races and calls `export_to_excel()`;
  today only tests and manual validation do it.
- **`Generations`/`Frequencies` sheets** — `dashboard/excel_export.py`
  still only covers the original 8 sheets; `GenerationRow`/`FrequenciesRow`
  have real builders now but no sheet of their own yet.
- **New factions** — Juízes do Conselho, Geómetras do Véu, Estatísticos
  Imperiais (named in project planning, not yet implemented).
- **`PairService`/`TripleService`/`EntropyService`/`TrendService`** —
  the capabilities originally sketched under the indicative names
  `StatisticsService`/`DelayService` began being implemented in
  Commits 12-13 as `core/services/statistical_profiles.py`/
  `rolling_windows.py`; those indicative names were never created as
  concrete services/classes themselves. The other four indicative names
  remain fully unimplemented (no fresh pair/triple data source, no
  entropy or trend definition yet), and none of the six replace the
  duplicated per-faction frequency/overdue/gap logic in
  `core/evolution/statistics.py`, `factions/chaos_cartographers/*.py`
  and `factions/axiomantes/profile.py` — that migration is still not started.
- **`ctx['rng']` retrofit** — deciding whether every faction should use
  the shared, seedable `ctx['rng']` (today only the Pantheon, Skeletons
  and Chronomancers do; Clerics deliberately kept the global `random`
  module for reproducibility reasons).
- **Benchmarks runner** — `benchmarks/` is still scaffolding, but its
  own README's original promise ("baseline runs: pure random key
  selection... the statistical floor every real faction/strategy
  should be compared against") is now partially fulfilled by the
  Arena's Acaso Puro system — what's left is wiring `benchmarks/` as a
  durable destination for Arena comparison output, not building a
  random baseline from zero.
- **Vampires, Gargoyles, Kor Vermelho, Werewolves in the Campaign
  Runner** — explicitly audited and **not** registered, for two
  different, documented reasons, not because nobody got to it yet:
  Vampires/Gargoyles/Kor Vermelho depend on Ariadne methods
  (`pairs()`/`triples()`/`least_frequent_numbers()`) that Commit 23
  already proved structurally impossible to certify temporally without
  redesigning their data source; Werewolves have a real provenance gap
  (`origem="lobisomem"` is absent from `candidate_provenance.py`'s
  closed taxonomy — latent, never yet triggered in the real archive).
  See `docs/AUDITORIA_FACCOES_E_ESTRATEGIAS.md` for the full matrix.
- **Campeão do Tesouro** (financial ranking, Arena layer) — the
  contract exists (`core/services/backtest_arena.py`'s module
  docstring and design notes) but is not implemented: no
  prize-value-per-category table exists anywhere in the project, and
  only 15 of the 67 real 2026 draws have financial data at all.
- **Pre-Git archaeology (V1/V2/V3)** — `docs/BESTIARIO_ALGORITMICO_RECUPERADO.md`
  only recovers V8 → today (the oldest commit reachable in this
  repository's Git history). A second pass, based directly on
  recovered pre-Git source files, plus an evolutionary tree of
  strategies, is scoped but not started.
- **Fangorn / Ensemble** (Treefolks V2) — the combination-of-Florestas
  contract is documented, zero implementation, zero module, zero
  placeholder. Blocked until real results exist for all 5 Florestas —
  Temporada 3 running does **not** auto-unlock it.
- **Component Contribution Trial** (Treefolks V2) — a designed
  generalization of the Star Contribution Trial to each Floresta's
  number/star scores (`component ∈ {"numbers","stars","full"}` vs. a
  neutral Fortuna baseline, independent per-component RNG streams,
  same shared key constructor) — designed in detail, not implemented.
- **Academia — Hi-Lo classes (predictive vs. repetition rival)** —
  registered concept, no closed design, no implementation. A
  predictive class studying sequences in the **real draw order** (not
  the already-sorted key format used everywhere in this project today)
  to bet whether the next number comes in higher or lower than the
  previous one; a rival class betting on repetition of the immediately
  preceding Hi/Lo pattern. Analogous application to stars. **Explicit
  prerequisite, still unconfirmed**: whether the historical dataset
  actually records real draw order at all — an already-sorted key
  cannot reconstruct it; without that confirmation the Hi-Lo class
  cannot be built honestly. (Incidental note: the 2026 dataset shows
  signs of an `ordem_saida`/`ordem_saida_disponivel` field on some
  records, observed during unrelated work — this does not confirm
  full-history coverage and was never formally verified.)
- **Academia — Rebeldes** — a future Academia class that tries to
  steal/copy a key produced by another class and then sabotages it via
  a controlled alteration; if the theft attempt fails, it falls back
  to its own manuscripts, built only from books/knowledge it has
  actually stolen or acquired before. Only the concept is registered —
  the exact theft/sabotage/fallback mechanics are unspecified.
- **Codex Bruxinorum — O Primeiro Grimório** — a future primordial book
  conceptually recovered/inspired from the old Java "EuroBruxinhos"
  project, preserving that project's historical ideas (weighted
  generation/distribution, historical frequencies, the old
  "Meditação") inside the Ariadne universe. Intended future direction:
  books transmit knowledge and can eventually unlock capabilities
  auditably, never simply altering a key or granting arbitrary
  modifiers. No JSON/model exists — roadmap only.
- **Livro de Todas as Chaves / Codex Infinitum** — a future canonical
  index of all 139,838,160 valid Euromillions keys: exactly one
  permanent page per key, exactly one key per page, reversible
  index→key and key→index operations without materializing 139.8M
  rows, independent of race/strategy/seed/campaign/RNG. Conceptual
  rule: "a page never changes key, a key never changes page." **Not to
  be confused with the Axiomantes**: the Codex would give canonical,
  absolute coordinates of the combinatorial space; the Axiomantes'
  Labyrinth (already implemented, `factions/axiomantes/labyrinth.py`)
  uses a seed-dependent Feistel permutation over that same space —
  related but distinct concepts. No implementation exists.
- **Laboratório de Malphas — Super-Esqueletos / Cyber-Anões** — a
  future expansion of the already-existing Malphas (final-key
  corruption) into a persistent "Obsidian Laboratory" for fictional/
  algorithmic experiments and synthetic beings. **Super-Esqueletos**:
  future synthetic individuals combining properties observed across
  several Esqueletos, keeping provenance of the lineages/experiments
  used — never simply "Esqueletos +X%". **Cyber-Anões**: a future
  laboratory variant of the Anões (dwarf DNA + cybernetic components,
  in-lore). A sketched (unimplemented) V1 hypothesis: a 10-draw
  window, pool A = numbers seen 1-2 times, pool B = numbers seen 0
  times, candidate = 3 from A + 2 from B, stars = 2 new or 1 new + 1
  eligible repeat — an experimental hypothesis, never a claim that
  absent numbers are "due" or that this has any advantage. Nothing
  implemented; today's real Malphas (key corruption) is not this
  laboratory expansion.
- **Cíclopes — "Olho para a Coisa"** — a future focal race/strategy.
  Each Ciclope would center its analysis on a single number (its
  "eye") and build candidates from that number's historical
  relationships/co-occurrences with other numbers and stars — future
  hypothesis: does conditioning generation on one focal number behave
  differently from global-frequency-based strategies? Whether the
  "eye" could be heritable/mutable across generations was discussed as
  a future extension, not a defined implementation. No code.
- **Personalidade dos indivíduos** — a future cross-cutting system
  where each individual could carry its own personality attributes on
  a 1-10 scale (5 neutral), independent of race/strategy — e.g.
  intelligence, greed, curiosity, skill, communication/sociability,
  courage, discipline, creativity, prudence. Could eventually influence
  behavior, learning, book/artifact seeking and use, crafting, and
  social interaction — **never silently altering the base strategy
  inside the Arena**. Any key modification from personality/an
  artifact would have to preserve provenance (original key, final key,
  cause of the transformation). **Explicit, binding restriction
  already in force**: Personalidade must always stay separate from the
  experimental Arena (`backtest_arena.py`) — never contaminating
  algorithmic comparisons between systems/strategies, the same way the
  Artifact Library (V13) is already structurally inert today
  (`altera_algoritmo`/`altera_resultados`/`altera_probabilidades`
  always `false`). Not for implementation now.

---

## Versão em português

Se preferires ler em português → [LEIA-ME.md](LEIA-ME.md)

---

## Disclaimer

> The position of a key in a pseudorandom permutation does not alter its real probability of being drawn. A coverage ≥ 50% is always expected when traversing ≥ 50% of the universe — this is entirely consistent with pure chance. No strategy described in this project increases the probability of winning the lottery. All keys have an equal probability of 1 in 139,838,160.

---

## Changelog

| Version | Highlight |
|---------|-----------|
| V1 | First council of agents |
| V2 | Distinct strategies per agent |
| V3 | Campaigns, generations, legendary characters |
| V4 | Council + Malphas corruption; amulets; relics; hidden library |
| V5 | Shadow war — Black Squad vs Elven Order; grimoire learns between runs |
| V6 | Multi-era campaigns; Scribes, chronicles, Atlas; configurable worlds |
| V7 | Eternal Library; Ariadne as sole data broker; Vampires; Gargoyles |
| V7.2 | Kors de Elarion — four named observers consulting Ariadne exclusively |
| V8 | Cartographers of Chaos — analytical books shared across factions |
| V8.1 | Axiomantes de Nemerion — Feistel permutation over 139M combinations; Echo Profile scoring; i18n |
| V9 | Plugin architecture — `FactionRegistry`, `CompatFaction`, per-faction `manifest.json`; adding a faction never touches `main.py` |
| V10 | Mystics — 8 new orders (lore + plugin scaffolding: Druids, Moon Priests, Star Gazers, Shamans, Witches, Seers, Oracles, Bone Readers), always abstain by design |
| V10.5 | Architecture complete — `races/` fully lore-only, first real shared services (`combinations.py`, `fitness.py`) |
| V11 | Clerics migrated into the plugin architecture (`races/legacy.py` retired) — 21 voting factions total |
| V12.3 | Dashboard Dataset — Heroes, Legends, Base de Chaves, Characters, Houses, Executive Summary, Economy, Prize Categories, Generations, Frequencies (incl. real `atraso_atual`); Excel Export (`dashboard/excel_export.py`); Shared Statistical Primitives + Rolling Window Selection (`statistical_profiles.py`, `rolling_windows.py`) |
| V13 | Biblioteca dos Artefactos — narrative artifact schema, registry and deterministic inspiration generator; official-draw registration CLI |
| Commits 15-19 | Candidate Analysis Layer — Statistical Window Profiles, Candidate Provenance/Evaluation/Performance (strictly retrospective, temporal boundary enforced); Minotauros — Clerics' key-persistence lineage |
| Commits 20-24 | Temporal Safety / Backtest Lab — candidate existence (Commit 20), historical dataset + Ariadne temporal modes (Commits 22-23), persistent memory / Necromancy (Commit 24); Commit 21 audited the gaps these close. Not yet wired into `main.py`. |
| Commit 25 | Backtest Orchestrator V1 (`6504425`) — first real end-to-end retrospective run for Clerics; VERIFIED/EXPLORATORY modes; `run_manifest.py` collision fix; `tzdata` added as the project's one non-stdlib dependency |
| Commit 26 | Zombie (`71be259`) — territorial Monte Carlo lineage for Clerics; 10 archetypal lineages total |
| Commit 27 | Campaign Runner V1 (`6308fc1`) — `target × seed × generations` grid for Clerics, dynamic race discovery, purely descriptive race performance |
| Campaign Runner V2 | Multi-system Campaign Runner (`cb5087e`) — Skeletons, Melforks, Axiomantes, Pantheon and Acaso Puro join Clerics via external adapters, zero faction/orchestrator changes; Arena layer (`88bfb28`) — Official Key, Equal Budget, abstention/participation accounting for normalized cross-system comparison |
| — | Historical archaeology — `docs/AUDITORIA_FACCOES_E_ESTRATEGIAS.md` and `docs/BESTIARIO_ALGORITMICO_RECUPERADO.md`, V8 → today, every claim tagged by evidence level |
| `cf22d7e7` | Astérias de Thalássia (Astéria Abissal + Astéria das Marés) + `attempted_races` generic contract extension — seventh `GENERATORS` system |
| `d9b8c104` | Star Contribution Trial (`core/services/star_contribution_trial.py`) — paired numbers-fixed/stars-swapped experiment |
| `e4624e65` | Arena Oficial — Temporada 2 / Guerra das Estrelas — real campaign, 324/324 cells, 9060 candidates; hypothesis tested, not confirmed |
| `f32b63b3` | Treefolks V2 — As Grandes Florestas — 5 real Florestas (LSTM/Bayes/Markov/Monte Carlo/Fortuna control), eighth `GENERATORS` system, Fangorn deliberately unbuilt |
| `747f12dd` | Treefolks V2 — Yggdrasil validated with PyTorch actually installed (`torch==2.13.0`); 1125/1125 tests, zero skipped |
| `85a65fec` | Arena Oficial — Temporada 3 / Guerra das Florestas — real campaign, 162/162 valid cells, 16140 candidates; no Floresta showed a clear advantage over the Fortuna control |

---

## License

MIT © 2026 Tiago Silva
