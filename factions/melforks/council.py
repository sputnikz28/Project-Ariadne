from .algorithm import melforks as _melforks

FACTION_META = {
    'name': 'Melforks Genéticos',
    'origin': 'melfork',
    'home': 'Laboratório Genético',
    'config_section': 'MELFORKS',
    'weight_key': 'peso_conselho',
    'default_weight': 1.0,
}


def council(ariadne=None, seed=None, cfg=None, ctx=None):
    if cfg is None or ctx is None:
        return []
    return _melforks(cfg, ctx)
