import random
from races.antigas import normalize


def kors_vermelho(ariadne):
    menos_freq = ariadne.least_frequent_numbers(20)
    if not menos_freq or len(menos_freq) < 5:
        return None

    pool = [x["numero"] for x in menos_freq]
    max_ap = max(x["aparicoes_totais"] for x in menos_freq) + 1
    weights = [max_ap - x["aparicoes_totais"] for x in menos_freq]

    escolhidos = set()
    tentativas = 0
    while len(escolhidos) < 5 and tentativas < 300:
        escolhidos.add(random.choices(pool, weights=weights, k=1)[0])
        tentativas += 1

    if len(escolhidos) < 5:
        restantes = [n for n in pool if n not in escolhidos]
        escolhidos.update(restantes[: 5 - len(escolhidos)])

    key = normalize(sorted(escolhidos), sorted(random.sample(range(1, 13), 2)))

    return {
        "nome": "Kael da Chama Fria",
        "classe": "Kor Vermelho",
        "tipo": "Kor Vermelho",
        "chave": key,
        "peso": 1.0,
        "doutrina": "O que raramente foi convocado guarda em si a tensão do esquecimento.",
        "numeros_menos_frequentes": menos_freq,
    }
