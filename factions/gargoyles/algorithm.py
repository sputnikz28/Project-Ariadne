import json
import random
from pathlib import Path


def load_pairs():
    return json.loads(Path("library/indexes/duplas.json").read_text(encoding="utf-8"))


def complete(pair):
    nums = list(pair)
    while len(nums) < 5:
        n = random.randint(1, 50)
        if n not in nums:
            nums.append(n)
    return sorted(nums), sorted(random.sample(range(1, 13), 2))


def stone_lineage():
    data = load_pairs()
    candidates = data.get("duplas_mais_comuns", [])[:30]
    pair = random.choice(candidates)["numeros"] if candidates else random.sample(range(1, 51), 2)
    return {
        "nome": "Gorath da Linhagem de Pedra",
        "classe": "Gárgula",
        "linhagem": "Pedra",
        "doutrina": "Duplas historicamente consistentes.",
        "dupla": pair,
        "chave": complete(pair),
    }


def mirror_lineage():
    data = load_pairs()
    candidates = data.get("duplas_consecutivas", [])[:30] or data.get("duplas_mais_comuns", [])[:30]
    pair = random.choice(candidates)["numeros"] if candidates else [16, 17]
    return {
        "nome": "Seraphine da Linhagem do Espelho",
        "classe": "Gárgula",
        "linhagem": "Espelho",
        "doutrina": "Duplas consecutivas e relações simétricas.",
        "dupla": pair,
        "chave": complete(pair),
    }


def create_gargoyles():
    return [stone_lineage(), mirror_lineage()]
