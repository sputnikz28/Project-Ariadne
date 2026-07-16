import random
import heapq
from races.legacy import normalize
from core.services.fitness import fitness


def werewolves(cfg, ctx):
    fase = ctx['mundo']['fase_lua']
    ativo = cfg.getboolean('LOBISOMENS', 'ativo') and (
        not cfg.getboolean('LOBISOMENS', 'apenas_semana_lua_cheia')
        or fase in {'gibosa crescente', 'cheia', 'gibosa minguante'}
    )
    if not ativo:
        return {'ativo': False, 'simulacoes': 0, 'finalistas': []}
    heap = []
    sims = cfg.getint('LOBISOMENS', 'simulacoes_monte_carlo')
    reps = cfg.getint('LOBISOMENS', 'representantes')
    for _ in range(sims):
        c = (sorted(random.sample(range(1, 51), 5)), sorted(random.sample(range(1, 13), 2)))
        f = fitness(c, ctx['estatisticas'])
        r = (f, tuple(c[0]), tuple(c[1]))
        if len(heap) < 100:
            heapq.heappush(heap, r)
        elif f > heap[0][0]:
            heapq.heapreplace(heap, r)
    top = sorted(heap, reverse=True)[:reps]
    return {
        'ativo': True,
        'simulacoes': sims,
        'finalistas': [
            {'nome': f'Fenrir-{i+1}', 'tipo': 'Lobisomem', 'fitness': f, 'chave': normalize(list(n), list(e))}
            for i, (f, n, e) in enumerate(top)
        ],
    }
