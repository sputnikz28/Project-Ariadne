"""Mago representatives — one of four Pantheon archetypes.

Invoked directly by main.py, outside Council voting (same pattern as
Black Squad and Elven Order). Blends overdue-number insight with
hot-number affinity.
"""
from core.services.combinations import normalize_candidate


def create_mage_representatives(ctx, quantity=2):
    est = ctx['estatisticas']
    rng = ctx['rng']
    out = []
    for i in range(quantity):
        nums = rng.sample([n for n, _ in est['atrasados'][:5]], 2) + rng.sample(est['quentes'], 3)
        stars = rng.sample(est['estrelas_quentes'], 2)
        out.append({
            'nome': f'Mago-{i + 1}',
            'tipo': 'Mago',
            'chave': normalize_candidate(nums, stars, rng),
        })
    return out
