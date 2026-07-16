# Relationships — Project Ariadne

Race/order relationship matrix. Grounded in `canon_index.md` and actual code mechanics wherever possible (flagged **[grounded]**); everything else is a light, deliberately conservative default (**[default]**) that new lore should feel free to deepen — but not contradict — rather than invent from scratch.

All 20 Council-voting races share one baseline fact, true regardless of any row below: **every proposal, from any race, is filtered/voted/backtested identically.** No race outranks another by lore alone (see `races/mystics/lore.md`, "Design constraint" — a principle that applies universe-wide, not just to Mystics).

| Race / Order | Allies | Rivals | Council stance | Malphas stance |
|---|---|---|---|---|
| `race:vampires` | Gárgulas (cordial) | Gárgulas (cordial) — same rivalry, both senses | Reliable, conservative voter (weight 0.90) | Opposed (default) |
| `race:gargoyles` | Treefolks (shared "observe and wait" temperament) **[default]** | Vampiros (cordial rivalry) **[grounded — both V7, both "counting" races]** | Conservative voter (weight 0.85), never led a revolt | Opposed (default) |
| `race:kors` | Axiomantes **[default — shared mathematical rigor, both Elarion-adjacent geography]**, Cartógrafos do Caos **[default — intellectual siblings, both statistical]** | Vampiros (mild professional rivalry — a Kor Vermelho quip about "arqueólogos que se recusam a emprestar as ferramentas") **[grounded]** | Full voter (weight 1.0), 4 independent observers (Branco/Vermelho/Verde/Preto) | Opposed (default) |
| `race:axiomantes` | Kors **[default]** | — (too new, too aloof for rivalries) | Only speaks when the Labyrinth portal opens (weight 0.75, conditional) | Opposed (default) |
| `race:chaos_cartographers` | Kors **[default]** | — | Analytical only — does not vote **[grounded]** | Opposed (default) |
| `race:dwarves` | Fadas, Melforks, Treefolks, Lobisomens (the "V3 — Mundo Vivo" cohort, arrived together) **[default]** | — | Full voter (weight 0.35), 3 clans each with own king | Opposed (default) |
| `race:faeries` | V3 cohort (see Dwarves) **[default]** | — | Full voter (weight 1.0) | Opposed (default) |
| `race:werewolves` | Clérigos **[grounded — `world/engine/council_war.py`: "Conselho purificado pelos Clérigos e por Fenrir"]**, V3 cohort | — | Full voter (weight 0.80), only active on full-moon weeks, active anti-corruption role in the Council War | Actively **opposed and effective** — Fenrir's pack is one of two named forces (with the Clérigos) that can purify Malphas's corruption **[grounded]** |
| `race:treefolks` | Gárgulas **[default]**, V3 cohort | — | Full voter (weight 0.90), investigates hypotheses rather than declaring predictions | Opposed (default) |
| `race:melforks` | Clérigos **[grounded — "Laboratório Genético" home + representatives literally named "Clérigo-N" in `factions/melforks/algorithm.py`, implying genetic descent from Clerics stock]** | — | Full voter (weight 1.0), genetic algorithm | Opposed (default) |
| `race:skeletons` | — (arrived alone in V6, no cohort) | — | Full voter (weight 0.80), sliding-window strategy | Opposed (default) |
| `race:chronomancers` | Panteão (Aion is thematically tied to the Ordem do Tempo) **[grounded — `orders/pantheon/aion.py` docstring]** | — | Full voter (weight 1.0, own `peso_cronomantes` key) | Opposed (default) |
| `race:mystics` (all 8) | Each other (two lineages, internal tension but no public hostility) **[grounded — `races/mystics/lore.md`]** | The mathematical races collectively — "cegas ao que não cabe numa fórmula" vs "imprevisíveis," mutual but non-hostile distrust **[grounded]** | Full Council seats since arrival, judged identically to math races **[grounded]** | Opposed (default) |
| `race:clerics` | Melforks, Lobisomens (see above) | — | Genetic-algorithm finalists feed the Council directly; the Ritual Celeste produces the "Escolha Humana Consagrada pelos Clérigos" | Actively opposed — the Clérigos are one of two purifying forces in the Council War **[grounded]** |
| `order:pantheon` | Chronomancers (Aion) | — | Outside Council voting by design — summoned directly by `main.py` | Opposed (default) |
| `order:black_squad` | — | `order:elven_order` (direct, ongoing war) **[grounded]** | Outside Council voting; steals relics, corrupts books, occasionally resurrects legends via necromancy | Not explicitly confederated with Malphas in any mechanic found — a **separate** corrupting force, not his agent. Do not conflate the two without new evidence. |
| `order:elven_order` | `order:scribes`, `order:librarians` (recovers/returns what Black Squad steals) **[grounded]** | `order:black_squad` **[grounded]** | Outside Council voting — "não vota directamente" | Neutral (not part of the Council War mechanic; fights a separate war) |
| `order:librarians` | `order:elven_order`, `order:scribes` | `order:black_squad` (their scrolls/books are the theft target) | Outside Council voting — infrastructure order | Opposed (default) |
| `order:scribes` | `order:librarians`, `order:elven_order` | `order:black_squad` | Outside Council voting — infrastructure order, guards the 9 forbidden books | Opposed (default) |

## Reading this table

- **[grounded]** entries are backed by a specific mechanic or quoted line of code/lore — safe to build on directly.
- **[default]** entries are conservative placeholders (mostly "shared arrival era" or "shared domain" logic) — a future lore pass may deepen these into real stories, but should not casually invent a rivalry or feud that isn't here without updating this file first.
- Malphas's virus mechanic (`world/engine/malphas_virus.py`) only infects Clerics population members (`Heroi.genoma`) — other races aren't individually "infectable," but any race's proposed key can still become the corruption target if the Council selects it. Treat "Malphas stance" as "this race's relationship to the Council War," not "can this race be personally infected."
