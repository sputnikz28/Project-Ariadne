
import math
import random
from collections import Counter


def desvio_padrao(nums):
    media = sum(nums) / len(nums)
    return math.sqrt(sum((n - media) ** 2 for n in nums) / len(nums))


def gaps(nums):
    nums = sorted(nums)
    return [nums[i + 1] - nums[i] for i in range(len(nums) - 1)]


def penalizacao_popularidade(nums):
    datas = sum(n <= 31 for n in nums)
    sequencia = sum(1 for a, b in zip(nums, nums[1:]) if b - a == 1)
    redondos = sum(n % 5 == 0 for n in nums)
    padrao_visual = 1 if len(set(gaps(nums))) == 1 else 0
    return datas * 3 + sequencia * 5 + redondos + padrao_visual * 4


def pontuar_chave(chave, estat, grimorio, config):
    nums, ests = chave
    desvio = desvio_padrao(nums)
    gs = gaps(nums)
    popularidade = penalizacao_popularidade(nums)
    distribuicao = len({(n - 1) // 10 for n in nums}) / 5
    gap_score = min(1.0, len(set(gs)) / 4)
    freq = sum(estat["freq_norm"].get(n, 0) for n in nums) / 5

    if not grimorio.get("conhecimento", {}).get("frequencias"):
        freq *= 0.25

    score = (
        config.getfloat("ESTRATEGIA_NEGRA", "peso_desvio_padrao", fallback=0.25)
        * min(1.0, desvio / 16)
        + config.getfloat("ESTRATEGIA_NEGRA", "peso_anti_popularidade", fallback=0.25)
        * max(0.0, 1 - popularidade / 25)
        + config.getfloat("ESTRATEGIA_NEGRA", "peso_distribuicao", fallback=0.20)
        * distribuicao
        + config.getfloat("ESTRATEGIA_NEGRA", "peso_gaps", fallback=0.15)
        * gap_score
        + config.getfloat("ESTRATEGIA_NEGRA", "peso_frequencia_roubada", fallback=0.15)
        * freq
    )
    return round(score * 100, 4)


def gerar_chave_promissora(estat, grimorio, config):
    total = config.getint("ESTRATEGIA_NEGRA", "candidatas_geradas", fallback=3000)
    minimo_desvio = config.getfloat("ESTRATEGIA_NEGRA", "desvio_minimo", fallback=10.0)
    max_datas = config.getint("ESTRATEGIA_NEGRA", "max_numeros_ate_31", fallback=3)

    melhores = []
    for _ in range(total):
        nums = sorted(random.sample(range(1, 51), 5))
        ests = sorted(random.sample(range(1, 13), 2))
        if sum(n <= 31 for n in nums) > max_datas:
            continue
        if desvio_padrao(nums) < minimo_desvio:
            continue
        score = pontuar_chave((nums, ests), estat, grimorio, config)
        melhores.append((score, nums, ests))

    if not melhores:
        nums = sorted(random.sample(range(1, 51), 5))
        ests = sorted(random.sample(range(1, 13), 2))
        return (nums, ests), pontuar_chave((nums, ests), estat, grimorio, config)

    score, nums, ests = max(melhores, key=lambda x: x[0])
    return (nums, ests), score


def diversificar(chaves, quantidade):
    escolhidas = []
    restantes = list(chaves)
    if not restantes:
        return escolhidas
    escolhidas.append(max(restantes, key=lambda x: x.get("score", 0)))
    restantes.remove(escolhidas[0])

    while restantes and len(escolhidas) < quantidade:
        def distancia(candidato):
            conjunto = set(candidato["chave"][0])
            return min(len(conjunto ^ set(e["chave"][0])) for e in escolhidas)
        proximo = max(restantes, key=lambda x: (distancia(x), x.get("score", 0)))
        escolhidas.append(proximo)
        restantes.remove(proximo)
    return escolhidas
