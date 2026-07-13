
import json
import random
from pathlib import Path


def carregar_duplas():
    return json.loads(Path("biblioteca/indices/duplas.json").read_text(encoding="utf-8"))


def completar(dupla):
    nums = list(dupla)
    while len(nums) < 5:
        n = random.randint(1, 50)
        if n not in nums:
            nums.append(n)
    return sorted(nums), sorted(random.sample(range(1, 13), 2))


def linhagem_pedra():
    dados = carregar_duplas()
    candidatas = dados.get("duplas_mais_comuns", [])[:30]
    dupla = random.choice(candidatas)["numeros"] if candidatas else random.sample(range(1, 51), 2)
    return {
        "nome": "Gorath da Linhagem de Pedra",
        "classe": "Gárgula",
        "linhagem": "Pedra",
        "doutrina": "Duplas historicamente consistentes.",
        "dupla": dupla,
        "chave": completar(dupla),
    }


def linhagem_espelho():
    dados = carregar_duplas()
    candidatas = dados.get("duplas_consecutivas", [])[:30] or dados.get("duplas_mais_comuns", [])[:30]
    dupla = random.choice(candidatas)["numeros"] if candidatas else [16, 17]
    return {
        "nome": "Seraphine da Linhagem do Espelho",
        "classe": "Gárgula",
        "linhagem": "Espelho",
        "doutrina": "Duplas consecutivas e relações simétricas.",
        "dupla": dupla,
        "chave": completar(dupla),
    }


def criar_gargulas():
    return [linhagem_pedra(), linhagem_espelho()]
