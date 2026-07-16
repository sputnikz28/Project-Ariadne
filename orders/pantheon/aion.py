"""Aion — the fourth Pantheon archetype, aggregating the other three.

Invoked directly by main.py, outside Council voting. Counts the numbers
and stars proposed by Magos, Druidas and Djinns, and keeps the most
common as its own "Deus"-tier key.
"""
from collections import Counter
from core.services.combinations import normalize_candidate


def create_aion(representatives, ctx):
    rng = ctx['rng']
    vn, ve = Counter(), Counter()
    for v in representatives:
        vn.update(v['chave'][0])
        ve.update(v['chave'][1])
    nums = [n for n, _ in vn.most_common(5)]
    stars = [e for e, _ in ve.most_common(2)]
    return {
        'nome': 'Aion',
        'tipo': 'Deus',
        'chave': normalize_candidate(nums, stars, rng),
    }
