"""Witches — Prophecy Mystics, masters of magical mixtures.

Placeholder faction: no prediction algorithm implemented yet. Always
abstains (returns []), same as any faction with nothing to contribute
this run. See races/mystics/prophecy/witches/ for lore, characters and
artifacts.
"""

FACTION_META = {
    'name': 'Witches',
    'origin': 'witches',
    'home': 'Caldeirão das Encruzilhadas',
    'config_section': 'WITCHES',
    'weight_key': 'peso_conselho',
    'default_weight': 0.5,
}


def council(ariadne=None, seed=None, cfg=None, ctx=None):
    """Future role: combine strategies, weighted voting, hybrid key
    generation, ensemble methods. Not implemented yet — always
    abstains.
    """
    return []
