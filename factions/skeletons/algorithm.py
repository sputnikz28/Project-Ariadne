from core.services.combinations import normalize_candidate


def generate(hero, ctx, numbers_width=25, stars_width=6):
    rng = ctx['rng']
    numbers_width = max(5, min(50, int(numbers_width)))
    stars_width = max(2, min(12, int(stars_width)))

    start_n = rng.randint(1, 50 - numbers_width + 1)
    end_n = start_n + numbers_width - 1
    numbers = rng.sample(range(start_n, end_n + 1), 5)

    start_e = rng.randint(1, 12 - stars_width + 1)
    end_e = start_e + stars_width - 1
    stars = rng.sample(range(start_e, end_e + 1), 2)

    ritual = {
        "inicio_numeros": start_n,
        "fim_numeros": end_n,
        "largura_numeros": numbers_width,
        "inicio_estrelas": start_e,
        "fim_estrelas": end_e,
        "largura_estrelas": stars_width,
    }
    if hasattr(hero, "genoma"):
        hero.genoma["ultimo_ritual_osseo"] = ritual

    return normalize_candidate(numbers, stars, rng), ritual


def create_representatives(config, ctx):
    if not config.getboolean("ESQUELETOS", "ativos", fallback=True):
        return []

    quantity = config.getint("ESQUELETOS", "quantidade_externa", fallback=4)
    numbers_width = config.getint("ESQUELETOS", "largura_numeros", fallback=25)
    stars_width = config.getint("ESQUELETOS", "largura_estrelas", fallback=6)
    names = [
        "Ossário da Cripta",
        "Tíbia do Intervalo",
        "Crânio das Vinte e Cinco Pedras",
        "Marfim das Seis Estrelas",
        "Fémur do Corredor Móvel",
    ]

    output = []
    for i in range(quantity):
        key, ritual = generate(None, ctx, numbers_width, stars_width)
        output.append({
            "nome": names[i % len(names)],
            "tipo": "Esqueleto das Catacumbas",
            "chave": key,
            "ritual": ritual,
        })
    return output
