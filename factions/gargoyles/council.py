import random


def _completar(dupla):
    nums = list(dupla)
    while len(nums) < 5:
        n = random.randint(1, 50)
        if n not in nums:
            nums.append(n)
    return sorted(nums), sorted(random.sample(range(1, 13), 2))


def gargoyles(ariadne, seed=None, cfg=None):
    """Gargoyles of the Stone — V8 Ariadne integration.

    Linhagem de Pedra: historically consistent pairs.
    Linhagem do Espelho: consecutive pairs (symmetric relations).
    Returns list of candidate dicts for main.py.
    """
    top = ariadne.pairs(limite=30)
    all_pairs = [p["numeros"] for p in top if "numeros" in p]

    dupla_p = random.choice(all_pairs) if all_pairs else random.sample(range(1, 51), 2)

    consecutive = [p for p in all_pairs if len(p) == 2 and abs(p[1] - p[0]) == 1]
    dupla_e = random.choice(consecutive) if consecutive else (
        random.choice(all_pairs) if all_pairs else [16, 17]
    )

    peso = cfg.getfloat("GARGULAS", "peso_conselho", fallback=0.85) if cfg else 0.85

    return [
        {
            "nome": "Gorath da Linhagem de Pedra",
            "tipo": "Gárgula de Pedra",
            "classe": "Gárgula",
            "linhagem": "Pedra",
            "doutrina": "Duplas historicamente consistentes.",
            "dupla": dupla_p,
            "chave": _completar(dupla_p),
            "peso": peso,
        },
        {
            "nome": "Seraphine da Linhagem do Espelho",
            "tipo": "Gárgula do Espelho",
            "classe": "Gárgula",
            "linhagem": "Espelho",
            "doutrina": "Duplas consecutivas e relações simétricas.",
            "dupla": dupla_e,
            "chave": _completar(dupla_e),
            "peso": peso,
        },
    ]
