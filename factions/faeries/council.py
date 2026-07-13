from races.extras import faeries as _faeries

FACTION_META = {
    'name': 'Fadas Lunélia',
    'origin': 'fada',
    'home': 'Jardim Eterno',
    'config_section': 'FADAS',
    'weight_key': 'peso_conselho',
    'default_weight': 1.0,
}


def council(ariadne=None, seed=None, cfg=None, ctx=None):
    if cfg is None or ctx is None:
        return []
    return _faeries(cfg, ctx)
