# Melforks Genéticos

**Home:** Laboratório Genético · **Arrived:** Era III — O Mundo Vivo · **Council weight:** 1.0

Genetic descendants of the Clérigos, isolated in a faster-cycling lab
population — their representatives are literally named "Clérigo-N."
See [`lore.md`](lore.md) for the full narrative history.

| File | Contents |
|---|---|
| `lore.md` | History, homeland, philosophy, hierarchy, Council and inter-race relationships |
| `lineages.json` | The single lab lineage (no clans — only generations) |
| `characters.json` | 1 archetypal character (Clérigo, regenerated each session) |
| `artifacts.json` | 2 artifacts |

**Faction plugin:** [`factions/melforks/`](../../factions/melforks) —
`algorithm.py` implements `melforks()`, the Council-voting genetic
algorithm (shares `core/services/fitness.py` with the Werewolves).
