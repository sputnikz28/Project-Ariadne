import random
from itertools import combinations
from races.legacy import normalize


def dwarves(cfg, ctx):
    out = []
    est = ctx['estatisticas']
    names = ['Barbas de Ferro', 'Cristal Azul', 'Forja Negra']
    for name in names[:cfg.getint('ANOES', 'numero_clas')]:
        pool = list(dict.fromkeys(est['quentes'][:8] + est['frios'][:5] + ctx['historico'][-1]['numeros']))
        while len(pool) < 20:
            n = random.randint(1, 50)
            if n not in pool:
                pool.append(n)
        ep = list(dict.fromkeys(est['estrelas_quentes'][:2] + est['estrelas_frias'][:2] + ctx['historico'][-1]['estrelas']))
        while len(ep) < 4:
            e = random.randint(1, 12)
            if e not in ep:
                ep.append(e)
        cart = []
        cnums = list(combinations(sorted(pool[:20]), 5))
        random.shuffle(cnums)
        for ns in cnums:
            if 85 <= sum(ns) <= 190:
                for es in combinations(sorted(ep[:4]), 2):
                    cart.append(normalize(list(ns), list(es)))
                    if len(cart) >= cfg.getint('ANOES', 'chaves_por_cla'):
                        break
            if len(cart) >= cfg.getint('ANOES', 'chaves_por_cla'):
                break
        out.append({
            'nome': name,
            'lider': 'Rei ' + random.choice(['Thorin', 'Borin', 'Dain']),
            'pool': sorted(pool[:20]),
            'estrelas_pool': sorted(ep[:4]),
            'carteira': cart,
        })
    return out
