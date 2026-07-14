"""Seers — Prophecy Mystics, masters of visions.

Placeholder faction: no prediction algorithm implemented yet. Always
abstains (returns []), same as any faction with nothing to contribute
this run. See races/mystics/prophecy/seers/ for lore, characters and
artifacts.
"""

FACTION_META = {
    'name': 'Seers',
    'origin': 'seers',
    'home': 'Torre dos Olhos Abertos',
    'config_section': 'SEERS',
    'weight_key': 'peso_conselho',
    'default_weight': 0.5,
}


def council(ariadne=None, seed=None, cfg=None, ctx=None):
    """Future role: trend detection, historical evolution, recurring
    patterns. Not implemented yet — always abstains.
    """
    return []
