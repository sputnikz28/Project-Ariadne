# Esqueletos das Catacumbas Numéricas

**Home:** Catacumbas Numéricas · **Arrived:** Era VI — Crónicas das Eras · **Council weight:** 0.80

A sliding-window ritual — restrict the range before choosing, instead
of searching the full interval. See [`lore.md`](lore.md) for the full
narrative history.

| File | Contents |
|---|---|
| `lore.md` | History, homeland, philosophy, hierarchy, Council and inter-race relationships |
| `lineages.json` | The single sliding-window lineage |
| `characters.json` | 5 named relics/characters |
| `artifacts.json` | 2 artifacts |

**Faction plugin:** [`factions/skeletons/`](../../factions/skeletons)
— `algorithm.py` implements `generate()` and `create_representatives()`.
Also reused directly by the Clerics genetic algorithm
(`races/legacy.py`) for heroes born with the "Esqueleto" archetype.
