
import json
import random
import shutil
import uuid
from pathlib import Path

from black_squad.persistencia import (
    REFLEXOS, ROUBADAS, RITUAIS, agora, load_grimoire, save, save_grimoire
)
from black_squad.estrategias import generate_promising_key, diversificar
from amulets.persistencia import BOOKS, ler_json
from artefacts.arca import load_all, save as save_relic


NAMES = [
    "Morthak da Sombra",
    "Veyron Eclipse",
    "Nyx do Desvio",
    "Sable das Matrizes",
    "Kharon dos Ecos Mortos",
    "Zareth Anti-Humano",
]

CONHECIMENTO_POR_LIVRO = {
    "livro_numeros_quentes.json": "frequencias",
    "livro_numeros_frios.json": "frequencias",
    "livro_pares_sagrados.json": "pares",
    "livro_trios_proibidos.json": "trios",
    "livro_gaps.json": "gaps",
    "grimorio_extracoes.json": "historico",
}


def _corromper_objeto(objeto, corruption):
    clone = json.loads(json.dumps(objeto))
    clone["tipo"] = "COPIA_SOMBRIA"
    clone["fidelidade"] = round(1.0 - corruption, 4)
    clone["corrupcao"] = round(corruption, 4)
    clone["criado_em"] = agora()
    return clone


def tentar_copiar_livros(config, events):
    grimoire = load_grimoire()
    maximo = config.getint("ESQUADRAO_NEGRO", "max_copias_por_execucao", fallback=2)
    chance = config.getfloat("ESQUADRAO_NEGRO", "chance_copiar_livro", fallback=0.60)
    minimo = config.getfloat("ESQUADRAO_NEGRO", "corrupcao_copia_min", fallback=0.05)
    maximo_corr = config.getfloat("ESQUADRAO_NEGRO", "corrupcao_copia_max", fallback=0.35)

    candidates = [p for p in BOOKS.glob("*.json")]
    random.shuffle(candidates)
    copiados = 0

    for path in candidates:
        if copiados >= maximo:
            break
        if random.random() > chance:
            continue
        original = ler_json(path, {})
        corruption = random.uniform(minimo, maximo_corr)
        copia = _corromper_objeto(original, corruption)
        copia["original"] = path.name
        copia["roubado_por"] = random.choice(NAMES)
        copia["id"] = "LIVRO-NEGRO-" + uuid.uuid4().hex[:8].upper()
        destino = REFLEXOS / f"{copia['id']}.json"
        save(destino, copia)

        if path.name not in grimoire["livros_copiados"]:
            grimoire["livros_copiados"].append(path.name)
        conhecimento = CONHECIMENTO_POR_LIVRO.get(path.name)
        if conhecimento:
            grimoire["conhecimento"][conhecimento] = True
        events.append({
            "tipo": "COPIA_LIVRO",
            "mago": copia["roubado_por"],
            "livro": path.name,
            "copia": destino.name,
            "corrupcao": copia["corrupcao"],
        })
        copiados += 1

    grimoire["nivel"] = 1 + len(grimoire["livros_copiados"]) + len(grimoire["reliquias_roubadas"])
    grimoire["execucoes"] = grimoire.get("execucoes", 0) + 1
    save_grimoire(grimoire)
    return grimoire


def tentar_roubar_reliquia(config, events):
    grimoire = load_grimoire()
    chance = config.getfloat("ESQUADRAO_NEGRO", "chance_roubar_reliquia", fallback=0.30)
    maximo = config.getint("ESQUADRAO_NEGRO", "max_reliquias_roubadas_por_execucao", fallback=1)
    disponiveis = [a for a in load_all() if a.get("estado") in {"PERDIDO", "ENCONTRADO", "ATIVO"}]
    random.shuffle(disponiveis)
    roubadas = 0

    for artefacto in disponiveis:
        if roubadas >= maximo:
            break
        if random.random() > chance:
            continue

        artefacto["estado"] = "ROUBADO_PELO_ESQUADRAO_NEGRO"
        artefacto["portador_atual"] = random.choice(NAMES)
        artefacto["corrupcao_sombria"] = round(random.uniform(0.10, 0.50), 4)
        artefacto.setdefault("historia", []).append({
            "evento": "ROUBADO_PELO_ESQUADRAO_NEGRO",
            "momento": agora(),
            "mago": artefacto["portador_atual"],
        })
        save_relic(artefacto)
        save(ROUBADAS / f"{artefacto['id']}.json", artefacto)
        if artefacto["id"] not in grimoire["reliquias_roubadas"]:
            grimoire["reliquias_roubadas"].append(artefacto["id"])
        events.append({
            "tipo": "ROUBO_RELIQUIA",
            "mago": artefacto["portador_atual"],
            "artefacto": artefacto,
        })
        roubadas += 1

    grimoire["nivel"] = 1 + len(grimoire["livros_copiados"]) + len(grimoire["reliquias_roubadas"])
    save_grimoire(grimoire)
    return grimoire


def create_mages(config, contexto, events):
    quantidade = config.getint("ESQUADRAO_NEGRO", "quantidade", fallback=5)
    grimoire = tentar_copiar_livros(config, events)
    grimoire = tentar_roubar_reliquia(config, events)

    candidates = []
    for idx in range(max(quantidade * 3, 10)):
        key, score = generate_promising_key(contexto["estatisticas"], grimoire, config)
        candidates.append({
            "nome": NAMES[idx % len(NAMES)] + f" #{idx + 1}",
            "tipo": "Mago do Esquadrão Negro",
            "chave": key,
            "score": score,
            "nivel_grimorio": grimoire["nivel"],
            "conhecimento": dict(grimoire["conhecimento"]),
        })

    escolhidos = diversificar(candidates, quantidade)
    return escolhidos, grimoire


def tentar_ressuscitar_lenda(config, events):
    if not config.getboolean("LENDAS", "permitir_necromancia", fallback=True):
        return None
    grimoire = load_grimoire()
    if not grimoire.get("conhecimento", {}).get("historico"):
        return None
    if random.random() > config.getfloat("ESQUADRAO_NEGRO", "chance_ressuscitar_lenda", fallback=0.15):
        return None

    livro = ler_json("lendas/livro_personagens_lendarias.json", {"personagens": []})
    echoes = ler_json("lendas/ecos_ancestrais.json", {"ecos": []})
    candidates = livro.get("personagens", []) + echoes.get("ecos", [])
    if not candidates:
        return None

    lenda = random.choice(candidates)
    eco = {
        "id": "RESS-" + uuid.uuid4().hex[:8].upper(),
        "nome": lenda["nome"] + " Eclipse",
        "classe": "Lenda Ressuscitada",
        "origem": lenda.get("origem", lenda.get("universo", "Era Perdida")),
        "chave": (
            lenda.get("chave", lenda.get("chave_memoria", {})).get("numeros", [4, 17, 23, 34, 46]),
            lenda.get("chave", lenda.get("chave_memoria", {})).get("estrelas", [3, 9]),
        ),
        "corrupcao": round(random.uniform(0.05, 0.35), 4),
        "ressuscitado_por": random.choice(NAMES),
    }
    save(RITUAIS / f"{eco['id']}.json", eco)
    grimoire["lendas_ressuscitadas"].append(eco["id"])
    grimoire["conhecimento"]["necromancia"] = True
    save_grimoire(grimoire)
    events.append({"tipo": "RESSURREICAO", "eco": eco})
    return eco
