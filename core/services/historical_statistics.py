"""Derived key statistics and within-dataset history for one historical
draw — the `estatisticas_chave` and `historico_no_conjunto` blocks.

Verified with 0 mismatches against the full 001-058 historical corpus:
number classifications (primes, Fibonacci, squares, triangular numbers),
`sequencias_consecutivas` as adjacent pairs (not runs), and
`historico_no_conjunto`'s atraso/frequencia_acumulada semantics (atraso =
distance to the prior occurrence within this dataset, `None` on first
occurrence; frequencia_acumulada = count from the first sorteio through
this one, inclusive). Pure: no I/O.
"""

from __future__ import annotations

import math

_PRIMES = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47}
_FIBONACCI = {1, 2, 3, 5, 8, 13, 21, 34}
_SQUARES = {1, 4, 9, 16, 25, 36, 49}
_TRIANGULARES = {1, 3, 6, 10, 15, 21, 28, 36, 45}


def _decade_bucket(n: int) -> str:
    if n <= 10:
        return "01-10"
    if n <= 20:
        return "11-20"
    if n <= 30:
        return "21-30"
    if n <= 40:
        return "31-40"
    return "41-50"


def _col_mod5(n: int) -> str:
    m = n % 5
    return str(m if m != 0 else 5)


def build_estatisticas_chave(
    numeros: list[int],
    estrelas: list[int],
    prev_numeros: list[int],
    prev_estrelas: list[int],
) -> dict[str, object]:
    numeros_sorted = sorted(numeros)
    estrelas_sorted = sorted(estrelas)
    n = len(numeros_sorted)
    soma = sum(numeros_sorted)
    produto = 1
    for x in numeros_sorted:
        produto *= x
    media = soma / n
    mediana = numeros_sorted[n // 2] if n % 2 == 1 else (numeros_sorted[n // 2 - 1] + numeros_sorted[n // 2]) / 2
    variancia_pop = sum((x - media) ** 2 for x in numeros_sorted) / n
    desvio_pop = math.sqrt(variancia_pop)

    distrib_dezenas = {"01-10": 0, "11-20": 0, "21-30": 0, "31-40": 0, "41-50": 0}
    for x in numeros_sorted:
        distrib_dezenas[_decade_bucket(x)] += 1

    distrib_col = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
    for x in numeros_sorted:
        distrib_col[_col_mod5(x)] += 1

    gaps = [numeros_sorted[i + 1] - numeros_sorted[i] for i in range(n - 1)]

    seqs = []
    for i in range(n - 1):
        if numeros_sorted[i + 1] == numeros_sorted[i] + 1:
            seqs.append([numeros_sorted[i], numeros_sorted[i + 1]])

    soma_e = sum(estrelas_sorted)

    return {
        "soma_numeros": soma,
        "produto_numeros": produto,
        "media_numeros": media,
        "mediana_numeros": mediana,
        "desvio_padrao_populacional": round(desvio_pop, 3),
        "variancia_populacional": round(variancia_pop, 1),
        "minimo": min(numeros_sorted),
        "maximo": max(numeros_sorted),
        "amplitude": max(numeros_sorted) - min(numeros_sorted),
        "pares": [x for x in numeros_sorted if x % 2 == 0],
        "impares": [x for x in numeros_sorted if x % 2 == 1],
        "quantidade_pares": sum(1 for x in numeros_sorted if x % 2 == 0),
        "quantidade_impares": sum(1 for x in numeros_sorted if x % 2 == 1),
        "baixos_1_25": [x for x in numeros_sorted if x <= 25],
        "altos_26_50": [x for x in numeros_sorted if x > 25],
        "primos": [x for x in numeros_sorted if x in _PRIMES],
        "fibonacci": [x for x in numeros_sorted if x in _FIBONACCI],
        "quadrados_perfeitos": [x for x in numeros_sorted if x in _SQUARES],
        "triangulares": [x for x in numeros_sorted if x in _TRIANGULARES],
        "multiplos_de_3": [x for x in numeros_sorted if x % 3 == 0],
        "multiplos_de_5": [x for x in numeros_sorted if x % 5 == 0],
        "distribuicao_por_dezenas": distrib_dezenas,
        "distribuicao_por_colunas_mod_5": distrib_col,
        "intervalos_ordenados": gaps,
        "media_intervalos": round(sum(gaps) / len(gaps), 2),
        "maior_intervalo": max(gaps),
        "menor_intervalo": min(gaps),
        "sequencias_consecutivas": seqs,
        "repetidos_sorteio_anterior": sorted(set(numeros_sorted) & set(prev_numeros)),
        "estrelas_repetidas_sorteio_anterior": sorted(set(estrelas_sorted) & set(prev_estrelas)),
        "soma_estrelas": soma_e,
        "media_estrelas": soma_e / len(estrelas_sorted),
        "amplitude_estrelas": max(estrelas_sorted) - min(estrelas_sorted),
        "estrelas_pares": [x for x in estrelas_sorted if x % 2 == 0],
        "estrelas_impares": [x for x in estrelas_sorted if x % 2 == 1],
        "vetor_binario_numeros_1_50": [1 if (i + 1) in numeros_sorted else 0 for i in range(50)],
        "vetor_binario_estrelas_1_12": [1 if (i + 1) in estrelas_sorted else 0 for i in range(12)],
    }


def build_historico_no_conjunto(all_sorteios: list[dict], idx: int) -> dict[str, object]:
    """`idx` must already point at the draw's own position in
    `all_sorteios` (i.e. the draw has already been appended) — atraso and
    frequencia_acumulada are computed relative to everything up to and
    including that position.
    """
    draw = all_sorteios[idx]
    numeros = draw["chave"]["numeros"]
    estrelas = draw["chave"]["estrelas"]

    atraso_n, freq_n = {}, {}
    for n in numeros:
        occ = [i for i in range(idx + 1) if n in all_sorteios[i]["chave"]["numeros"]]
        prior = [i for i in occ if i < idx]
        atraso_n[str(n)] = (idx - prior[-1]) if prior else None
        freq_n[str(n)] = len(occ)

    atraso_e, freq_e = {}, {}
    for e in estrelas:
        occ = [i for i in range(idx + 1) if e in all_sorteios[i]["chave"]["estrelas"]]
        prior = [i for i in occ if i < idx]
        atraso_e[str(e)] = (idx - prior[-1]) if prior else None
        freq_e[str(e)] = len(occ)

    return {
        "indice_no_conjunto": idx,
        "atraso_numeros_em_sorteios": atraso_n,
        "atraso_estrelas_em_sorteios": atraso_e,
        "frequencia_acumulada_numeros_ate_este_sorteio": freq_n,
        "frequencia_acumulada_estrelas_ate_este_sorteio": freq_e,
    }
