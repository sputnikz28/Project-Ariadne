from races.extras import treefolks as _treefolks

FACTION_META = {
    'name': 'Treefolks da Floresta Ancestral',
    'origin': 'treefolk',
    'home': 'Floresta Ancestral',
    'config_section': 'TREEFOLKS',
    'weight_key': 'peso_conselho',
    'default_weight': 0.90,
}


def council(ariadne=None, seed=None, cfg=None, ctx=None):
    if cfg is None or ctx is None:
        return []
    return _treefolks(cfg, ctx)
