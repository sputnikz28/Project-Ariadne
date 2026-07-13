
import json
import random
from pathlib import Path


def carregar_triplas():
    return json.loads(Path("biblioteca/indices/triplas.json").read_text(encoding="utf-8"))


def completar(tripla):
    nums = list(tripla)
    while len(nums) < 5:
        n = random.randint(1, 50)
        if n not in nums:
            nums.append(n)
    return sorted(nums), sorted(random.sample(range(1, 13), 2))


def linhagem_sanguinea():
    dados = carregar_triplas()
    candidatas = dados.get("triplas_mais_comuns", [])[:20]
    escolha = random.choice(candidatas)["numeros"] if candidatas else random.sample(range(1, 51), 3)
    chave = completar(escolha)
    return {
        "nome": "Conde Vaelor da Linhagem Sanguínea",
        "classe": "Vampiro",
        "linhagem": "Sanguínea",
        "doutrina": "Triplas frequentes inseridas numa chave equilibrada.",
        "tripla": escolha,
        "chave": chave,
    }


def linhagem_sombria():
    dados = carregar_triplas()
    candidatas = dados.get("triplas_consecutivas", [])[:20] or dados.get("triplas_mais_comuns", [])[:20]
    escolha = random.choice(candidatas)["numeros"] if candidatas else [16, 17, 18]
    chave = completar(escolha)
    return {
        "nome": "Lady Nyx da Linhagem Sombria",
        "classe": "Vampiro",
        "linhagem": "Sombria",
        "doutrina": "Triplas consecutivas, harmónicas e repetitivas.",
        "tripla": escolha,
        "chave": chave,
    }


def criar_vampiros():
    return [linhagem_sanguinea(), linhagem_sombria()]
