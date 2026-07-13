
import random
from dataclasses import dataclass, field, asdict


def normalize(nums, ests):
    nums = list(dict.fromkeys(n for n in nums if 1 <= n <= 50))
    ests = list(dict.fromkeys(e for e in ests if 1 <= e <= 12))
    while len(nums) < 5:
        n = random.randint(1, 50)
        if n not in nums:
            nums.append(n)
    while len(ests) < 2:
        e = random.randint(1, 12)
        if e not in ests:
            ests.append(e)
    return sorted(nums[:5]), sorted(ests[:2])


def aplicar_conhecimento(key, hidden_numbers, hidden_stars):
    nums = list(key[0])
    ests = list(key[1])
    if hidden_numbers and random.random() < 0.55:
        nums[random.randrange(5)] = random.choice(hidden_numbers)
    if hidden_stars and random.random() < 0.45:
        ests[random.randrange(2)] = random.choice(hidden_stars)
    return normalize(nums, ests)


def gaps(nums):
    s = sorted(nums)
    return [s[i + 1] - s[i] for i in range(4)]


@dataclass
class Heroi:
    id: str
    name: str
    raca: str
    casa: str
    generation: int
    pais: list = field(default_factory=list)
    genoma: dict = field(default_factory=dict)
    pontos: int = 0
    titulo: str = "Sem título"
    keys: list = field(default_factory=list)
    amuletos: list = field(default_factory=list)
    estado: str = "VIVO"
    treinos: int = 0

    def to_dict(self):
        return asdict(self)


NAMES = ["Lyra", "Morgana", "Kael", "Gruk", "Aruk", "Elarion", "Selene", "Thara", "Aion", "Velka"]
TITULOS = ["da Névoa", "dos Ossos", "da Lua Fria", "Pedra-Partida", "dos Astros", "do Bosque"]
RACAS = ["Bruxa", "Vidente", "Chefe Tribal", "Elfo", "Goblin", "Shaman", "Cronomante", "Esqueleto"]
CASAS = ["Casa Lunar", "Casa dos Ossos", "Casa do Caos", "Casa das Estrelas", "Casa Tribal", "Casa do Bosque"]


def create(i, g=1, pais=None):
    return Heroi(
        id=f"H-{i:05d}",
        name=f"{random.choice(NAMES)} {random.choice(TITULOS)}",
        raca=random.choice(RACAS),
        casa=random.choice(CASAS),
        generation=g,
        pais=pais or [],
        genoma={
            "clareza": random.random(),
            "confusao": random.random(),
            "caos": random.random(),
            "memoria": random.randint(1, 8),
        },
    )


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
        from races.skeletons import generate as gerar_esqueleto
        key, _ritual = gerar_esqueleto(h, ctx, 25, 6)
        return aplicar_conhecimento(key, hidden_numbers, hidden_stars)

    if raca == "Cronomante":
        from races.chronomancers import generate_temporal_key
        key = generate_temporal_key(
            h.name,
            ctx.get("extracao", {}),
            world,
            int(h.id.split("-")[-1]) % 7,
        )["chave"]
        return aplicar_conhecimento(key, hidden_numbers, hidden_stars)

    if raca == "Bruxa":
        key = normalize(
            random.sample(est["quentes"], 2)
            + random.sample(est["frios"], 2)
            + [random.randint(1, 50)],
            [
                random.choice(est["estrelas_quentes"]),
                random.choice(est["estrelas_frias"]),
            ],
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
        key = normalize(nums, random.sample(est["estrelas_quentes"], 2))
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
        key = normalize(nums, random.sample(range(1, 13), 2))
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
                key = normalize(nums, random.sample(est["estrelas_quentes"], 2))
                return aplicar_conhecimento(key, hidden_numbers, hidden_stars)

    if raca == "Goblin":
        nums = (
            random.sample(range(35, 51), 3)
            if world["jackpot"] >= 100_000_000
            else []
        ) + random.sample(range(1, 51), 5)
        key = normalize(nums, random.sample(range(1, 13), 2))
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
    key = normalize(nums, ests)
    return aplicar_conhecimento(key, hidden_numbers, hidden_stars)
