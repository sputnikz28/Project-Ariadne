from races.extras import dwarves as _dwarves

FACTION_META = {
    'name': 'Clãs Anões das Montanhas',
    'origin': 'cla_anao',
    'home': 'Fortaleza das Montanhas',
    'config_section': 'ANOES',
    'weight_key': 'peso_conselho',
    'default_weight': 0.35,
}


def council(ariadne=None, seed=None, cfg=None, ctx=None):
    """Returns list of clan dicts; each clan has 'carteira' with multiple keys."""
    if cfg is None or ctx is None:
        return []
    return _dwarves(cfg, ctx)
