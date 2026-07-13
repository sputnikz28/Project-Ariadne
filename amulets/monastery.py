
import random
from amulets.persistencia import ler_json, LIVROS

MAPA_LIVROS = {
    "quentes": "livro_numeros_quentes.json",
    "frios": "livro_numeros_frios.json",
    "historico": "grimorio_extracoes.json",
    "pares": "livro_pares_sagrados.json",
    "trios": "livro_trios_proibidos.json",
    "estrelas": "livro_estrelas.json",
    "atrasos": "livro_atrasos.json",
    "gaps": "livro_gaps.json",
}


def _classes(config, chave):
    return {
        x.strip() for x in config.get("MONGES_E_ESCRIBAS", chave, fallback="").split(",")
        if x.strip()
    }


def livros_permitidos(config, classe):
    classe = classe.replace("Renascido ", "")
    if classe in _classes(config, "acesso_total"):
        return list(MAPA_LIVROS)

    permitidos = []
    if classe in _classes(config, "acesso_quentes_frios"):
        permitidos += ["quentes", "frios", "atrasos"]
    if classe in _classes(config, "acesso_historico"):
        permitidos += ["historico", "estrelas", "atrasos"]
    if classe in _classes(config, "acesso_pares_trios"):
        permitidos += ["pares", "trios"]
    if classe in _classes(config, "acesso_gaps"):
        permitidos += ["gaps"]
    return sorted(set(permitidos))


def conceder_audiencia(config, heroi, geracao, eventos):
    permitidos = livros_permitidos(config, heroi.raca)
    if not permitidos:
        return []
    if random.random() > config.getfloat("MONGES_E_ESCRIBAS", "chance_audiencia", fallback=0.35):
        return []

    maximo = config.getint("MONGES_E_ESCRIBAS", "max_consultas_por_heroi", fallback=2)
    escolhidos = random.sample(permitidos, min(maximo, len(permitidos)))
    conhecimentos = []

    for tipo in escolhidos:
        livro = ler_json(LIVROS / MAPA_LIVROS[tipo], {})
        resumo = {"tipo": tipo, "livro": livro.get("nome", MAPA_LIVROS[tipo])}
        if tipo == "quentes":
            resumo["numeros"] = [x["numero"] for x in livro.get("numeros", [])[:5]]
        elif tipo == "frios":
            resumo["numeros"] = [x["numero"] for x in livro.get("numeros", [])[:5]]
        elif tipo == "atrasos":
            resumo["numeros"] = [x["numero"] for x in livro.get("numeros", [])[:5]]
        elif tipo == "estrelas":
            resumo["estrelas"] = [x["estrela"] for x in livro.get("estrelas", [])[:4]]
        elif tipo == "pares":
            resumo["pares"] = [x["numeros"] for x in livro.get("pares", [])[:3]]
        elif tipo == "trios":
            resumo["trios"] = [x["numeros"] for x in livro.get("trios", [])[:2]]
        elif tipo == "gaps":
            resumo["gaps"] = [x["gap"] for x in livro.get("gaps", [])[:5]]
        elif tipo == "historico":
            resumo["total_extracoes"] = livro.get("total_extracoes", 0)

        conhecimentos.append(resumo)
        eventos.append({
            "geracao": geracao,
            "id": heroi.id,
            "nome": heroi.nome,
            "classe": heroi.raca,
            "livro": resumo["livro"],
            "tipo": tipo,
            "autorizado": True,
        })

    heroi.genoma["conhecimento_oculto"] = conhecimentos
    return conhecimentos
