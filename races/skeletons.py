
import random
from races.legacy import normalize


def generate(heroi, contexto, numbers_width=25, stars_width=6):
    numbers_width = max(5, min(50, int(numbers_width)))
    stars_width = max(2, min(12, int(stars_width)))

    inicio_n = random.randint(1, 50 - numbers_width + 1)
    fim_n = inicio_n + numbers_width - 1
    numbers = random.sample(range(inicio_n, fim_n + 1), 5)

    inicio_e = random.randint(1, 12 - stars_width + 1)
    fim_e = inicio_e + stars_width - 1
    stars = random.sample(range(inicio_e, fim_e + 1), 2)

    ritual = {
        "inicio_numeros": inicio_n,
        "fim_numeros": fim_n,
        "largura_numeros": numbers_width,
        "inicio_estrelas": inicio_e,
        "fim_estrelas": fim_e,
        "largura_estrelas": stars_width,
    }
    if hasattr(heroi, "genoma"):
        heroi.genoma["ultimo_ritual_osseo"] = ritual

    return normalize(numbers, stars), ritual


def create_representatives(config, contexto):
    if not config.getboolean("ESQUELETOS", "ativos", fallback=True):
        return []

    quantidade = config.getint("ESQUELETOS", "quantidade_externa", fallback=4)
    largura_n = config.getint("ESQUELETOS", "largura_numeros", fallback=25)
    largura_e = config.getint("ESQUELETOS", "largura_estrelas", fallback=6)
    names = [
        "Ossário da Cripta",
        "Tíbia do Intervalo",
        "Crânio das Vinte e Cinco Pedras",
        "Marfim das Seis Estrelas",
        "Fémur do Corredor Móvel",
    ]

    saida = []
    for i in range(quantidade):
        key, ritual = generate(None, contexto, largura_n, largura_e)
        saida.append({
            "nome": names[i % len(names)],
            "tipo": "Esqueleto das Catacumbas",
            "chave": key,
            "ritual": ritual,
        })
    return saida
