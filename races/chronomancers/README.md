# Cronomantes da Ordem do Tempo

**Home:** Ordem do Tempo · **Arrived:** Era IV.2 · **Council weight:** 1.0 (own `peso_cronomantes` key)

Derive keys from the millisecond-precise timing of the extraction
event itself, not the historical record. See [`lore.md`](lore.md) for
the full narrative history.

| File | Contents |
|---|---|
| `lore.md` | History, homeland, philosophy, hierarchy, Council and inter-race relationships |
| `orders.json` | The single Ordem do Tempo, its 5 members and Pantheon link (Aion) |
| `characters.json` | 5 named characters |
| `artifacts.json` | 3 artifacts |

**Faction plugin:** [`factions/chronomancers/`](../../factions/chronomancers)
— `algorithm.py` implements the Council-voting temporal-key generator;
`representatives.py` implements `create_aion()` for the Pantheon
subsystem (`orders/pantheon/`), reused directly by the Clerics genetic
algorithm for heroes born with the "Cronomante" archetype.
