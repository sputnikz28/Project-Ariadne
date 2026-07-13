import random
from races.antigas import normalizar


def kors_branco(ariadne):
    atrasados = ariadne.numeros_atrasados(15)
    if not atrasados or len(atrasados) < 5:
        return None

    pool = [x["numero"] for x in atrasados]
    pesos = [x["atraso"] + 1 for x in atrasados]

    escolhidos = set()
    tentativas = 0
    while len(escolhidos) < 5 and tentativas < 300:
        escolhidos.add(random.choices(pool, weights=pesos, k=1)[0])
        tentativas += 1

    if len(escolhidos) < 5:
        restantes = [n for n in pool if n not in escolhidos]
        escolhidos.update(restantes[: 5 - len(escolhidos)])

    chave = normalizar(sorted(escolhidos), sorted(random.sample(range(1, 13), 2)))

    return {
        "nome": "Aelyra dos Silêncios",
        "classe": "Kor Branco",
        "tipo": "Kor Branco",
        "chave": chave,
        "peso": 1.0,
        "doutrina": "Os números que dormem há mais tempo serão os primeiros a despertar.",
        "numeros_atrasados": atrasados,
    }
