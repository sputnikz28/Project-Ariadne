import random
from races.legacy import normalize


def kors_branco(ariadne):
    atrasados = ariadne.overdue_numbers(15)
    if not atrasados or len(atrasados) < 5:
        return None

    pool = [x["numero"] for x in atrasados]
    weights = [x["atraso"] + 1 for x in atrasados]

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
        "nome": "Aelyra dos Silêncios",
        "classe": "Kor Branco",
        "tipo": "Kor Branco",
        "chave": key,
        "peso": 1.0,
        "doutrina": "Os números que dormem há mais tempo serão os primeiros a despertar.",
        "numeros_atrasados": atrasados,
    }
