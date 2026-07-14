# Oracles

**Lineage:** Prophecy Mystics · **Home:** Salão dos Espelhos Silenciosos

They never generate keys directly — they interpret the proposals
produced by the Grand Council. Full entry, philosophy and future
analytical role in [`../../orders.json`](../../orders.json) (id
`oracles`).

**Architecture note:** by design, Oracles don't propose new candidate
keys — their future role is ranking and judging *other* factions'
proposals (proposal ranking, confidence estimation, meta-analysis),
closer in spirit to `factions/chaos_cartographers/` (analytical) than
to a key-generating faction. For now, the placeholder still registers
normally through `FactionRegistry` and abstains (`propose()` returns
`[]`), per this task's requirement that every plugin register
correctly. See `nota_arquitetura` in `orders.json`.

**Characters:** Cassiel Farwatcher, Delphine Mirrorsworn — see
[`../../characters.json`](../../characters.json).

**Artifacts:** Eye of Prophecy, Mirror of Destiny — see
[`../../artifacts.json`](../../artifacts.json).

**Faction plugin:** [`factions/oracles/`](../../../../factions/oracles)
— currently a placeholder that registers and abstains; no prediction
or meta-analysis logic implemented yet.
