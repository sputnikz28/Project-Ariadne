# Lore Architecture — how the story connects to the code

For the *engineering* layered architecture (core → factions → orders → races → datasets → experiments), see the "Architecture" section of the top-level `CLAUDE.md`. This document is the lore-specific companion: which file backs which narrative fact.

## The authority chain

```
docs/lore/canon_index.md        ← the single source of truth (entity ids)
        ↓ referenced by
docs/lore/timeline.md            ← when things happened
docs/lore/relationships.md       ← how races relate to each other
docs/lore/geography.md           ← where things are
docs/lore/factions.md            ← philosophy per faction (lore voice)
docs/lore/artifacts.md           ← catalog of named items
docs/lore/characters.md          ← encyclopedia of named individuals
docs/lore/locations.md           ← detailed gazetteer
docs/lore/glossary.md            ← terminology
        ↓ grounds
races/<name>/{README.md, lore.md, characters.json, artifacts.json, lineages.json|orders.json}
```

**Rule:** a race's `lore.md` may *expand* on a canon fact with more narrative color, but must not *contradict* `canon_index.md`, `timeline.md`, or `relationships.md`. If a race needs a new named character or place that doesn't exist yet, add it to `canon_index.md` first, then write the race file that uses it.

## Per-race file pattern

Every race under `races/` (except the deferred `races/legacy.py`) follows the same five-file pattern:

| File | Purpose | Format |
|---|---|---|
| `README.md` | Short pointer: home, arrival era, Council weight, links to the other 4 files, link to the matching `factions/<name>/` plugin | English, terse |
| `lore.md` | History, homeland, philosophy, hierarchy, notable characters, artifacts, Council relationship, inter-race relationships | Portuguese prose, ends with the mandatory non-prediction disclaimer |
| `characters.json` | `{"raca": ..., "personagens": [{id, nome, titulo, biografia, personalidade, artefactos_preferidos, metodo}]}` | JSON |
| `artifacts.json` | `{"raca": ..., "artefactos": [{id, nome, nome_pt, descricao, ...}]}` | JSON |
| `lineages.json` or `orders.json` | Sub-groups within the race (bloodlines/clans → `lineages.json`; monastic/scholarly orders → `orders.json`) | JSON |

The Mystics race (`races/mystics/`) is the one deliberate exception: it's an umbrella over 8 sub-races, each nested under `races/mystics/{nature,prophecy}/<order>/` with just a `README.md` pointing back to the shared parent JSON files.

## Canon vs Runtime, mapped to files

| Canon (hand-authored, stable) | Runtime (simulation output, changes every run) |
|---|---|
| `docs/lore/*.md` | `datasets/generated/` |
| `races/**/*.{md,json}` | `experiments/` |
| `orders/**/*.py` **name pools** (fixed lists like `black_mages.py: NAMES`) | `library/cache/` |
| `factions/**/manifest.json` | The *entries* inside `docs/lore/legends/livro_personagens_lendarias.json` (the mechanic/schema is fine to document; the entries themselves are not canon facts) |
| `docs/lore/legends/ecos_ancestrais.json` (Íria da Névoa Azul — a deliberate seed, not procedural) | `artifacts/relics/*.json` (procedurally forged, except explicitly marked seed relics like `ART-EXEMPLO001.json`) |

## Adding a new faction (e.g. V11's Juízes do Conselho)

1. Add its entity ids to `canon_index.md` first (`race:`, `faction:`, home `place:`, any founding `character:`).
2. Add its arrival to `timeline.md` (new Era or a new entry under the current one).
3. Add a row to `relationships.md` and `factions.md`.
4. Only then write `factions/<name>/` (code) and `races/<name>/` (lore).
