from .algorithm import create_chronomancers as _create_chronomancers

FACTION_META = {
    'name': 'Cronomantes da Ordem do Tempo',
    'origin': 'cronomante',
    'home': 'Ordem do Tempo',
    'config_section': 'EXTRACAO',
    'weight_key': 'peso_cronomantes',
    'default_weight': 1.0,
}


def council(ariadne=None, seed=None, cfg=None, ctx=None):
    if cfg is None or ctx is None:
        return []
    return _create_chronomancers(cfg, ctx.get('extracao', {}), ctx.get('mundo', {}), ctx.get('rng'))
