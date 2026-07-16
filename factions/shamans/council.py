"""Shamans — Prophecy Mystics, communicate with ancestral spirits.

Placeholder faction: no prediction algorithm implemented yet. Always
abstains (returns []), same as any faction with nothing to contribute
this run. See races/mystics/prophecy/shamans/ for lore, characters and
artifacts.
"""

FACTION_META = {
    'name': 'Shamans',
    'origin': 'shamans',
    'home': 'Tendas do Vento Ancestral',
    'config_section': 'SHAMANS',
    'weight_key': 'peso_conselho',
    'default_weight': 0.5,
}


def council(ariadne=None, seed=None, cfg=None, ctx=None):
    """Future role: rare events, outliers, symbolic randomness,
    unusual historical patterns. Not implemented yet — always abstains.
    """
    return []
