
import random
import uuid

from artefactos.arca import talvez_materializar

RARIDADES = [
    ("COMUM", 0.55, 1.05),
    ("RARO", 0.25, 1.15),
    ("EPICO", 0.13, 1.30),
    ("LENDARIO", 0.06, 1.60),
    ("MITICO", 0.01, 2.00),
]

NOMES = [
    "Osso Lunar",
    "Espelho dos Sonhos Esquecidos",
    "Livro dos Ecos",
    "Presa Imutável de Fenrir",
    "Fragmento Divino",
    "Lágrima da Primeira Luz",
    "Coroa Quebrada de Malphas",
]


def raridade():
    rolagem = random.random()
    acumulado = 0.0
    for nome, probabilidade, multiplicador in RARIDADES:
        acumulado += probabilidade
        if rolagem <= acumulado:
            return nome, multiplicador
    return "COMUM", 1.05


def forjar(criador, geracao, config=None, seed=None):
    rar, multiplicador = raridade()
    artefacto = {
        "id": "ART-" + uuid.uuid4().hex[:10].upper(),
        "nome": random.choice(NOMES),
        "raridade": rar,
        "multiplicador": multiplicador,
        "criador": criador.nome,
        "geracao_criacao": geracao,
        "donos": [criador.nome],
        "energia_acumulada": 0.0,
        "conselhos": 0,
        "estado": "ATIVO",
    }
    if config is not None:
        talvez_materializar(config, artefacto, seed)
    return artefacto


def evoluir(herois, taxa):
    for heroi in herois:
        for artefacto in heroi.amuletos:
            if isinstance(artefacto, dict):
                artefacto["energia_acumulada"] = round(
                    artefacto.get("energia_acumulada", 0.0)
                    + max(0, heroi.pontos) * taxa,
                    4,
                )


def herdar(eliminado, elite):
    eventos = []
    if not elite:
        return eventos

    for artefacto in list(eliminado.amuletos):
        destino = random.choice(elite)
        if isinstance(artefacto, dict):
            artefacto.setdefault("donos", []).append(destino.nome)
            artefacto["estado"] = "HERDADO"
        destino.amuletos.append(artefacto)
        eventos.append((eliminado.nome, destino.nome, artefacto))

    eliminado.amuletos = []
    return eventos
