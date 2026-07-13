
import random
from amulets.persistencia import ler_json, BOOKS

BOOKS_MAP = {
    "quentes": "livro_numeros_quentes.json",
    "frios": "livro_numeros_frios.json",
    "historico": "grimorio_extracoes.json",
    "pares": "livro_pares_sagrados.json",
    "trios": "livro_trios_proibidos.json",
    "estrelas": "livro_estrelas.json",
    "atrasos": "livro_atrasos.json",
    "gaps": "livro_gaps.json",
}


def _faction_classes(config, key):
    return {
        x.strip() for x in config.get("MONGES_E_ESCRIBAS", key, fallback="").split(",")
        if x.strip()
    }


def livros_permitidos(config, faction_class):
    faction_class = faction_class.replace("Renascido ", "")
    if faction_class in _faction_classes(config, "acesso_total"):
        return list(BOOKS_MAP)

    permitidos = []
    if faction_class in _faction_classes(config, "acesso_quentes_frios"):
        permitidos += ["quentes", "frios", "atrasos"]
    if faction_class in _faction_classes(config, "acesso_historico"):
        permitidos += ["historico", "estrelas", "atrasos"]
    if faction_class in _faction_classes(config, "acesso_pares_trios"):
        permitidos += ["pares", "trios"]
    if faction_class in _faction_classes(config, "acesso_gaps"):
        permitidos += ["gaps"]
    return sorted(set(permitidos))


def conceder_audiencia(config, heroi, generation, events):
    permitidos = livros_permitidos(config, heroi.raca)
    if not permitidos:
        return []
    if random.random() > config.getfloat("MONGES_E_ESCRIBAS", "chance_audiencia", fallback=0.35):
        return []

    maximo = config.getint("MONGES_E_ESCRIBAS", "max_consultas_por_heroi", fallback=2)
    escolhidos = random.sample(permitidos, min(maximo, len(permitidos)))
    conhecimentos = []

    for kind in escolhidos:
        livro = ler_json(BOOKS / BOOKS_MAP[kind], {})
        resumo = {"tipo": kind, "livro": livro.get("nome", BOOKS_MAP[kind])}
        if kind == "quentes":
            resumo["numeros"] = [x["numero"] for x in livro.get("numeros", [])[:5]]
        elif kind == "frios":
            resumo["numeros"] = [x["numero"] for x in livro.get("numeros", [])[:5]]
        elif kind == "atrasos":
            resumo["numeros"] = [x["numero"] for x in livro.get("numeros", [])[:5]]
        elif kind == "estrelas":
            resumo["estrelas"] = [x["estrela"] for x in livro.get("estrelas", [])[:4]]
        elif kind == "pares":
            resumo["pares"] = [x["numeros"] for x in livro.get("pares", [])[:3]]
        elif kind == "trios":
            resumo["trios"] = [x["numeros"] for x in livro.get("trios", [])[:2]]
        elif kind == "gaps":
            resumo["gaps"] = [x["gap"] for x in livro.get("gaps", [])[:5]]
        elif kind == "historico":
            resumo["total_extracoes"] = livro.get("total_extracoes", 0)

        conhecimentos.append(resumo)
        events.append({
            "geracao": generation,
            "id": heroi.id,
            "nome": heroi.name,
            "classe": heroi.raca,
            "livro": resumo["livro"],
            "tipo": kind,
            "autorizado": True,
        })

    heroi.genoma["conhecimento_oculto"] = conhecimentos
    return conhecimentos
