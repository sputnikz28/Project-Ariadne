"""Oracles — Prophecy Mystics. They never generate keys directly; they
interpret the proposals produced by the Grand Council.

Architecture note: Oracles are conceptually closer to an analytical
faction (like factions/chaos_cartographers/) than to a key-generating
one — their future role is to rank and judge *other* factions'
proposals, not to submit new candidate keys. For now they still
register normally through FactionRegistry and abstain (return []),
per the requirement that every plugin register correctly; once
meta-analysis is implemented, propose() may legitimately continue to
always return [] even while doing real analytical work elsewhere.

Placeholder faction: no algorithm implemented yet. See
races/mystics/prophecy/oracles/ for lore, characters and artifacts.
"""

FACTION_META = {
    'name': 'Oracles',
    'origin': 'oracles',
    'home': 'Salão dos Espelhos Silenciosos',
    'config_section': 'ORACLES',
    'weight_key': 'peso_conselho',
    'default_weight': 0.5,
}


def council(ariadne=None, seed=None, cfg=None, ctx=None):
    """Future role: proposal ranking, confidence estimation,
    meta-analysis of the Council's own proposals. Not implemented
    yet — always abstains (never submits a candidate key).
    """
    return []
