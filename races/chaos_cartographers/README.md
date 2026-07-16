# Cartógrafos do Caos

**Home:** Biblioteca Eterna · **Arrived:** Era VIII · **Council weight:** — (does not vote)

Five scholars, five analytical books published every session, zero
votes cast — by design. See [`lore.md`](lore.md) for the full
narrative history.

| File | Contents |
|---|---|
| `lore.md` | History, homeland, philosophy, hierarchy, Council and inter-race relationships |
| `orders.json` | The Colégio dos Cartógrafos and its 5 members |
| `characters.json` | 5 named characters |
| `artifacts.json` | 5 artifacts (their own published books) |

**Faction plugin:** [`factions/chaos_cartographers/`](../../factions/chaos_cartographers)
— `constellations.py`, `cycles.py`, `trends.py`, `randomness.py`,
`markov.py` implement each Cartographer's analysis; `council.py`
(`execute_cartographers`) runs all five. `manifest.json` sets
`"votes": false`.
