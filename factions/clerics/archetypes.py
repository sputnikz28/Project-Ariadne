import random
from core.services.combinations import normalize_candidate, gaps


def aplicar_conhecimento(key, hidden_numbers, hidden_stars):
    nums = list(key[0])
    ests = list(key[1])
    if hidden_numbers and random.random() < 0.55:
        nums[random.randrange(5)] = random.choice(hidden_numbers)
    if hidden_stars and random.random() < 0.45:
        ests[random.randrange(2)] = random.choice(hidden_stars)
    return normalize_candidate(nums, ests, random)


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


def generate(h, ctx):
    est = ctx["estatisticas"]
    hist = ctx["historico"]
    world = ctx["mundo"]
    hidden_numbers, hidden_stars = _segredos(h)

    raca = h.raca.replace("Renascido ", "")

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
