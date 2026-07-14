# Oracles

Prophecy Mystics — they never generate keys directly; they interpret
the proposals produced by the Grand Council.

**Status:** placeholder only — no meta-analysis algorithm implemented
yet. `council()` always returns `[]` (a valid abstention), exactly
like a faction with nothing to contribute this run.

**Architecture note:** Oracles are conceptually analytical (closer to
`factions/chaos_cartographers/`) rather than key-generating — their
future role is to rank and judge *other* factions' proposals, not
submit new candidate keys. See the code comment in `council.py` for
detail.

**Future analytical role:** proposal ranking, confidence estimation,
meta-analysis.

**Lore, characters and artifacts:** see
[`races/mystics/prophecy/oracles/`](../../races/mystics/prophecy/oracles).
