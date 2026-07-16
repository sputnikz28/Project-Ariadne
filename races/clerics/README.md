# Clérigos

**Home:** Templo dos Clérigos · **Arrived:** Era I (V1 — Os Primeiros Oráculos), formalized as a genetic algorithm in Era II (V2 — A Evolução Genética) · **Council weight:** 1.0 per finalist, plus the separate Ritual Celeste contribution

The oldest Council methodology — not a single strategy but an
evolving population across 8 ancestral lineages (archetypes), bred
generation over generation. See [`lore.md`](lore.md) for the full
narrative history.

| File | Contents |
|---|---|
| `lore.md` | History, homeland, evolutionary philosophy, the 8 lineages, hierarchy (6 houses), Council role, and relationships with Ariadne/Melforks/Werewolves/Chronomancers/Skeletons |
| `lineages.json` | The 8 ancestral archetypes (Bruxa, Vidente, Chefe Tribal, Elfo, Goblin, Shaman, Cronomante, Esqueleto) + the 6 houses |
| `characters.json` | 8 archetypal entries — Clerics are procedurally regenerated each run from fixed name/title pools, not fixed individuals, so each entry describes a lineage's method rather than one person |
| `artifacts.json` | 3 artifacts — Living Amulets, the Ritual Celeste's Escolha Humana Consagrada, and the Path of the 1000 Souls |

**Faction plugin:** [`factions/clerics/`](../../factions/clerics) —
`algorithm.py` (the genetic algorithm engine), `archetypes.py` (the
8-lineage dispatcher), `council.py` (the `FactionRegistry`-discovered
entry point). See `factions/clerics/README.md` for why `main.py` still
calls `execute()` explicitly once, ahead of the registry loop.
