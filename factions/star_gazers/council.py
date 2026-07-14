"""Star Gazers — Nature Mystics, masters of celestial observation.

Placeholder faction: no prediction algorithm implemented yet. Always
abstains (returns []), same as any faction with nothing to contribute
this run. See races/mystics/nature/star_gazers/ for lore, characters
and artifacts.
"""

FACTION_META = {
    'name': 'Star Gazers',
    'origin': 'star_gazers',
    'home': 'Observatório de Vidro Celeste',
    'config_section': 'STAR_GAZERS',
    'weight_key': 'peso_conselho',
    'default_weight': 0.5,
}


def council(ariadne=None, seed=None, cfg=None, ctx=None):
    """Future role: Euromillions stars, stellar combinations, celestial
    symbolism. Not implemented yet — always abstains.
    """
    return []
