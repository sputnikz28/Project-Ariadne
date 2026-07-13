import random
from races.legacy import normalize


def kors_verde(ariadne):
    transition = ariadne.transition_pattern()
    if not transition.get("ultima"):
        return None

    persistentes = transition.get("persistentes", [])
    chegados = transition.get("chegados", [])
    ests_chegadas = transition.get("estrelas_chegadas", [])
    ests_persistentes = transition.get("estrelas_persistentes", [])

    # Base: numbers that just arrived in the last draw
    candidates = list(chegados)

    # Anchor with 1-2 persistent numbers
    if persistentes:
        candidates.extend(random.sample(persistentes, min(2, len(persistentes))))

    # Add neighbours of arrived numbers to expand the pool
    for n in chegados:
        for adj in (n - 1, n + 1):
            if 1 <= adj <= 50 and adj not in candidates:
                candidates.append(adj)

    # Deduplicate (preserve order)
    vistos = set()
    unique_candidates = []
    for n in candidates:
        if n not in vistos:
            vistos.add(n)
            unique_candidates.append(n)
    candidates = unique_candidates

    # Fill to at least 5
    if len(candidates) < 5:
        ultima_nums = set(transition["ultima"]["numeros"])
        restante = [n for n in range(1, 51) if n not in vistos and n not in ultima_nums]
        random.shuffle(restante)
        candidates.extend(restante[: 5 - len(candidates)])

    nums = sorted(random.sample(candidates, 5) if len(candidates) >= 5 else candidates[:5])

    # Stars: prefer newly arrived or persistent stars
    pool_ests = list(dict.fromkeys(ests_chegadas + ests_persistentes))
    if len(pool_ests) >= 2:
        stars = sorted(random.sample(pool_ests, 2))
    elif len(pool_ests) == 1:
        outras = [e for e in range(1, 13) if e not in pool_ests]
        stars = sorted(pool_ests + [random.choice(outras)])
    else:
        stars = sorted(random.sample(range(1, 13), 2))

    key = normalize(nums, stars)

    return {
        "nome": "Sylvara das Passagens",
        "classe": "Kor Verde",
        "tipo": "Kor Verde",
        "chave": key,
        "peso": 1.0,
        "doutrina": "A passagem entre dois momentos revela o ritmo do universo.",
        "transicao": {
            "penultima": transition["penultima"]["id"],
            "ultima": transition["ultima"]["id"],
            "persistentes": persistentes,
            "chegados": chegados,
            "saidos": transition.get("saidos", []),
            "delta_soma": transition.get("delta_soma"),
        },
    }
