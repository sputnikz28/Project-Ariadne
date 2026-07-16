# Clérigos

**Home:** Templo dos Clérigos · **Arrived:** Era I–II (V1 Primeiros Oráculos, V2 Evolução Genética) · **Council weight:** 1.0 per finalist

The oldest Council methodology — a genetic algorithm breeding a
population across 8 historical archetypes across generations, with
the Path of the 1000 Souls, living amulets, and Malphas's virus all
interleaved into the same per-generation loop. See
[`races/clerics/lore.md`](../../races/clerics/lore.md) for the full
narrative history.

| File | Contents |
|---|---|
| `algorithm.py` | `Heroi` dataclass, `create()`, `avaliar()`, `execute()` — the genetic algorithm engine (moved from `core/evolution/genetic.py`) |
| `archetypes.py` | `generate()` — the 8-archetype dispatcher (moved from `races/legacy.py`); 2 of 8 archetypes (Esqueleto, Cronomante) delegate to `factions.skeletons.algorithm` / `factions.chronomancers.algorithm` |
| `council.py` | `FactionRegistry`-discovered entry point — reads the population already computed by `main.py` via `ctx['clerics_evo']`, does not re-run the algorithm |
| `strategy.py` | Dormant native `Faction` class skeleton, not yet wired (matches the same pattern already used by `factions/druids/strategy.py`) |
| `manifest.json` | Council identity — home, weight, description |

## Why `main.py` still calls `execute()` explicitly

Every other faction's Council contribution flows entirely through
`FactionRegistry` auto-discovery. Clerics is the one exception: its
population (`evo`) is also consumed by
`world/engine/celestial_energy.py`'s Ritual Celeste (souls from
`evo['cemiterio']`/`evo['ressuscitados']`), which is a separate,
pre-existing mechanic outside this plugin. Running the genetic
algorithm a second time inside `council()` would consume a different
slice of the random stream than the ritual saw, breaking
reproducibility for a given seed. So `main.py` runs
`factions.clerics.algorithm.execute(cfg, ctx)` once, stores the result
in `ctx['clerics_evo']`, and `council.py` only reads it back — no
hardcoded weight or candidate-building logic remains in `main.py`.
