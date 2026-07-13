import random


def _completar(tripla):
    nums = list(tripla)
    while len(nums) < 5:
        n = random.randint(1, 50)
        if n not in nums:
            nums.append(n)
    return sorted(nums), sorted(random.sample(range(1, 13), 2))


def vampires(ariadne, seed=None, cfg=None):
    """Vampires of Elarion — V8 Ariadne integration.

    Linhagem Sanguínea: frequent triples from historical data.
    Linhagem Sombria: consecutive triples (harmonic patterns).
    Returns list of candidate dicts for main.py.
    """
    top = ariadne.triples(limite=20)
    all_triples = [t["numeros"] for t in top if "numeros" in t]

    escolha_s = random.choice(all_triples) if all_triples else random.sample(range(1, 51), 3)

    consecutive = [t for t in all_triples if len(t) >= 2 and max(t) - min(t) <= len(t)]
    escolha_n = random.choice(consecutive) if consecutive else (
        random.choice(all_triples) if all_triples else [16, 17, 18]
    )

    peso = cfg.getfloat("VAMPIROS", "peso_conselho", fallback=0.90) if cfg else 0.90

    return [
        {
            "nome": "Conde Vaelor da Linhagem Sanguínea",
            "tipo": "Vampiro Sanguíneo",
            "classe": "Vampiro",
            "linhagem": "Sanguínea",
            "doutrina": "Triplas frequentes inseridas numa chave equilibrada.",
            "tripla": escolha_s,
            "chave": _completar(escolha_s),
            "peso": peso,
        },
        {
            "nome": "Lady Nyx da Linhagem Sombria",
            "tipo": "Vampiro Sombrio",
            "classe": "Vampiro",
            "linhagem": "Sombria",
            "doutrina": "Triplas consecutivas, harmónicas e repetitivas.",
            "tripla": escolha_n,
            "chave": _completar(escolha_n),
            "peso": peso,
        },
    ]
