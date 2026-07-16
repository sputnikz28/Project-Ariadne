# Factions — Lore Summary

A lore-facing summary of all 20 Council-voting races/factions plus Clerics. For the *engineering* view (which `.py` file implements what), see the Architecture section of the top-level `CLAUDE.md`. This document is about philosophy and voice, not code.

| Race | One-line philosophy | Narrative framing of its algorithm | Council weight |
|---|---|---|---|
| Vampiros de Elarion | The past doesn't promise the future, but it doesn't lie about itself either. | Reads which triples of numbers have kept company most often. | 0.90 |
| Gárgulas do Torreão de Pedra | Stone doesn't forget. | Reads which pairs of numbers keep returning together. | 0.85 |
| Kors de Elarion | Four ways of watching: what's overdue, what's rare, what just changed, what echoes weekly. | Four independent statistical observers through Ariadne. | 1.0 |
| Axiomantes de Nemerion | Every key already exists somewhere in the Labyrinth; the question is only whether the portal opens. | Combinatorial rank/unrank over 139.8M positions + Feistel permutation. | 0.75, conditional |
| Cartógrafos do Caos | We don't propose — we describe. | Five analytical books (constellations, cycles, trends, randomness, Markov chains). Does not vote. | — |
| Clãs Anões das Montanhas | Three forges, three philosophies, one mountain. | Clan-based combinatorial pools filtered by sum range. | 0.35 |
| Fadas Lunélia | Everyday numbers carry an everyday weight. | Weighted sampling biased toward familiar numbers. | 1.0 |
| Lobisomens de Fenrir | The pack only hunts when the moon allows it. | Monte Carlo simulation, active only on full-moon weeks. | 0.80 |
| Treefolks da Floresta Ancestral | We test hypotheses; we don't declare truths. | ML-flavored scoring measuring its own "statistical ghost." | 0.90 |
| Melforks Genéticos | Born in a laboratory, not a forest — but still Clerics at heart. | Micro genetic algorithm: elite crossover + fitness scoring. | 1.0 |
| Esqueletos das Catacumbas Numéricas | A moving window remembers exactly as much as it should. | Sliding 25-number window ritual. | 0.80 |
| Cronomantes da Ordem do Tempo | The extraction itself has a rhythm, measured in milliseconds. | Derives keys from sub-second event timing + lunar age. | 1.0 (own weight key) |
| Mystics — Nature (Druids, Moon Priests, Star Gazers) | The pattern already exists outside us; we listen, we don't calculate. | Placeholder — no algorithm yet, abstains every run. | 0.5 each |
| Mystics — Prophecy (Shamans, Witches, Seers, Oracles, Bone Readers) | The pattern isn't found, it's interpreted through ritual. | Placeholder — no algorithm yet, abstains every run (Oracles by design, permanently). | 0.5 each |
| Clérigos | The population itself is the strategy — breed, compete, survive. | Genetic algorithm across 8 archetypes (Bruxa, Vidente, Chefe Tribal, Elfo, Goblin, Shaman, Cronomante, Esqueleto). | 1.0 (finalists) |

## The one universal rule

No race's lore ever justifies a higher win rate. Every proposal — mystic or mathematical, ancient or brand new, weight 0.35 or weight 1.4 — passes through the same filter, the same weighted vote, the same Backtesting engine. See `races/mystics/README.md`'s "Design constraint" for the canonical phrasing of this principle; it applies to all 20 races equally, not just the Mystics.
