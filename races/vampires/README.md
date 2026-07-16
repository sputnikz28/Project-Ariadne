# Vampiros de Elarion

**Home:** Cripta Eterna · **Arrived:** V7 — Biblioteca Eterna · **Council weight:** 0.90

Masters of the triple — two rival-but-cordial lineages who read the
Library's triple index directly rather than through Ariadne. See
[`lore.md`](lore.md) for the full narrative history.

| File | Contents |
|---|---|
| `lore.md` | History, homeland, philosophy, hierarchy, Council and inter-race relationships |
| `lineages.json` | The two lineages — Sanguínea (Conde Vaelor) and Sombria (Lady Nyx) |
| `characters.json` | 3 named characters |
| `artifacts.json` | 4 artifacts |

**Faction plugin:** [`factions/vampires/`](../../factions/vampires) —
`algorithm.py` implements `create_vampires()` (used by the standalone
V7 report `simulate_v7.py`); `council.py` implements the Council-voting
path independently. See the V10.5 architecture migration notes in the
top-level `CLAUDE.md` for why these two paths currently differ.
