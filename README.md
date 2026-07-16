# The Eternal Library

> A multi-agent statistical simulation framework where fantasy-inspired factions analyse historical lottery data using competing statistical philosophies — with full backtesting under identical conditions.

**No magic. No predictions. Just agents, data, and reproducible experiments.**

---

## What is this?

The Eternal Library is an experimental Python framework built around one central idea: **what happens when many independent agents, each following a different statistical strategy, compete on the same historical dataset under identical, reproducible conditions?**

The agents are factions from a fictional universe. The dataset is 1,962 real Euromillions draws (2004–2026). The strategies range from genetic algorithms and Markov chains to combinatorial permutations and frequency analysis.

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

## Architecture

```
Ariadne (data broker)
    │
    ├── Eternal Library (persistent knowledge)
    │       ├── Scrolls        — one JSON per real draw (1,962 total)
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
│   ├── 2004/ … 2025/   ← compact format (1,907 scrolls)
│   └── 2026/           ← full format with astronomy (55 scrolls)
├── books/
│   └── cartographers/  ← 5 analytical books (Cartographers)
├── indices/            ← pairs, triples, frequencies, moon phases
├── cache/              ← Ariadne query cache
└── black_kors/
    └── papyri/         ← Nyxara's weekly papyri
```

---

## File structure

```
Project-Ariadne/
│
├── main.py                     ← simulation entry point
├── config.txt                  ← all parameters
├── requirements.txt            ← stdlib only (no external ML libs)
│
├── core/                        ← framework engine
│   ├── strategy.py / registry.py / plugin_loader.py  ← FactionRegistry + plugin architecture
│   ├── i18n/                    ← translations.py — 6 languages × 25 translation keys
│   ├── data/                    ← loaders.py — reusable historical/jackpot/moon data access
│   └── services/                ← shared, lore-agnostic helpers (combinations.py, fitness.py)
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
│   ├── catalogue/, cache/, black_kors/
├── artifacts/                   ← artefacts, relics and magical objects
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

# Consult Ariadne directly
python query_ariadne.py pairs --limite 10
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

- **1,962 real Euromillions draws** (2004–2026) stored as individual JSON scrolls (`library/scrolls/`)
- **55 full 2026 scrolls** with astronomy metadata, statistics, and SHA-256 signature
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
layers away. Faction-specific narrative logic (the 13 `factions/*/`
strategies) is not under test — it doesn't affect framework stability
and its "correctness" is largely narrative, not mechanical.

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

---

## License

MIT © 2026 Tiago Silva
