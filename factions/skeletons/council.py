from races.skeletons import create_representatives as _create_representatives

FACTION_META = {
    'name': 'Esqueletos das Catacumbas Numéricas',
    'origin': 'esqueleto',
    'home': 'Catacumbas Numéricas',
    'config_section': 'ESQUELETOS',
    'weight_key': 'peso_conselho',
    'default_weight': 0.80,
}


def council(ariadne=None, seed=None, cfg=None, ctx=None):
    if cfg is None or ctx is None:
        return []
    return _create_representatives(cfg, ctx)
