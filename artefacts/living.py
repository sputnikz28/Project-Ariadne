
import random
import uuid

from artefacts.arca import maybe_materialize

RARIDADES = [
    ("COMUM", 0.55, 1.05),
    ("RARO", 0.25, 1.15),
    ("EPICO", 0.13, 1.30),
    ("LENDARIO", 0.06, 1.60),
    ("MITICO", 0.01, 2.00),
]

NAMES = [
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
    for name, probabilidade, multiplicador in RARIDADES:
        acumulado += probabilidade
        if rolagem <= acumulado:
            return name, multiplicador
    return "COMUM", 1.05


def forjar(criador, generation, config=None, seed=None):
    rar, multiplicador = raridade()
    artefacto = {
        "id": "ART-" + uuid.uuid4().hex[:10].upper(),
        "nome": random.choice(NAMES),
        "raridade": rar,
        "multiplicador": multiplicador,
        "criador": criador.name,
        "geracao_criacao": generation,
        "donos": [criador.name],
        "energia_acumulada": 0.0,
        "conselhos": 0,
        "estado": "ATIVO",
    }
    if config is not None:
        maybe_materialize(config, artefacto, seed)
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
    events = []
    if not elite:
        return events

    for artefacto in list(eliminado.amuletos):
        destino = random.choice(elite)
        if isinstance(artefacto, dict):
            artefacto.setdefault("donos", []).append(destino.name)
            artefacto["estado"] = "HERDADO"
        destino.amuletos.append(artefacto)
        events.append((eliminado.name, destino.name, artefacto))

    eliminado.amuletos = []
    return events
