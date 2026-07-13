"""
Perfil do Labirinto — análise estatística dos Ecos Históricos.

Calcula um perfil a partir das chaves encontradas antes do marco
e pontua chaves inéditas por afinidade com esse perfil.
"""

from collections import Counter
from math import sqrt

from .labyrinth import key_at_position, UNIVERSE


def calculate_profile(echoes):
    """
    Constrói o perfil estatístico a partir dos ecos (chaves históricas antes do marco).
    ecos: lista de {'numeros': [...], 'estrelas': [...], ...}
    """
    if not echoes:
        return None

    n = len(echoes)
    somas = [sum(e['numeros']) for e in echoes]
    soma_media = sum(somas) / n
    variancia = sum((s - soma_media) ** 2 for s in somas) / n
    sum_deviation = sqrt(variancia)

    parities = Counter()
    baixos_altos = Counter()
    freq_nums = Counter()
    freq_ests = Counter()
    gaps_medios = []
    amplitudes = []

    for e in echoes:
        ns = sorted(e['numeros'])
        es = e['estrelas']

        n_pares = sum(1 for x in ns if x % 2 == 0)
        parities[(n_pares, 5 - n_pares)] += 1

        n_baixos = sum(1 for x in ns if x <= 25)
        baixos_altos[(n_baixos, 5 - n_baixos)] += 1

        freq_nums.update(ns)
        freq_ests.update(es)

        gaps = [ns[i + 1] - ns[i] for i in range(4)]
        gaps_medios.append(sum(gaps) / 4)
        amplitudes.append(ns[-1] - ns[0])

    gap_medio = sum(gaps_medios) / n
    amplitude_media = sum(amplitudes) / n

    return {
        'n_ecos': n,
        'soma_media': round(soma_media, 1),
        'desvio_soma': round(sum_deviation, 1),
        'faixa_soma_preferida': [
            int(soma_media - sum_deviation),
            int(soma_media + sum_deviation),
        ],
        'paridades_preferidas': [p for p, _ in parities.most_common(2)],
        'baixos_altos_preferidos': [ba for ba, _ in baixos_altos.most_common(2)],
        'numeros_mais_frequentes': [num for num, _ in freq_nums.most_common(10)],
        'numeros_menos_frequentes': [num for num, _ in reversed(freq_nums.most_common())][: 10],
        'estrelas_mais_frequentes': [est for est, _ in freq_ests.most_common(6)],
        'gap_medio': round(gap_medio, 1),
        'amplitude_media': round(amplitude_media, 1),
        'distribuicao_numerica': dict(sorted(freq_nums.items())),
        'distribuicao_estrelas': dict(sorted(freq_ests.items())),
    }


# Pontuação por nº de matches com os top-5 mais frequentes:
#   0→0, 1→5, 2→10, 3→20, 4→15, 5→10 (penaliza ser muito previsível)
_SCORE_AFINIDADE_NUMS = [0.0, 5.0, 10.0, 20.0, 15.0, 10.0]


def score_chave(nums, ests, profile):
    """
    Pontua (nums, ests) de 0 a 100 com base no perfil dos Ecos.

    Dimensões:
      Soma dentro da faixa preferida  → 20 pts
      Paridade predominante           → 15 pts
      Baixos/altos predominantes      → 15 pts
      Afinidade com nums frequentes   → 20 pts  (pico em 3 de 5)
      Afinidade com estrelas          → 15 pts
      Gap médio próximo do perfil     → 10 pts
      Amplitude próxima do perfil     →  5 pts
                                       --------
                                       100 pts
    Bónus: 1-2 números raramente vistos  +5 pts (cap final: 100)
    """
    score = 0.0
    soma = sum(nums)
    ns = sorted(nums)

    # --- Soma (20 pts) ---
    faixa = profile['faixa_soma_preferida']
    if faixa[0] <= soma <= faixa[1]:
        score += 20.0
    else:
        dist = min(abs(soma - faixa[0]), abs(soma - faixa[1]))
        score += max(0.0, 20.0 - dist * 0.5)

    # --- Paridade (15 pts) ---
    n_pares = sum(1 for x in nums if x % 2 == 0)
    key_pair = (n_pares, 5 - n_pares)
    pref = profile['paridades_preferidas']
    if pref and key_pair == pref[0]:
        score += 15.0
    elif len(pref) > 1 and key_pair == pref[1]:
        score += 10.0

    # --- Baixos/altos (15 pts) ---
    n_baixos = sum(1 for x in nums if x <= 25)
    ba_chave = (n_baixos, 5 - n_baixos)
    ba_pref = profile['baixos_altos_preferidos']
    if ba_pref and ba_chave == ba_pref[0]:
        score += 15.0
    elif len(ba_pref) > 1 and ba_chave == ba_pref[1]:
        score += 10.0

    # --- Afinidade com números frequentes (20 pts) ---
    top5 = set(profile['numeros_mais_frequentes'][:5])
    afinidade = len(set(nums) & top5)
    score += _SCORE_AFINIDADE_NUMS[afinidade]

    # --- Bónus: 1-2 números raramente vistos (5 pts) ---
    raros = set(profile['numeros_menos_frequentes'][:5])
    n_raros = len(set(nums) & raros)
    if 1 <= n_raros <= 2:
        score += 5.0

    # --- Afinidade com estrelas (15 pts) ---
    top3_ests = set(profile['estrelas_mais_frequentes'][:3])
    afinidade_ests = len(set(ests) & top3_ests)
    score += afinidade_ests * 7.5

    # --- Gap médio (10 pts) ---
    gaps = [ns[i + 1] - ns[i] for i in range(4)]
    gap_chave = sum(gaps) / 4
    diff_gap = abs(gap_chave - profile['gap_medio'])
    score += max(0.0, 10.0 - diff_gap * 0.8)

    # --- Amplitude (5 pts) ---
    span = ns[-1] - ns[0]
    diff_amp = abs(span - profile['amplitude_media'])
    score += max(0.0, 5.0 - diff_amp * 0.15)

    return min(100.0, round(score, 1))


def choose_by_profile(pos_alvo, seed, profile, historical_keys, n_candidates):
    """
    Avalia n_candidatos chaves inéditas após o marco e devolve a de maior score.
    Começa no espaço_médio após o marco; avança posição a posição.
    """
    salto = max(1, profile.get('gap_medio', 1))
    pos = int(pos_alvo + salto) % UNIVERSE

    melhor_score = -1.0
    best_key = None
    melhor_pos = None
    n_undrawn = 0
    n_total = 0

    while n_undrawn < n_candidates:
        nums, ests = key_at_position(pos, seed)
        n_total += 1

        key_t = (tuple(nums), tuple(ests))
        if key_t not in historical_keys:
            n_undrawn += 1
            s = score_chave(nums, ests, profile)
            if s > melhor_score:
                melhor_score = s
                best_key = [list(nums), list(ests)]
                melhor_pos = pos

        pos = (pos + 1) % UNIVERSE

    return {
        'chave': best_key,
        'posicao': melhor_pos,
        'score': melhor_score,
        'candidatos_avaliados': n_total,
        'ineditas_avaliadas': n_undrawn,
    }
