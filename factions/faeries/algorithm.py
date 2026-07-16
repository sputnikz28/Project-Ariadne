import random
from races.legacy import normalize


def faeries(cfg, ctx):
    if not cfg.getboolean('FADAS', 'ativo'):
        return []
    nq = [int(x) for x in cfg['FADAS']['numeros_quotidiano'].split(',')]
    eq = [int(x) for x in cfg['FADAS']['estrelas_quotidiano'].split(',')]
    est = ctx['estatisticas']
    out = []
    for i in range(cfg.getint('FADAS', 'quantidade')):
        rank = []
        for n in range(1, 51):
            sc = .4 * (1 - abs(n - 25.5) / 25.5) + .25 * est['atraso_norm'][n] + .2 * est['freq_norm'][n] + .15 * (n in nq)
            rank.append((n, max(.001, sc)))
        nums = [n for n, _ in rank]
        weights = [s for _, s in rank]
        key = None
        for _ in range(2000):
            c = list(dict.fromkeys(random.choices(nums, weights=weights, k=12)))
            if len(c) < 5:
                continue
            ns = sorted(random.sample(c, 5))
            pares = sum(n % 2 == 0 for n in ns)
            if any(n <= 10 for n in ns) and set(ns) & set(est['quentes']) and set(ns) & set(est['frios']) and 100 <= sum(ns) <= 170 and pares in (2, 3):
                key = ns
                break
        if key is None:
            key = sorted(random.sample(range(1, 51), 5))
        re = sorted(((e, .5 * est['freq_est_norm'][e] + .35 * est['atraso_est_norm'][e] + .15 * (e in eq)) for e in range(1, 13)), key=lambda x: x[1], reverse=True)
        out.append({'nome': f'Lunélia-{i+1}', 'tipo': 'Fada', 'chave': normalize(key, [e for e, _ in re[:2]])})
    return out
