"""Moon Priests — Nature Mystics, guardians of the lunar temples.

Placeholder faction: no prediction algorithm implemented yet. Always
abstains (returns []), same as any faction with nothing to contribute
this run. See races/mystics/nature/moon_priests/ for lore, characters
and artifacts.
"""

FACTION_META = {
    'name': 'Moon Priests',
    'origin': 'moon_priests',
    'home': 'Templo da Lua Prateada',
    'config_section': 'MOON_PRIESTS',
    'weight_key': 'peso_conselho',
    'default_weight': 0.5,
}


def council(ariadne=None, seed=None, cfg=None, ctx=None):
    """Future role: new moon, full moon, eclipses, lunar calendars.
    Not implemented yet — always abstains.
    """
    return []
