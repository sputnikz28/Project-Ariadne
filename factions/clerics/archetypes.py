import random
from core.services.combinations import normalize_candidate, gaps
from core.services.fitness import fitness


def aplicar_conhecimento(key, hidden_numbers, hidden_stars):
    nums = list(key[0])
    ests = list(key[1])
    if hidden_numbers and random.random() < 0.55:
        nums[random.randrange(5)] = random.choice(hidden_numbers)
    if hidden_stars and random.random() < 0.45:
        ests[random.randrange(2)] = random.choice(hidden_stars)
    return normalize_candidate(nums, ests, random)


_ZOMBIE_DEFAULTS = {
    "tamanho_pool_numeros": 12,
    "tamanho_pool_estrelas": 5,
    "n_simulacoes": 300,
}


def _zombie_config(cfg):
    if cfg is None:
        return dict(_ZOMBIE_DEFAULTS)
    return {
        "tamanho_pool_numeros": cfg.getint(
            "ZOMBIES", "tamanho_pool_numeros", fallback=_ZOMBIE_DEFAULTS["tamanho_pool_numeros"]
        ),
        "tamanho_pool_estrelas": cfg.getint(
            "ZOMBIES", "tamanho_pool_estrelas", fallback=_ZOMBIE_DEFAULTS["tamanho_pool_estrelas"]
        ),
        "n_simulacoes": cfg.getint(
            "ZOMBIES", "n_simulacoes", fallback=_ZOMBIE_DEFAULTS["n_simulacoes"]
        ),
    }


def _nascer_territorio_zombie(rng, tamanho_pool_numeros, tamanho_pool_estrelas):
    return {
        "pool_numeros": sorted(rng.sample(range(1, 51), tamanho_pool_numeros)),
        "pool_estrelas": sorted(rng.sample(range(1, 13), tamanho_pool_estrelas)),
    }


def mutar_territorio_zombie(territorio, rng, taxa_mutacao):
    """Minimal drift mutation for reproduction (called from
    algorithm.py's breeding loop, never from generate() itself): each
    pool element independently has `taxa_mutacao` probability of being
    replaced by a value not currently in that pool. Size, uniqueness
    and the 1-50/1-12 bounds are always preserved — the territory is
    never rebuilt from scratch, only nudged.
    """
    pool_numeros = list(territorio["pool_numeros"])
    for i in range(len(pool_numeros)):
        if rng.random() < taxa_mutacao:
            candidatos = [n for n in range(1, 51) if n not in pool_numeros]
            if candidatos:
                pool_numeros[i] = rng.choice(candidatos)

    pool_estrelas = list(territorio["pool_estrelas"])
    for i in range(len(pool_estrelas)):
        if rng.random() < taxa_mutacao:
            candidatos = [e for e in range(1, 13) if e not in pool_estrelas]
            if candidatos:
                pool_estrelas[i] = rng.choice(candidatos)

    return {"pool_numeros": sorted(pool_numeros), "pool_estrelas": sorted(pool_estrelas)}


def _explorar_territorio_zombie(territorio, est, rng, n_simulacoes):
    """Monte Carlo exploration strictly within the territory's pools —
    same objective function (core.services.fitness.fitness) already
    used by factions/werewolves/algorithm.py, no new metric introduced.
    Returns the exact argmax over the n_simulacoes sampled candidates —
    ties keep the first candidate found, deterministic given rng.
    """
    melhor_chave = None
    melhor_fitness = None
    for _ in range(n_simulacoes):
        nums = sorted(rng.sample(territorio["pool_numeros"], 5))
        ests = sorted(rng.sample(territorio["pool_estrelas"], 2))
        f = fitness((nums, ests), est)
        if melhor_fitness is None or f > melhor_fitness:
            melhor_fitness = f
            melhor_chave = (nums, ests)
    return melhor_chave


def _segredos(heroi):
    numbers = []
    stars = []
    for segredo in heroi.genoma.get("conhecimento_oculto", []):
        numbers.extend(segredo.get("numeros", []))
        stars.extend(segredo.get("estrelas", []))
        for par in segredo.get("pares", []):
            numbers.extend(par)
        for trio in segredo.get("trios", []):
            numbers.extend(trio)
    return list(dict.fromkeys(numbers)), list(dict.fromkeys(stars))


def generate(h, ctx, cfg=None):
    est = ctx["estatisticas"]
    hist = ctx["historico"]
    world = ctx["mundo"]
    hidden_numbers, hidden_stars = _segredos(h)

    raca = h.raca.replace("Renascido ", "")

    if raca == "Minotauro":
        if h.keys:
            ultima = h.keys[-1]
            return list(ultima["numeros"]), list(ultima["estrelas"])
        herdada = h.genoma.get("chave_herdada")
        if herdada is not None:
            return list(herdada[0]), list(herdada[1])
        nums = sorted(random.sample(range(1, 51), 5))
        ests = sorted(random.sample(range(1, 13), 2))
        return normalize_candidate(nums, ests, random)

    if raca == "Zombie":
        zcfg = _zombie_config(cfg)
        territorio = h.genoma.get("territorio_zombie")
        if territorio is None:
            territorio = _nascer_territorio_zombie(
                random, zcfg["tamanho_pool_numeros"], zcfg["tamanho_pool_estrelas"],
            )
            h.genoma["territorio_zombie"] = territorio
        nums, ests = _explorar_territorio_zombie(territorio, est, random, zcfg["n_simulacoes"])
        return nums, ests

    if raca == "Esqueleto":
        from factions.skeletons.algorithm import generate as gerar_esqueleto
        key, _ritual = gerar_esqueleto(h, ctx, 25, 6)
        return aplicar_conhecimento(key, hidden_numbers, hidden_stars)

    if raca == "Cronomante":
        from factions.chronomancers.algorithm import generate_temporal_key
        key = generate_temporal_key(
            h.name,
            ctx.get("extracao", {}),
            world,
            ctx["rng"],
            int(h.id.split("-")[-1]) % 7,
        )["chave"]
        return aplicar_conhecimento(key, hidden_numbers, hidden_stars)

    if raca == "Bruxa":
        key = normalize_candidate(
            random.sample(est["quentes"], 2)
            + random.sample(est["frios"], 2)
            + [random.randint(1, 50)],
            [
                random.choice(est["estrelas_quentes"]),
                random.choice(est["estrelas_frias"]),
            ],
            random,
        )
        return aplicar_conhecimento(key, hidden_numbers, hidden_stars)

    if raca == "Vidente":
        nums = random.sample(est["quentes"], 2)
        if random.random() < 0.08 + h.genoma["clareza"] * 0.25:
            for n in random.sample(hist[0]["numeros"], random.randint(1, 2)):
                nums.append(
                    n
                    if random.random() > h.genoma["confusao"]
                    else max(1, min(50, n + random.choice([-2, -1, 1, 2])))
                )
        key = normalize_candidate(nums, random.sample(est["estrelas_quentes"], 2), random)
        return aplicar_conhecimento(key, hidden_numbers, hidden_stars)

    if raca == "Chefe Tribal":
        simbolos = {
            "sol": 7,
            "lua": 14,
            "lobo": 29,
            "fogo": 10,
            "agua": -5,
            "montanha": 22,
            "corvo": 33,
        }
        atual = random.randint(1, 12)
        nums = []
        ossos = random.choices(list(simbolos), k=5)
        h.genoma["ossos"] = ossos
        for simbolo in ossos:
            atual = max(1, min(50, atual + simbolos[simbolo]))
            nums.append(atual)
        key = normalize_candidate(nums, random.sample(range(1, 13), 2), random)
        return aplicar_conhecimento(key, hidden_numbers, hidden_stars)

    if raca == "Elfo":
        for _ in range(1000):
            nums = sorted(random.sample(range(1, 51), 5))
            pares = sum(n % 2 == 0 for n in nums)
            baixos = sum(n <= 25 for n in nums)
            if (
                100 <= sum(nums) <= 170
                and pares in (2, 3)
                and baixos in (2, 3)
                and max(gaps(nums)) <= 20
            ):
                key = normalize_candidate(nums, random.sample(est["estrelas_quentes"], 2), random)
                return aplicar_conhecimento(key, hidden_numbers, hidden_stars)

    if raca == "Goblin":
        nums = (
            random.sample(range(35, 51), 3)
            if world["jackpot"] >= 100_000_000
            else []
        ) + random.sample(range(1, 51), 5)
        key = normalize_candidate(nums, random.sample(range(1, 13), 2), random)
        return aplicar_conhecimento(key, hidden_numbers, hidden_stars)

    displacement = {
        "nova": 2,
        "crescente": 1,
        "quarto crescente": 2,
        "gibosa crescente": 3,
        "cheia": 0,
        "gibosa minguante": -1,
        "quarto minguante": -2,
        "minguante": -3,
    }.get(world["fase_lua"], 0)

    nums = [
        max(1, min(50, n + displacement))
        for n in hist[-1]["numeros"]
    ]
    ests = [
        max(1, min(12, e + (1 if displacement > 0 else -1)))
        for e in hist[-1]["estrelas"]
    ]
    key = normalize_candidate(nums, ests, random)
    return aplicar_conhecimento(key, hidden_numbers, hidden_stars)
