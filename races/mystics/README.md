# Mystics

The Mystics race brings back the original V1 spirit of Project
Ariadne, where intuition, rituals and ancient traditions coexist with
mathematical and statistical strategies. See [`lore.md`](lore.md) for
the full narrative history.

**Status: architecture, lore and plugin skeletons only. No prediction
algorithms are implemented yet.** Every faction below currently
registers correctly through `core.registry.FactionRegistry` and
abstains (`propose()` returns `[]`) on every run — exactly like any
other faction with nothing to contribute this round. This is
intentional, not a bug: these orders exist for now, they don't yet
predict.

## Two lineages

```
mystics/
├── nature/        ← Nature Mystics: harmony with nature, celestial
│   │                 and seasonal cycles
│   ├── druids/
│   ├── moon_priests/
│   └── star_gazers/
│
└── prophecy/       ← Prophecy Mystics: destiny read through symbols,
    │                  rituals and ancient tradition
    ├── shamans/
    ├── witches/
    ├── seers/
    ├── oracles/
    └── bone_readers/
```

| File | Contents |
|---|---|
| `lore.md` | Full narrative history — the two lineages, why they rarely agree with the mathematical races, why they hold a permanent Council seat, how Ariadne archives their rituals, how the Judges evaluate them |
| `orders.json` | The 8 mystical orders — philosophy, future analytical role, home, linked artifacts and faction plugin |
| `characters.json` | 16 named characters (2 per order) — name, title, lineage, biography, personality, preferred artifacts, future analytical speciality |
| `artifacts.json` | 16 artifacts (2 per order) |
| `nature/<order>/`, `prophecy/<order>/` | One folder per order with a short README pointing back to the shared JSON data and to its matching `factions/<order>/` plugin |

## Matching faction plugins

Each order also has an executable (placeholder) plugin under
`factions/`, auto-discovered by `FactionRegistry` — no changes to
`main.py` were needed to add them:

`factions/druids/`, `factions/moon_priests/`, `factions/star_gazers/`,
`factions/shamans/`, `factions/witches/`, `factions/seers/`,
`factions/oracles/`, `factions/bone_readers/`

## Design constraint

These factions must **not** outperform mathematical factions by
design — they represent alternative methodologies, not a shortcut.
Every proposal, mystical or mathematical, is filtered, voted and
backtested through exactly the same Council, the same Judges and the
same Backtesting engine. Lore never overrides statistics.
