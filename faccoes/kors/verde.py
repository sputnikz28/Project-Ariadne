import random
from racas.antigas import normalizar


def kors_verde(ariadne):
    transicao = ariadne.padrao_transicao()
    if not transicao.get("ultima"):
        return None

    persistentes = transicao.get("persistentes", [])
    chegados = transicao.get("chegados", [])
    ests_chegadas = transicao.get("estrelas_chegadas", [])
    ests_persistentes = transicao.get("estrelas_persistentes", [])

    # Base: numbers that just arrived in the last draw
    candidatos = list(chegados)

    # Anchor with 1-2 persistent numbers
    if persistentes:
        candidatos.extend(random.sample(persistentes, min(2, len(persistentes))))

    # Add neighbours of arrived numbers to expand the pool
    for n in chegados:
        for adj in (n - 1, n + 1):
            if 1 <= adj <= 50 and adj not in candidatos:
                candidatos.append(adj)

    # Deduplicate (preserve order)
    vistos = set()
    candidatos_uniq = []
    for n in candidatos:
        if n not in vistos:
            vistos.add(n)
            candidatos_uniq.append(n)
    candidatos = candidatos_uniq

    # Fill to at least 5
    if len(candidatos) < 5:
        ultima_nums = set(transicao["ultima"]["numeros"])
        restante = [n for n in range(1, 51) if n not in vistos and n not in ultima_nums]
        random.shuffle(restante)
        candidatos.extend(restante[: 5 - len(candidatos)])

    nums = sorted(random.sample(candidatos, 5) if len(candidatos) >= 5 else candidatos[:5])

    # Stars: prefer newly arrived or persistent stars
    pool_ests = list(dict.fromkeys(ests_chegadas + ests_persistentes))
    if len(pool_ests) >= 2:
        estrelas = sorted(random.sample(pool_ests, 2))
    elif len(pool_ests) == 1:
        outras = [e for e in range(1, 13) if e not in pool_ests]
        estrelas = sorted(pool_ests + [random.choice(outras)])
    else:
        estrelas = sorted(random.sample(range(1, 13), 2))

    chave = normalizar(nums, estrelas)

    return {
        "nome": "Sylvara das Passagens",
        "classe": "Kor Verde",
        "tipo": "Kor Verde",
        "chave": chave,
        "peso": 1.0,
        "doutrina": "A passagem entre dois momentos revela o ritmo do universo.",
        "transicao": {
            "penultima": transicao["penultima"]["id"],
            "ultima": transicao["ultima"]["id"],
            "persistentes": persistentes,
            "chegados": chegados,
            "saidos": transicao.get("saidos", []),
            "delta_soma": transicao.get("delta_soma"),
        },
    }
