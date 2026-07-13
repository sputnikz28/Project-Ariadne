
import json
import random
from pathlib import Path
from datetime import datetime, timezone

BASE = Path("artefactos/reliquias")
ORDEM = {"COMUM": 0, "RARO": 1, "EPICO": 2, "LENDARIO": 3, "MITICO": 4}

COMPATIBILIDADE = {
    "Presa": {"Lobisomem", "Vidente", "Cronomante"},
    "Espelho": {"Vidente", "Bruxa", "Cronomante"},
    "Livro": {"Mago Temporal", "Druida dos Ecos", "Treefolk IA", "Shaman", "Bruxa"},
    "Osso": {"Chefe Tribal", "Shaman"},
    "Fragmento": {"Melfork Genético", "Vidente", "Cronomante"},
    "Coroa": {"Goblin", "Bruxa"},
    "Lágrima": {"Melfork Genético", "Vidente", "Elfo"},
}


def _agora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def guardar(artefacto):
    BASE.mkdir(parents=True, exist_ok=True)
    (BASE / f"{artefacto['id']}.json").write_text(
        json.dumps(artefacto, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def carregar_todos():
    BASE.mkdir(parents=True, exist_ok=True)
    saida = []
    for path in BASE.glob("ART-*.json"):
        try:
            saida.append(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue
    return saida


def compatibilidade(classe, artefacto):
    classe = classe.replace("Renascido ", "")
    for palavra, classes in COMPATIBILIDADE.items():
        if palavra.lower() in artefacto.get("nome", "").lower():
            return classe in classes
    return classe not in {"Goblin"}


def talvez_materializar(config, artefacto, seed):
    if not config.getboolean("ARCA_ARTEFACTOS", "ativa", fallback=True):
        return False
    minima = config.get("ARCA_ARTEFACTOS", "raridade_minima", fallback="RARO").upper()
    if ORDEM.get(artefacto.get("raridade", "COMUM"), 0) < ORDEM.get(minima, 1):
        return False
    if random.random() > config.getfloat("ARCA_ARTEFACTOS", "chance_materializacao", fallback=0.10):
        return False

    persistente = dict(artefacto)
    persistente.update({
        "universo_origem": seed,
        "estado": "PERDIDO",
        "portador_atual": None,
        "vezes_encontrado": 0,
        "execucoes_sobrevividas": 0,
        "historia": [{
            "evento": "MATERIALIZADO_NA_ARCA",
            "momento": _agora(),
            "criador": artefacto.get("criador"),
        }],
    })
    guardar(persistente)
    return True


def preparar_nova_execucao(config):
    incremento = config.getfloat("ARCA_ARTEFACTOS", "energia_evolucao_por_execucao", fallback=0.10)
    for art in carregar_todos():
        art["execucoes_sobrevividas"] = art.get("execucoes_sobrevividas", 0) + 1
        art["energia_acumulada"] = round(art.get("energia_acumulada", 0.0) + incremento, 4)
        evoluir_raridade(art)
        guardar(art)


def evoluir_raridade(art):
    feitos = (
        art.get("vezes_encontrado", 0)
        + art.get("conselhos", 0)
        + len(art.get("donos", []))
        + art.get("execucoes_sobrevividas", 0) // 3
    )
    if feitos >= 20:
        art["raridade"], art["multiplicador"] = "MITICO", 2.0
    elif feitos >= 12:
        art["raridade"], art["multiplicador"] = "LENDARIO", 1.6
    elif feitos >= 6:
        art["raridade"], art["multiplicador"] = "EPICO", 1.3


def tentar_encontrar(config, herois, geracao, contador_execucao, eventos):
    if not config.getboolean("ARCA_ARTEFACTOS", "permitir_redescoberta", fallback=True):
        return contador_execucao
    maximo = config.getint("ARCA_ARTEFACTOS", "max_encontrados_por_execucao", fallback=3)
    if contador_execucao >= maximo:
        return contador_execucao

    chance = config.getfloat("ARCA_ARTEFACTOS", "chance_encontro_por_geracao", fallback=0.025)
    perdidos = [a for a in carregar_todos() if a.get("estado") == "PERDIDO"]
    random.shuffle(perdidos)

    for heroi in herois:
        if contador_execucao >= maximo or not perdidos:
            break
        compativeis = [a for a in perdidos if compatibilidade(heroi.raca, a)]
        if not compativeis or random.random() > chance:
            continue

        art = random.choice(compativeis)
        art["estado"] = "ENCONTRADO"
        art["portador_atual"] = heroi.nome
        art.setdefault("donos", []).append(heroi.nome)
        art["vezes_encontrado"] = art.get("vezes_encontrado", 0) + 1
        art.setdefault("historia", []).append({
            "evento": "REENCONTRADO",
            "momento": _agora(),
            "geracao": geracao,
            "personagem": heroi.nome,
            "classe": heroi.raca,
        })
        guardar(art)
        heroi.amuletos.append(art)
        eventos.append({
            "evento": "REDESCOBERTA_PERSISTENTE",
            "geracao": geracao,
            "dono": heroi.nome,
            "artefacto": art,
        })
        perdidos.remove(art)
        contador_execucao += 1

    return contador_execucao


def marcar_perdido(artefacto, antigo_dono, geracao):
    if not isinstance(artefacto, dict) or not artefacto.get("id"):
        return
    path = BASE / f"{artefacto['id']}.json"
    if not path.exists():
        return
    artefacto["estado"] = "PERDIDO"
    artefacto["portador_atual"] = None
    artefacto.setdefault("historia", []).append({
        "evento": "PERDIDO_APOS_ELIMINACAO",
        "momento": _agora(),
        "geracao": geracao,
        "antigo_dono": antigo_dono,
    })
    guardar(artefacto)
