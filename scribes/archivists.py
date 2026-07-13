
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


BASE = Path("escribas")


def agora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ler(path, padrao):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return padrao


def guardar(path, dados):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8")


def listar_json(pasta):
    itens = []
    for path in Path(pasta).glob("*.json"):
        dados = ler(path, {})
        if dados:
            itens.append(dados)
    return itens


def inventariar_era(era, resumo_execucao):
    artefactos = listar_json("artefactos/reliquias")
    reflexos = listar_json("black_squad/dark_library/corrupted_reflections")
    roubadas = listar_json("black_squad/dark_library/stolen_relics")
    missoes = listar_json("elven_order/mission_archive")
    livros = listar_json("amuletos/books")
    lendas = ler("lendas/livro_personagens_lendarias.json", {"personagens": []}).get("personagens", [])
    individuos = ler("data/todos_individuos.json", [])

    inventario = {
        "era": era,
        "criado_em": agora(),
        "resumo_execucao": resumo_execucao,
        "contagens": {
            "artefactos_persistentes": len(artefactos),
            "livros_proibidos": len(livros),
            "reflexos_sombrios": len(reflexos),
            "reliquias_roubadas": len(roubadas),
            "missoes_elficas": len(missoes),
            "lendas": len(lendas),
            "individuos_registados": len(individuos),
        },
        "artefactos": artefactos,
        "livros": [
            {
                "nome": l.get("nome") or l.get("livro"),
                "tipo": l.get("tipo"),
                "atualizado_em": l.get("atualizado_em"),
            }
            for l in livros
        ],
        "reflexos_sombrios": reflexos,
        "reliquias_roubadas": roubadas,
        "lendas": lendas,
    }
    guardar(BASE / "inventarios" / f"inventario_era_{era:03d}.json", inventario)
    return inventario


def criar_biografias(era, maximo=12):
    individuos = ler("data/todos_individuos.json", [])
    individuos = sorted(individuos, key=lambda x: x.get("pontos", 0), reverse=True)[:maximo]
    criadas = []
    for pessoa in individuos:
        bio = {
            "era": era,
            "id": pessoa.get("id"),
            "nome": pessoa.get("nome"),
            "raca": pessoa.get("raca"),
            "casa": pessoa.get("casa"),
            "geracao": pessoa.get("geracao"),
            "pais": pessoa.get("pais", []),
            "pontos": pessoa.get("pontos", 0),
            "titulo": pessoa.get("titulo"),
            "estado": pessoa.get("estado"),
            "amuletos": pessoa.get("amuletos", []),
            "melhores_chaves": sorted(
                pessoa.get("chaves", []),
                key=lambda x: (x.get("acertos_numeros", 0), x.get("acertos_estrelas", 0)),
                reverse=True,
            )[:5],
            "criada_em": agora(),
        }
        nome_seguro = "".join(c for c in (pessoa.get("id") or "sem_id") if c.isalnum() or c in "-_")
        path = BASE / "biografias" / f"era_{era:03d}_{nome_seguro}.json"
        guardar(path, bio)
        criadas.append(str(path))
    return criadas


def atualizar_atlas(era, inventario):
    atlas_path = BASE / "atlas" / "atlas_do_universo.json"
    atlas = ler(atlas_path, {"nome": "Atlas do Universo", "eras": []})
    atlas["eras"].append({
        "era": era,
        "momento": agora(),
        "contagens": inventario["contagens"],
        "chave_original": inventario["resumo_execucao"].get("chave_original"),
        "chave_corrompida": inventario["resumo_execucao"].get("chave_corrompida"),
        "seed": inventario["resumo_execucao"].get("seed"),
    })
    atlas["total_eras"] = len(atlas["eras"])
    guardar(atlas_path, atlas)
    return atlas


def criar_museu(era, inventario):
    salas = {
        "Sala I — Relíquias Persistentes": inventario["artefactos"],
        "Sala II — Reflexos Sombrios": inventario["reflexos_sombrios"],
        "Sala III — Relíquias Roubadas": inventario["reliquias_roubadas"],
        "Sala IV — Personagens Lendárias": inventario["lendas"],
    }
    museu = {
        "era": era,
        "nome": "Museu do Mosteiro",
        "criado_em": agora(),
        "salas": salas,
    }
    guardar(BASE / "museu" / f"museu_era_{era:03d}.json", museu)
    return museu


def escrever_cronica(era, inventario):
    r = inventario["resumo_execucao"]
    linhas = [
        "╔════════════════════════════════════════════════════╗",
        f"             📜 CRÓNICA DA ERA {era}",
        "╚════════════════════════════════════════════════════╝",
        "",
        f"Semente do universo: {r.get('seed')}",
        f"Chave original: {r.get('chave_original')}",
        f"Chave corrompida: {r.get('chave_corrompida')}",
        f"Indivíduos únicos: {r.get('individuos')}",
        f"Chaves das raças antigas: {r.get('chaves_antigas')}",
        f"Magos Negros: {r.get('magos_negros')}",
        f"Missões Élficas nesta era: {r.get('missoes_elficas')}",
        f"Artefactos persistentes: {inventario['contagens']['artefactos_persistentes']}",
        f"Livros proibidos: {inventario['contagens']['livros_proibidos']}",
        f"Reflexos sombrios: {inventario['contagens']['reflexos_sombrios']}",
        f"Lendas: {inventario['contagens']['lendas']}",
        "",
        "Os Escribas fecharam os portões do arquivo e selaram esta era.",
    ]
    path = BASE / "cronicas" / f"cronica_era_{era:03d}.txt"
    path.write_text("\n".join(linhas), encoding="utf-8")
    return path


def inventario_resumido(inventario):
    raridades = Counter(a.get("raridade", "DESCONHECIDA") for a in inventario["artefactos"])
    estados = Counter(a.get("estado", "DESCONHECIDO") for a in inventario["artefactos"])
    return {
        "raridades": dict(raridades),
        "estados": dict(estados),
        "artefactos": inventario["contagens"]["artefactos_persistentes"],
        "livros": inventario["contagens"]["livros_proibidos"],
        "lendas": inventario["contagens"]["lendas"],
    }
