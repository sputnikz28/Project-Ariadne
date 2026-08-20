# The Eternal Library

> A multi-agent statistical simulation framework where fantasy-inspired factions analyse historical lottery data using competing statistical philosophies — with full backtesting under identical conditions.

**No magic. No predictions. Just agents, data, and reproducible experiments.**

---

## What is this?

The Eternal Library is an experimental Python framework built around one central idea: **what happens when many independent agents, each following a different statistical strategy, compete on the same historical dataset under identical, reproducible conditions?**

The agents are factions from a fictional universe. The dataset is 1,968 real Euromillions draws (2004–2026). The strategies range from genetic algorithms and Markov chains to combinatorial permutations and frequency analysis.

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

## Current Status (V13)

A quick map of what actually exists in this repository today, kept separate from ideas — see [Roadmap / Future Vision](#roadmap--future-vision) for what is *not* built yet.

**✅ Core simulation engine** — plugin architecture (`core/registry.py`, `core/plugin_loader.py`, `core/strategy.py`), 21 auto-discovered voting factions, Ariadne as sole data broker, Council (filtering, weighted voting, Malphas corruption), 21 lore-only races, i18n (6 languages).

**✅ Historical dataset pipeline** — 1,968 real Euromillions draws (2004–2026), immutable annual datasets, plus `core/services/historical_dataset.py`, `historical_astronomy.py`, `historical_statistics.py`, `historical_scroll.py` and `historical_draw_generator.py` (used by `register_official_draw.py`, a full transactional CLI — staged → validated → installed, with rollback — for registering new official draws).

**✅ Heroes & Legends** — `library/heroes/` and `library/legends/` registries (`entries/*.json` as source of truth, derived `LIVRO_DOS_HEROIS.json`/`LIVRO_DAS_LENDAS.json` indices), plus `core/services/hero_evaluation.py`/`legend_evaluation.py` and their CLIs (`evaluate_heroes.py`, `evaluate_legends.py`).

**✅ Dashboard Dataset** — `core/services/dashboard_data.py`, a pure data-assembly layer: Heroes, Legends, Base de Chaves (draws), Characters, Houses, Executive Summary, Economy, Prize Categories, Generations and Frequencies are all implemented and tested against real data (see [Dashboard Dataset](#dashboard-dataset) below).

**✅ Dashboard Excel Export** — `dashboard/excel_export.py` turns an already-built `DashboardDataset` into a `.xlsx` workbook (Executive Summary, Heroes, Legends, Characters, Houses, Key Base, Economy, Prize Categories). Tested, including against the project's real data. No CLI or script wires this to live data yet — see [Dashboard Dataset](#dashboard-dataset) below.

**✅ Shared Statistical Primitives & Rolling Windows** — `core/services/statistical_profiles.py` (frequency, delay, parity, low/high, decade buckets, key gaps, repeated values) and `core/services/rolling_windows.py` (last-N-draws / last-N-Tuesdays-or-Fridays selection). Pure infrastructure — **not a prediction strategy, does not generate keys**, just reshaping/counting/selecting over data the caller already loaded.

**✅ Biblioteca dos Artefactos (Artifact Library)** — `core/services/artifact_schema.py`, `artifact_registry.py` and `artifact_inspiration.py`; 15 founding narrative artifacts, every one verified to have zero effect on algorithms, results or probabilities (see [The Artifact Library](#the-artifact-library-biblioteca-dos-artefactos) below).

**✅ Testing** — 614 tests across 25 modules (`python -m unittest discover -s tests`).

---

## Architecture

```
Ariadne (data broker)
    │
    ├── Eternal Library (persistent knowledge)
    │       ├── Scrolls        — one JSON per real draw (1,968 total)
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
| **Clerics** | Genetic algorithm — 72 individuals evolve over 14 generations |
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

---

## The Eternal Library (persistent knowledge)

```
library/
├── ariadne/            ← Ariadne engine (engine.py)
├── sources/            ← immutable annual datasets 2004–2026
├── scrolls/
│   ├── 2004/ … 2025/   ← compact format (1,929 scrolls)
│   └── 2026/           ← full format with astronomy (61 scrolls)
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

**Economy and Prize Categories are real, not synthetic.** The official 2026 dataset only has complete financial/prize-category data for 15 of its 61 draws — confirmed via the dataset's own `qualidade_dados` flags, never inferred from whether a value happens to be non-null. Every sum, mean, minimum and maximum in `EconomySummary`/`PrizeCategorySummary` is computed only over the draws that actually have that field; a field with zero real observations resolves to `None`, never an invented `0` or an estimate. `PrizeCategoryRow` always emits exactly 13 rows per draw — the fixed, official Euromillions prize-tier table, a game rule rather than a per-draw fact — with only the observed winner counts ever `None`.

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

## File structure

```
Project-Ariadne/
│
├── main.py                     ← simulation entry point
├── register_official_draw.py   ← CLI: register new official draws (staged → validated → installed, with rollback)
├── evaluate_heroes.py           ← CLI: Hero Evaluation Engine
├── evaluate_legends.py          ← CLI: Legend Evaluation Engine
├── config.txt                  ← all parameters
├── requirements.txt            ← stdlib only (no external ML libs)
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
│       └── artifact_schema.py, artifact_registry.py,
│           artifact_inspiration.py             ← Biblioteca dos Artefactos (see above)
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
│   ├── clerics/                 ← Clérigos (V11) — the 8 ancestral lineages, 6 houses
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
│   └── lore/                    ← canon bible (canon_index, timeline, relationships, geography,
│       │                          factions, artifacts, characters, locations, glossary, architecture)
│       └── legends/             ← legendary characters registry (runtime, not canon)
└── tests/                       ← unittest suite for the framework (registry, plugin_loader, council, models, backtesting)
```

---

## Quick start

**Requirements:** Python 3.10+ — stdlib only, no pip installs needed.

```bash
git clone https://github.com/your-username/eternal-library.git
cd eternal-library

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

- **1,968 real Euromillions draws** (2004–2026) stored as individual JSON scrolls (`library/scrolls/`)
- **61 full 2026 scrolls** with astronomy metadata, statistics, and SHA-256 signature
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

`tests/` uses Python's stdlib `unittest` — no external test framework,
consistent with the project's stdlib-only philosophy. Run the suite
with:

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

**Current suite:** 614 tests across 25 modules, also covering the
historical dataset pipeline, Hero/Legend evaluation, the Dashboard
Dataset layer, the Dashboard Excel Export and the Artifact Library —
each with dedicated tests against real, on-disk data
(`datasets/historical/euromillions/`, `library/artifacts/entries/`),
not just synthetic fixtures.

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
- **Benchmarks runner** — `benchmarks/` is scaffolding only; no runner
  exists yet.

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

---

## License

MIT © 2026 Tiago Silva
