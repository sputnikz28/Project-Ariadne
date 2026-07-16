# Geography — Project Ariadne

A map in prose, organized by region. See `locations.md` for a detailed entry per place, and `canon_index.md` for place ids.

## Two layers, one world

Project Ariadne runs on two layers that never mix mechanically but sit on top of each other narratively:

1. **The real layer** — `place:paris`. The actual Euromillions draw happens in Paris, França, `Europe/Paris` timezone (`world/engine/builder.py`, `config.txt [MUNDO]`). This is the literal, unfantastical anchor: a real weekday, a real season, a real moon phase, a real jackpot figure.
2. **The narrative layer** — everything else in this document. A fantasy realm of libraries, crypts, towers and forests that *interprets* the real draw, never predicts it. Every race's homeland exists in this layer.

## The Biblioteca Eterna — the hub

`place:biblioteca_eterna` sits at the center of the narrative layer, physically and thematically. Every race, sooner or later, passes through it: the Librarians (`order:librarians`) convert real draw data into scrolls here; the Scribes (`order:scribes`) keep the Museu do Mosteiro and the Atlas do Universo here; the Chaos Cartographers publish their five books here; Ariadne (`entity:ariadne`) is its guardian. The Cripta Eterna and the Torreão de Pedra are built into or onto the Library's own structure — the Vampires beneath its oldest archives, the Gárgulas on its highest tower.

## Elarion

`place:elarion` is the shared realm/city referenced by two races' full names — "Vampiros **de Elarion**" and "Kors **de Elarion**." The Kors' home is Elarion itself; the Vampires' specific site within it is the Cripta Eterna. The two races are geographic neighbors, which explains their professional-rivalry banter (see `relationships.md`) better than coincidence would.

## The Mountain–Forest belt

South and west of the Library, a belt of wilderness holds the "V3 — Mundo Vivo" cohort, all arriving in the same era:

- `place:fortaleza_das_montanhas` — the Dwarves' mountain fortress, home to three clans (Barbas de Ferro, Cristal Azul, Forja Negra).
- `place:jardim_eterno` — the Faeries' eternal garden.
- `place:floresta_da_lua_cheia` — the Werewolves' forest, most active during the full moon.
- `place:floresta_ancestral` — the Treefolks' ancestral forest.

## Nemerion

`place:cidadela_de_nemerion` stands apart — deliberately isolated, reachable in lore only when the Axiomantes' Labyrinth portal opens. Its geography is combinatorial as much as physical: 139,838,160 chambers, per the Axiomantes' own mathematics.

## The Ordem do Tempo

`place:ordem_do_tempo` is less a fixed location than a standing order that exists "outside" ordinary geography — fitting for a race whose keys are derived from the millisecond-precise timing of the extraction event itself. Thematically linked to Aion (`entity:aion`) and the Panteão.

## Under the Library — Laboratório and Catacumbas

Two more sites sit beneath or adjacent to the Library rather than out in the wilderness:

- `place:laboratorio_genetico` — the Melforks' genetic laboratory, implied to be a literal offshoot of the Clerics' genetic-algorithm lineage.
- `place:catacumbas_numericas` — the Skeletons' catacombs, arrived alone in Era VI with no cohort.

## The Mystic homes

Two lineages, eight homes, none of them adjacent to each other by design — the Mystics are deliberately scattered, gathering only at the Council:

- Nature Mystics: `place:circulo_do_carvalho_eterno` (Druids), `place:templo_da_lua_prateada` (Moon Priests), `place:observatorio_de_vidro_celeste` (Star Gazers).
- Prophecy Mystics: `place:tendas_do_vento_ancestral` (Shamans), `place:caldeirao_das_encruzilhadas` (Witches), `place:torre_dos_olhos_abertos` (Seers), `place:salao_dos_espelhos_silenciosos` (Oracles), `place:fossa_dos_ossos_sagrados` (Bone Readers).

## Unmapped

The Esquadrão Negro (`order:black_squad`) and the Ordem Élfica (`order:elven_order`) have no named home in canon yet — see the "Known canon gaps" section of `canon_index.md`. Do not invent one without updating that file first.
