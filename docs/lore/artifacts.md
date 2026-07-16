# Artifacts — Catalog

Master index of every named canon artifact, relic and book, now that all 20 race packages are complete. Per-race detail lives in `races/<name>/artifacts.json` — this is the cross-race lookup, plus everything that doesn't belong to a single race.

## Race-owned

| Race | Artifacts |
|---|---|
| Clérigos | Amuletos Vivos, Escolha Humana Consagrada pelos Clérigos, Caminho das 1000 Almas |
| Vampiros de Elarion | Índice de Triplas, Anel de Vaelor, Véu Sombrio, Taça de Sangue Estatístico |
| Gárgulas do Torreão de Pedra | Índice de Duplas, Asa de Granito, Espelho de Granito |
| Kors de Elarion | Pergaminho dos Atrasados, Brasa Fria, Mapa das Passagens, Papiro Kor Preto |
| Axiomantes de Nemerion | Labirinto de Nemerion, Portal do Labirinto |
| Cartógrafos do Caos | Livro das Constelações, Livro dos Intervalos, Livro das Correntes, Livro do Acaso Esperado, Livro dos Ecos Sequenciais |
| Clãs Anões das Montanhas | Forja de Barbas de Ferro, Cristal de Borin, Martelo da Forja Negra |
| Fadas Lunélia | Pétala do Jardim Eterno, Colar dos Números Quotidianos |
| Lobisomens de Fenrir | Presa Imutável de Fenrir (also a universe-wide living amulet), Uivo da Lua Cheia |
| Treefolks da Floresta Ancestral | Pergaminho de Lua Cheia, Anéis de Crescimento |
| Melforks Genéticos | Tubo de Ensaio Ancestral, Registo de Gerações |
| Esqueletos das Catacumbas Numéricas | Ritual da Janela Móvel, Corredor Sem Entrada Fixa |
| Cronomantes da Ordem do Tempo | Relógio de Segundos Perdidos, Ampulheta Partida, Relógio Lunar |
| Mystics — Druids | Oak Staff, Moon Branch |
| Mystics — Moon Priests | Silver Crescent, Lunar Chalice |
| Mystics — Star Gazers | Celestial Astrolabe, Star Compass |
| Mystics — Shamans | Spirit Drum, Ancestral Mask |
| Mystics — Witches | Cauldron of Echoes, Crystal Vial |
| Mystics — Seers | Veil of Tomorrow, Hourglass of Echoes |
| Mystics — Oracles | Eye of Prophecy, Mirror of Destiny |
| Mystics — Bone Readers | Sacred Bones, Ivory Dice |

That's 21 races × 2–4 artifacts each = **50 race-owned canon artifacts**.

## Not race-exclusive

**The 9 Forbidden Books** (`artifacts/amulets/books.py`), guarded by the Scribes with class-gated access:

1. Grimório de Todas as Extrações — every draw ever recorded
2. Livro das Chamas Frequentes — hot numbers
3. Livro dos Esquecidos — cold numbers
4. Livro dos Pares Sagrados — sacred pairs
5. Livro dos Trios Proibidos — forbidden trios
6. Atlas das Doze Luzes — the twelve stars
7. Crónica dos Números Ausentes — delays/overdue
8. Geometria Secreta da Teia — gaps
9. Livro das Extrações por Cumprir — the next draw

**Living Amulets** (`artifacts/living.py`) — forged for any hero regardless of race, rarity COMUM→MITICO: Osso Lunar, Espelho dos Sonhos Esquecidos, Livro dos Ecos, Presa Imutável de Fenrir (also Werewolf-owned, see above — the one artifact that is both a race artifact and a universe-wide living amulet), Fragmento Divino, Lágrima da Primeira Luz, **Coroa Quebrada de Malphas** (the one amulet explicitly tied to the antagonist).

**Institutional relics:**

- **Grande Grimório das Extrações** — the scroll library itself, maintained by the Librarians.
- **Grimório Negro** — the Black Squad's persistent, learning knowledge-tracker.
- **Livro dos Ecos da Primeira Linha** — a hand-authored seed/prologue relic, created by Escriba Fundador, once owned by Gruk dos Astros and Velka dos Ossos before being stolen by the Black Squad.

## Not yet canon

Individual hero-forged relics (`artifacts/relics/*.json`, other than the seed above) are **runtime** — procedurally generated per campaign, not fixed canon items. See `canon_index.md`'s Canon vs Runtime section.
