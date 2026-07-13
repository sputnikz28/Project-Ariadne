from races.extras import werewolves as _werewolves

FACTION_META = {
    'name': 'Lobisomens de Fenrir',
    'origin': 'lobisomem',
    'home': 'Floresta da Lua Cheia',
    'config_section': 'LOBISOMENS',
    'weight_key': 'peso_conselho',
    'default_weight': 0.80,
}


def council(ariadne=None, seed=None, cfg=None, ctx=None):
    """Returns {'ativo': bool, 'simulacoes': int, 'finalistas': list}."""
    if cfg is None or ctx is None:
        return {'ativo': False, 'simulacoes': 0, 'finalistas': []}
    return _werewolves(cfg, ctx)
