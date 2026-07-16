"""Djinn representatives — one of four Pantheon archetypes.

Invoked directly by main.py, outside Council voting. Perturbs the
previous draw's numbers with small random displacements.
"""
from core.services.combinations import normalize_candidate


def create_djinn_representatives(ctx, quantity=2):
    hist = ctx['historico']
    rng = ctx['rng']
    out = []
    for i in range(quantity):
        nums = [max(1, min(50, n + rng.choice([-5, -3, -1, 1, 3, 5]))) for n in hist[-1]['numeros']]
        stars = [max(1, min(12, e + rng.choice([-2, -1, 1, 2]))) for e in hist[-1]['estrelas']]
        out.append({
            'nome': f'Djinn-{i + 1}',
            'tipo': 'Djinn',
            'chave': normalize_candidate(nums, stars, rng),
        })
    return out
