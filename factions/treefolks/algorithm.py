import random
from core.services.combinations import normalize_candidate


def treefolks(cfg, ctx):
    if not cfg.getboolean('TREEFOLKS', 'ativo'):
        return []
    est = ctx['estatisticas']
    out = []
    for i in range(cfg.getint('TREEFOLKS', 'quantidade')):
        tr = round(random.uniform(.7, .95), 3)
        te = round(random.uniform(.08, .3), 3)
        fa = round(tr - te, 3)
        rn = sorted(((n, .45 * est['freq_norm'][n] + .35 * est['atraso_norm'][n] + .2 * random.random()) for n in range(1, 51)), key=lambda x: x[1], reverse=True)
        re = sorted(((e, .55 * est['freq_est_norm'][e] + .3 * est['atraso_est_norm'][e] + .15 * random.random()) for e in range(1, 13)), key=lambda x: x[1], reverse=True)
        out.append({
            'nome': f'Raiz-{i+1}',
            'tipo': 'Treefolk',
            'modelo': random.choice(['Random Forest', 'Rede Neural', 'LSTM', 'Bayesiano']),
            'treino': tr, 'teste': te, 'fantasma': fa,
            'peso': max(.02, 1 - fa),
            'chave': normalize_candidate([n for n, _ in rn[:5]], [e for e, _ in re[:2]], random),
        })
    return out
