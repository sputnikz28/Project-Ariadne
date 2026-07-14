"""Bone Readers — Prophecy Mystics, ancient tribal diviners who cast
sacred bones to reveal hidden paths.

Placeholder faction: no prediction algorithm implemented yet. Always
abstains (returns []), same as any faction with nothing to contribute
this run. See races/mystics/prophecy/bone_readers/ for lore,
characters and artifacts.
"""

FACTION_META = {
    'name': 'Bone Readers',
    'origin': 'bone_readers',
    'home': 'Fossa dos Ossos Sagrados',
    'config_section': 'BONE_READERS',
    'weight_key': 'peso_conselho',
    'default_weight': 0.5,
}


def council(ariadne=None, seed=None, cfg=None, ctx=None):
    """Future role: pseudo-random ritual generators, ritual seeds,
    symbolic combinations. Not implemented yet — always abstains.
    """
    return []
