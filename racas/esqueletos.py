
import random
from racas.antigas import normalizar


def gerar(heroi, contexto, largura_numeros=25, largura_estrelas=6):
    largura_numeros = max(5, min(50, int(largura_numeros)))
    largura_estrelas = max(2, min(12, int(largura_estrelas)))

    inicio_n = random.randint(1, 50 - largura_numeros + 1)
    fim_n = inicio_n + largura_numeros - 1
    numeros = random.sample(range(inicio_n, fim_n + 1), 5)

    inicio_e = random.randint(1, 12 - largura_estrelas + 1)
    fim_e = inicio_e + largura_estrelas - 1
    estrelas = random.sample(range(inicio_e, fim_e + 1), 2)

    ritual = {
        "inicio_numeros": inicio_n,
        "fim_numeros": fim_n,
        "largura_numeros": largura_numeros,
        "inicio_estrelas": inicio_e,
        "fim_estrelas": fim_e,
        "largura_estrelas": largura_estrelas,
    }
    if hasattr(heroi, "genoma"):
        heroi.genoma["ultimo_ritual_osseo"] = ritual

    return normalizar(numeros, estrelas), ritual


def criar_representantes(config, contexto):
    if not config.getboolean("ESQUELETOS", "ativos", fallback=True):
        return []

    quantidade = config.getint("ESQUELETOS", "quantidade_externa", fallback=4)
    largura_n = config.getint("ESQUELETOS", "largura_numeros", fallback=25)
    largura_e = config.getint("ESQUELETOS", "largura_estrelas", fallback=6)
    nomes = [
        "Ossário da Cripta",
        "Tíbia do Intervalo",
        "Crânio das Vinte e Cinco Pedras",
        "Marfim das Seis Estrelas",
        "Fémur do Corredor Móvel",
    ]

    saida = []
    for i in range(quantidade):
        chave, ritual = gerar(None, contexto, largura_n, largura_e)
        saida.append({
            "nome": nomes[i % len(nomes)],
            "tipo": "Esqueleto das Catacumbas",
            "chave": chave,
            "ritual": ritual,
        })
    return saida
