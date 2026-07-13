
import json
import random
import shutil
import uuid
from pathlib import Path

from black_squad.persistencia import (
    REFLEXOS, ROUBADAS, RITUAIS, agora, carregar_grimorio, guardar, guardar_grimorio
)
from black_squad.estrategias import gerar_chave_promissora, diversificar
from amulets.persistencia import LIVROS, ler_json
from artefacts.arca import carregar_todos, guardar as guardar_reliquia


NOMES = [
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


def _corromper_objeto(objeto, corrupcao):
    clone = json.loads(json.dumps(objeto))
    clone["tipo"] = "COPIA_SOMBRIA"
    clone["fidelidade"] = round(1.0 - corrupcao, 4)
    clone["corrupcao"] = round(corrupcao, 4)
    clone["criado_em"] = agora()
    return clone


def tentar_copiar_livros(config, eventos):
    grimorio = carregar_grimorio()
    maximo = config.getint("ESQUADRAO_NEGRO", "max_copias_por_execucao", fallback=2)
    chance = config.getfloat("ESQUADRAO_NEGRO", "chance_copiar_livro", fallback=0.60)
    minimo = config.getfloat("ESQUADRAO_NEGRO", "corrupcao_copia_min", fallback=0.05)
    maximo_corr = config.getfloat("ESQUADRAO_NEGRO", "corrupcao_copia_max", fallback=0.35)

    candidatos = [p for p in LIVROS.glob("*.json")]
    random.shuffle(candidatos)
    copiados = 0

    for path in candidatos:
        if copiados >= maximo:
            break
        if random.random() > chance:
            continue
        original = ler_json(path, {})
        corrupcao = random.uniform(minimo, maximo_corr)
        copia = _corromper_objeto(original, corrupcao)
        copia["original"] = path.name
        copia["roubado_por"] = random.choice(NOMES)
        copia["id"] = "LIVRO-NEGRO-" + uuid.uuid4().hex[:8].upper()
        destino = REFLEXOS / f"{copia['id']}.json"
        guardar(destino, copia)

        if path.name not in grimorio["livros_copiados"]:
            grimorio["livros_copiados"].append(path.name)
        conhecimento = CONHECIMENTO_POR_LIVRO.get(path.name)
        if conhecimento:
            grimorio["conhecimento"][conhecimento] = True
        eventos.append({
            "tipo": "COPIA_LIVRO",
            "mago": copia["roubado_por"],
            "livro": path.name,
            "copia": destino.name,
            "corrupcao": copia["corrupcao"],
        })
        copiados += 1

    grimorio["nivel"] = 1 + len(grimorio["livros_copiados"]) + len(grimorio["reliquias_roubadas"])
    grimorio["execucoes"] = grimorio.get("execucoes", 0) + 1
    guardar_grimorio(grimorio)
    return grimorio


def tentar_roubar_reliquia(config, eventos):
    grimorio = carregar_grimorio()
    chance = config.getfloat("ESQUADRAO_NEGRO", "chance_roubar_reliquia", fallback=0.30)
    maximo = config.getint("ESQUADRAO_NEGRO", "max_reliquias_roubadas_por_execucao", fallback=1)
    disponiveis = [a for a in carregar_todos() if a.get("estado") in {"PERDIDO", "ENCONTRADO", "ATIVO"}]
    random.shuffle(disponiveis)
    roubadas = 0

    for artefacto in disponiveis:
        if roubadas >= maximo:
            break
        if random.random() > chance:
            continue

        artefacto["estado"] = "ROUBADO_PELO_ESQUADRAO_NEGRO"
        artefacto["portador_atual"] = random.choice(NOMES)
        artefacto["corrupcao_sombria"] = round(random.uniform(0.10, 0.50), 4)
        artefacto.setdefault("historia", []).append({
            "evento": "ROUBADO_PELO_ESQUADRAO_NEGRO",
            "momento": agora(),
            "mago": artefacto["portador_atual"],
        })
        guardar_reliquia(artefacto)
        guardar(ROUBADAS / f"{artefacto['id']}.json", artefacto)
        if artefacto["id"] not in grimorio["reliquias_roubadas"]:
            grimorio["reliquias_roubadas"].append(artefacto["id"])
        eventos.append({
            "tipo": "ROUBO_RELIQUIA",
            "mago": artefacto["portador_atual"],
            "artefacto": artefacto,
        })
        roubadas += 1

    grimorio["nivel"] = 1 + len(grimorio["livros_copiados"]) + len(grimorio["reliquias_roubadas"])
    guardar_grimorio(grimorio)
    return grimorio


def criar_magos(config, contexto, eventos):
    quantidade = config.getint("ESQUADRAO_NEGRO", "quantidade", fallback=5)
    grimorio = tentar_copiar_livros(config, eventos)
    grimorio = tentar_roubar_reliquia(config, eventos)

    candidatos = []
    for idx in range(max(quantidade * 3, 10)):
        chave, score = gerar_chave_promissora(contexto["estatisticas"], grimorio, config)
        candidatos.append({
            "nome": NOMES[idx % len(NOMES)] + f" #{idx + 1}",
            "tipo": "Mago do Esquadrão Negro",
            "chave": chave,
            "score": score,
            "nivel_grimorio": grimorio["nivel"],
            "conhecimento": dict(grimorio["conhecimento"]),
        })

    escolhidos = diversificar(candidatos, quantidade)
    return escolhidos, grimorio


def tentar_ressuscitar_lenda(config, eventos):
    if not config.getboolean("LENDAS", "permitir_necromancia", fallback=True):
        return None
    grimorio = carregar_grimorio()
    if not grimorio.get("conhecimento", {}).get("historico"):
        return None
    if random.random() > config.getfloat("ESQUADRAO_NEGRO", "chance_ressuscitar_lenda", fallback=0.15):
        return None

    livro = ler_json("lendas/livro_personagens_lendarias.json", {"personagens": []})
    ecos = ler_json("lendas/ecos_ancestrais.json", {"ecos": []})
    candidatos = livro.get("personagens", []) + ecos.get("ecos", [])
    if not candidatos:
        return None

    lenda = random.choice(candidatos)
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
        "ressuscitado_por": random.choice(NOMES),
    }
    guardar(RITUAIS / f"{eco['id']}.json", eco)
    grimorio["lendas_ressuscitadas"].append(eco["id"])
    grimorio["conhecimento"]["necromancia"] = True
    guardar_grimorio(grimorio)
    eventos.append({"tipo": "RESSURREICAO", "eco": eco})
    return eco
