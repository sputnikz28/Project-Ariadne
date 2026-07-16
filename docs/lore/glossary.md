# Glossary — Project Ariadne

## World & institutions

- **Grande Conselho (the Council)** — the weighted-vote body every faction proposes a key to. Filters, votes, backtests every proposal identically regardless of race.
- **Ariadne** (`entity:ariadne`) — guardian of the Biblioteca Eterna; purely descriptive, never predictive. Every one of her methods' outputs carries the disclaimer "não aumenta a probabilidade de prever um sorteio futuro."
- **Biblioteca Eterna (Eternal Library)** — the narrative-layer hub; see `geography.md`.
- **Juízes (the Judges)** — evaluate every faction's historical proposals through Backtesting, without favoring ritual over statistics or vice-versa.
- **Backtesting** — the mechanism (`compare_result.py`) that scores past proposals against real draw results.

## Antagonists & conflict

- **Malphas, o Quebra-Conselhos** (`entity:malphas`) — the universal antagonist. Corrupts the Council's final chosen key. His virus mechanic (`world/engine/malphas_virus.py`) infects Clerics population members specifically; any race's proposal can still become the corruption *target* if selected as final.
- **Guerra do Conselho (Council War)** — the yearly confrontation between an infected carrier and the purifying forces (Clérigos + Lobisomens de Fenrir).
- **Convicção Sombria (Dark Conviction)** — Malphas's ritual mantra-chanting mechanic, run after every Council session.
- **Guerra das Sombras (War of Shadows)** — the persistent V5-era conflict between the Esquadrão Negro and the Ordem Élfica over stolen knowledge.
- **Esquadrão Negro (Black Squad)** — steals relics, corrupts books into "Reflexos Sombrios" (shadow copies), performs necromancy on legendary echoes. A separate corrupting force from Malphas — not confirmed to be his agent.
- **Ordem Élfica (Elven Order)** — Black Squad's counterpart; raids the dark library to recover and purify what was stolen.
- **Grimório Negro (Black Grimoire)** — the Black Squad's persistent, learning knowledge-tracker.

## Portal, Labyrinth & mathematics

- **Portal (Axiomantes)** — opens when historical coverage ≥ 50% and excess ≥ 0; only then do the Axiomantes vote.
- **Labirinto de Nemerion** — the combinatorial space of all 139,838,160 possible keys, addressed via rank/unrank + Feistel permutation.

## Grading & legends

- **Livro das Personagens Lendárias (Book of Legendary Characters)** — runtime log of any character/proposal scoring ≥3 numbers + 2 stars against a real result. **Runtime, not canon** — see `canon_index.md`.
- **Grades**, worst to best: BRONZE, PRATA, OURO, PLATINA, DIAMANTE, DIVINO, IMORTAL (5 numbers + 2 stars).
- **Eco Lendário (Legendary Echo)** — an entry in the above book, or a deliberately hand-authored seed character like Íria da Névoa Azul.
- **Ressuscitar (Resurrect)** — the Black Squad's necromancy mechanic: brings back a legendary echo, appending " Eclipse" to its name and corrupting it.

## Ritual & world mechanics

- **Ritual Celeste (Celestial Ritual)** — souls (eliminated/resurrected Clerics heroes) donate energy scaled by title and amulets, producing the "Escolha Humana Consagrada pelos Clérigos" — a human-blessed key with its own Council weight.
- **Caminho das 1000 Almas (Path of the 1000 Souls)** — resurrection tournament mechanic for eliminated Clerics heroes.
- **Painel dos Deuses (Panel of the Gods)** — V6.1 mechanic separating world rules into swappable profiles.
- **Pressão do Destino (Pressure of Destiny)** — counter of consecutive draws with zero winners; a narrative tension gauge in `world/engine/builder.py`.
- **Panteão (Pantheon)** — Magos, Druida-representatives, Djinns and Aion; summoned directly by `main.py`, outside Council voting (`orders/pantheon/`).

## Canon vs Runtime

See `canon_index.md`'s dedicated section — the single most important distinction for anyone extending this lore.
