import json
import random
from pathlib import Path


def load_triples():
    return json.loads(Path("library/indexes/triplas.json").read_text(encoding="utf-8"))


def complete(triple):
    nums = list(triple)
    while len(nums) < 5:
        n = random.randint(1, 50)
        if n not in nums:
            nums.append(n)
    return sorted(nums), sorted(random.sample(range(1, 13), 2))


def blood_lineage():
    data = load_triples()
    candidates = data.get("triplas_mais_comuns", [])[:20]
    choice = random.choice(candidates)["numeros"] if candidates else random.sample(range(1, 51), 3)
    key = complete(choice)
    return {
        "nome": "Conde Vaelor da Linhagem Sanguínea",
        "classe": "Vampiro",
        "linhagem": "Sanguínea",
        "doutrina": "Triplas frequentes inseridas numa chave equilibrada.",
        "tripla": choice,
        "chave": key,
    }


def shadow_lineage():
    data = load_triples()
    candidates = data.get("triplas_consecutivas", [])[:20] or data.get("triplas_mais_comuns", [])[:20]
    choice = random.choice(candidates)["numeros"] if candidates else [16, 17, 18]
    key = complete(choice)
    return {
        "nome": "Lady Nyx da Linhagem Sombria",
        "classe": "Vampiro",
        "linhagem": "Sombria",
        "doutrina": "Triplas consecutivas, harmónicas e repetitivas.",
        "tripla": choice,
        "chave": key,
    }


def create_vampires():
    return [blood_lineage(), shadow_lineage()]
