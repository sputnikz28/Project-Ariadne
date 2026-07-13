"""
Labirinto de Nemerion — matemática do Universo Combinatório.

Rank/unrank para C(50,5) x C(12,2) e permutação Feistel reproduzível.
139.838.160 câmaras; nenhuma repetida; nenhuma perdida.
"""

from math import comb

UNIVERSE = 139_838_160   # C(50,5) * C(12,2) = 2_118_760 * 66
_H = 11826               # ceil(sqrt(UNIVERSO)); _H^2 = 139_854_276 > UNIVERSO

# ---------------------------------------------------------------------------
# Rank / unrank
# ---------------------------------------------------------------------------

def rank_numbers(nums):
    """Índice combinatório de 5 números de {1..50}. Resultado em [0, C(50,5)-1]."""
    c = sorted(x - 1 for x in nums)   # 0-indexed
    return comb(c[0], 1) + comb(c[1], 2) + comb(c[2], 3) + comb(c[3], 4) + comb(c[4], 5)


def unrank_numbers(r):
    """Inverso de rank_numeros. Devolve lista ordenada de 5 números de {1..50}."""
    result = []
    for k in range(5, 0, -1):
        c = k - 1
        while comb(c + 1, k) <= r:
            c += 1
        result.append(c + 1)
        r -= comb(c, k)
    return sorted(result)


def rank_stars(ests):
    """Índice combinatório de 2 estrelas de {1..12}. Resultado em [0, C(12,2)-1]."""
    a, b = sorted(x - 1 for x in ests)
    return comb(a, 1) + comb(b, 2)


def unrank_stars(r):
    """Inverso de rank_estrelas. Devolve lista ordenada de 2 estrelas de {1..12}."""
    b = 1
    while comb(b + 1, 2) <= r:
        b += 1
    a = r - comb(b, 2)
    return [a + 1, b + 1]


def rank_key(nums, ests):
    """Índice único de (nums, ests) em [0, UNIVERSO-1]."""
    return rank_numbers(nums) * 66 + rank_stars(ests)


def unrank_key(r):
    """Devolve (nums, ests) a partir de índice em [0, UNIVERSO-1]."""
    return unrank_numbers(r // 66), unrank_stars(r % 66)


# ---------------------------------------------------------------------------
# Feistel — permutação pseudoaleatória sobre [0, UNIVERSO-1]
# ---------------------------------------------------------------------------

def _mix(val, key):
    """Wang integer hash — mistura val com key, devolve 32 bits."""
    x = (val ^ (key & 0xFFFFFFFF)) & 0xFFFFFFFF
    x = (x ^ (x >> 16)) & 0xFFFFFFFF
    x = (x * 0x45D9F3B) & 0xFFFFFFFF
    x = (x ^ (x >> 16)) & 0xFFFFFFFF
    x = (x * 0x45D9F3B) & 0xFFFFFFFF
    x = x ^ (x >> 16)
    return x & 0xFFFFFFFF


def _round_key(seed, r):
    return ((seed & 0xFFFFFFFF) * 2654435761 + r * 1013904223) & 0xFFFFFFFF


def _feistel_base(idx, seed):
    """Bijecção sobre [0, _H^2-1]. 4 rondas aditivas com swap."""
    L, R = divmod(idx, _H)
    for r in range(4):
        rk = _round_key(seed, r)
        F = _mix(R, rk) % _H
        L, R = R, (L + F) % _H
    return L * _H + R


def _feistel_base_inv(idx, seed):
    """Inverso de _feistel_base."""
    L, R = divmod(idx, _H)
    for r in reversed(range(4)):
        rk = _round_key(seed, r)
        F = _mix(L, rk) % _H
        L, R = (R - F) % _H, L
    return L * _H + R


def key_at_position(pos, seed):
    """Chave (nums, ests) na posição pos da sequência Feistel."""
    idx = _feistel_base(pos, seed)
    while idx >= UNIVERSE:
        idx = _feistel_base(idx, seed)
    return unrank_key(idx)


def key_position(nums, ests, seed):
    """Posição de (nums, ests) na sequência Feistel — O(1) (sem iterar 139M vezes)."""
    idx = rank_key(nums, ests)
    pos = _feistel_base_inv(idx, seed)
    while pos >= UNIVERSE:
        pos = _feistel_base_inv(pos, seed)
    return pos
