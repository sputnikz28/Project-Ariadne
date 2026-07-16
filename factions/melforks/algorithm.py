import random
from races.legacy import normalize
from core.services.fitness import fitness


def melforks(cfg, ctx):
    if not cfg.getboolean('MELFORKS', 'ativo'):
        return []
    est = ctx['estatisticas']
    tam = cfg.getint('MELFORKS', 'populacao_chaves')
    pop = [normalize(random.sample(range(1, 51), 5), random.sample(range(1, 13), 2)) for _ in range(tam)]
    for _ in range(cfg.getint('MELFORKS', 'geracoes_chaves')):
        av = sorted(((fitness(c, est), c) for c in pop), key=lambda x: x[0], reverse=True)
        elite = [c for _, c in av[:cfg.getint('MELFORKS', 'elite')]]
        nova = elite[:]
        while len(nova) < tam:
            a, b = random.sample(elite, 2)
            pn = list(dict.fromkeys(a[0] + b[0]))
            pe = list(dict.fromkeys(a[1] + b[1]))
            nova.append(normalize(random.sample(pn, 5), random.sample(pe, 2)))
        pop = nova
    top = sorted(((fitness(c, est), c) for c in pop), key=lambda x: x[0], reverse=True)[:cfg.getint('MELFORKS', 'representantes')]
    return [{'nome': f'Clérigo-{i+1}', 'tipo': 'Melfork', 'fitness': f, 'chave': c} for i, (f, c) in enumerate(top)]
