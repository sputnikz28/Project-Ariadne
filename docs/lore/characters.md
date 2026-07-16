# Characters — Encyclopedia

Full encyclopedia of every canon character, now that all 21 race packages are complete (V11 added Clerics). Full biographies live in each race's `characters.json`; this is the cross-race browse view. See `canon_index.md` for the id lookup table.

## Clérigos

Not fixed individuals — a procedurally-regenerated population from 10 names × 6 titles × 6 houses. `characters.json` documents the 8 ancestral archetypes (generation methods) instead:

- **Bruxa** — mixes hot/cold numbers with a personal touch of chance.
- **Vidente** — trusts hot numbers, influenced by the most recent draw when the hero's genome "clarity" is high.
- **Chefe Tribal** — displaces a starting number through 5 ritual symbols (sun, moon, wolf, fire, water, mountain, raven).
- **Elfo** — the most disciplined archetype: rejects any candidate failing sum/parity/gap constraints, up to 1000 tries.
- **Goblin** — bets on high numbers when the jackpot is large, samples freely otherwise.
- **Shaman** — displaces the last draw by the current moon phase (the archetype dispatcher's fallback).
- **Cronomante** — borrows `factions/chronomancers/algorithm.py` directly, no logic of its own.
- **Esqueleto** — borrows `factions/skeletons/algorithm.py` directly, no logic of its own.

## Vampiros de Elarion

- **Conde Vaelor** — Senhor da Linhagem Sanguínea. Trusts raw historical recurrence.
- **Lady Nyx** — Senhora da Linhagem Sombria. Trusts consecutive-number neighborliness.
- **Morwenna das Contagens Silenciosas** — Arquivista-Chefe; maintains the Índice de Triplas both lineages depend on.

## Gárgulas do Torreão de Pedra

- **Gorath** — Senhor da Linhagem de Pedra. Trusts consistent historical pairs.
- **Seraphine** — Senhora da Linhagem do Espelho. Trusts consecutive, symmetric pairs.

## Kors de Elarion

- **Aelyra dos Silêncios** (Kor Branco) — reads overdue numbers.
- **Kael da Chama Fria** (Kor Vermelho) — reads the least-frequent numbers.
- **Sylvara das Passagens** (Kor Verde) — reads transitions between consecutive draws.
- **Nyxara das Sombras Semanais** (Kor Preto) — reads weekly echoes, writes to the Papiro Kor Preto archive.

## Axiomantes de Nemerion

- **Axiomantes de Nemerion** (voz colectiva) — the order's single collective voice; no individual Axiomantes named yet, a known canon gap.

## Cartógrafos do Caos

- **Eldran das Constelações** — co-occurrence network and centrality between numbers.
- **Vesara dos Intervalos** — historical delays, averages, maxima, full cycles.
- **Lirien das Correntes** — windowed trends, low vs high, final digits.
- **Thalvos do Acaso Esperado** — Monte Carlo, real vs expected-random comparison.
- **Oryn dos Ecos Sequenciais** — Markov transitions, neighborhood, consecutive sequences.

## Clãs Anões das Montanhas

- **Rei Thorin** (Barbas de Ferro) — the most conservative king, favors hot-number pools.
- **Rei Borin** (Cristal Azul) — the most analytical, balances hot and cold.
- **Rei Dain** (Forja Negra) — the most prolific, largest key output per session.

## Fadas Lunélia

- **Lunélia** (archetype) — every representative is a numbered Lunélia-N; believes everyday human number choices carry real weight.

## Lobisomens de Fenrir

- **Fenrir** (archetype) — the pack's collective spirit; every finalist is a numbered Fenrir-N, chosen by Monte Carlo. One of two forces (with the Clérigos) that purify Council War corruption.

## Treefolks da Floresta Ancestral

- **Grande Carvalho Ancestral** — the fixed investigator character; tests whether the moon phase affects draw patterns, always honestly inconclusive.
- **Raiz** (archetype) — numbered representatives (Raiz-N), each borrowing one of four ritual "model" names (Random Forest, Rede Neural, LSTM, Bayesiano).

## Melforks Genéticos

- **Clérigo** (archetype) — numbered representatives (Clérigo-N), genetically descended from the Clerics lineage, reborn each session's evolutionary cycle.

## Esqueletos das Catacumbas Numéricas

- **Ossário da Cripta**, **Tíbia do Intervalo**, **Crânio das Vinte e Cinco Pedras**, **Marfim das Seis Estrelas**, **Fémur do Corredor Móvel** — five named relic-characters, each a sliding-window style.

## Cronomantes da Ordem do Tempo

- **Aurel dos Segundos Perdidos**, **Chrona da Ampulheta Partida**, **Kairon do Último Instante**, **Selvar, Guardião do Pulso**, **Nym do Relógio Lunar** — five chronomancers at different index offsets of the same temporal formula.

## Mystics

Sixteen characters, two per order — full entries in each order's `characters.json`:

- **Druids:** Thistlewood Greenbark, Wren Hollowmoss
- **Moon Priests:** Selwyn Nightveil, Lyanna Duskwhisper
- **Star Gazers:** Orion Farsight, Vesper Skyholt
- **Shamans:** Kova Ashwalker, Mireya Bonesong
- **Witches:** Hessa Emberweave, Fennira Duskbrew
- **Oracles:** Cassiel Farwatcher, Delphine Mirrorsworn
- **Seers:** Isolde Farsight, Baltasar Windmere
- **Bone Readers:** Grukka Stonejaw, Thane Ivoryfall

## Esquadrão Negro (Black Squad)

Morthak da Sombra, Veyron Eclipse, Nyx do Desvio, Sable das Matrizes, Kharon dos Ecos Mortos, Zareth Anti-Humano — six named mages; currently held by Zareth Anti-Humano: the stolen relic "Livro dos Ecos da Primeira Linha."

## Ordem Élfica (Elven Order)

Kael da Folha Negra, Thalion Passo Silencioso, Arya da Lâmina Verde, Elyndor Sem Pegadas, Naeris do Orvalho Escuro — five ninjas who raid the Black Squad's dark library in two-person teams.

## Bibliotecários / Escribas

- **Orion dos Arquivos** — signs every scroll converted into the Grande Grimório das Extrações.
- **Escriba Fundador** — historical creator of the seed relic Livro dos Ecos da Primeira Linha.

## Legendary echoes

- **Íria da Névoa Azul** — Vidente, Era dos Primeiros Oráculos (Era I). Canon seed character, dormant (`ECO_ADORMECIDO`) until a real result confirms her key. Later resurrected — corrupted — by the Black Squad as "Íria da Névoa Azul Eclipse."

## Cosmological entities

- **Ariadne** — guardian of the Biblioteca Eterna, purely descriptive.
- **Malphas, o Quebra-Conselhos** — the universal antagonist; corrupts the Council's final chosen key.
- **Aion** — the Pantheon's aggregate "Deus"-tier being, thematically tied to the Ordem do Tempo.

## Totals

- **21 races** now have named characters, archetypes, or a named collective voice — full coverage.
- **~54 race-level named/archetype characters** (including the 8 Clerics archetypes) + 16 Mystics + 6 Black Squad + 5 Elven Order + 3 institutional/cosmological = the full canon cast.
- Remaining known gap: Axiomantes has only a collective voice, no individuals — see `canon_index.md`, "Known canon gaps."
