"""Druids — Nature Mystics, masters of forests and lunar cycles.

Placeholder faction: no prediction algorithm implemented yet. Always
abstains (returns []), same as any faction with nothing to contribute
this run. See races/mystics/nature/druids/ for lore, characters and
artifacts.
"""

FACTION_META = {
    'name': 'Druids',
    'origin': 'druids',
    'home': 'Círculo do Carvalho Eterno',
    'config_section': 'DRUIDS',
    'weight_key': 'peso_conselho',
    'default_weight': 0.5,
}


def council(ariadne=None, seed=None, cfg=None, ctx=None):
    """Future role: lunar phases, seasons, solstices, equinoxes, ISO
    week cycles. Not implemented yet — always abstains.
    """
    return []
