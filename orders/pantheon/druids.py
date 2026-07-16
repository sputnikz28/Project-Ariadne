"""Druida representatives — one of four Pantheon archetypes.

Invoked directly by main.py, outside Council voting. Unrelated to the
Council faction factions/druids/ (Nature Mystics) despite the shared
name — that faction still abstains every run; this is a separate
narrative archetype that draws on hot-number affinity.
"""
from core.services.combinations import normalize_candidate


def create_druid_representatives(ctx, quantity=2):
    est = ctx['estatisticas']
    rng = ctx['rng']
    out = []
    for i in range(quantity):
        nums = rng.sample(est['quentes'], 5)
        stars = rng.sample(est['estrelas_quentes'], 2)
        out.append({
            'nome': f'Druida-{i + 1}',
            'tipo': 'Druida',
            'chave': normalize_candidate(nums, stars, rng),
        })
    return out
