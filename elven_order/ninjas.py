
import json
import random
import uuid
from pathlib import Path
from datetime import datetime, timezone

from black_squad.persistencia import (
    REFLEXOS, ROUBADAS, load_grimoire, save_grimoire, ler, save
)
from artefacts.arca import save as save_relic


NAMES = [
    "Kael da Folha Negra",
    "Thalion Passo Silencioso",
    "Arya da Lâmina Verde",
    "Elyndor Sem Pegadas",
    "Naeris do Orvalho Escuro",
]


def agora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def create_ninjas(config):
    quantidade = config.getint("ORDEM_ELFICA", "quantidade", fallback=4)
    ninjas = []
    for i in range(quantidade):
        ninjas.append({
            "nome": NAMES[i % len(NAMES)],
            "tipo": "Ninja Élfico",
            "furtividade": round(random.uniform(0.65, 0.98), 3),
            "velocidade": round(random.uniform(0.65, 0.98), 3),
            "resistencia_malphas": round(random.uniform(0.45, 0.95), 3),
            "conhecimento_reliquias": round(random.uniform(0.40, 0.90), 3),
        })
    return ninjas


def execute_missions(config, ninjas, events):
    estado_path = Path("elven_order/estado_ordem.json")
    estado = ler(estado_path, {
        "nivel": 1, "missoes": 0, "sucessos": 0, "falhas": 0, "itens_recuperados": []
    })
    max_missoes = config.getint("ORDEM_ELFICA", "max_missoes_por_execucao", fallback=3)
    chance_missao = config.getfloat("ORDEM_ELFICA", "chance_missao", fallback=0.70)
    chance_purificar = config.getfloat("ORDEM_ELFICA", "chance_purificar", fallback=0.60)
    bonus_fenrir = config.getfloat("ORDEM_ELFICA", "bonus_fenrir", fallback=0.15)
    grimoire = load_grimoire()

    alvos = []
    alvos += [("LIVRO", p) for p in REFLEXOS.glob("*.json")]
    alvos += [("RELIQUIA", p) for p in ROUBADAS.glob("*.json")]
    random.shuffle(alvos)

    for kind, path in alvos[:max_missoes]:
        if random.random() > chance_missao:
            continue
        equipa = random.sample(ninjas, min(2, len(ninjas)))
        poder = sum(n["furtividade"] + n["velocidade"] + n["resistencia_malphas"] for n in equipa) / (3 * len(equipa))
        defesa = min(0.90, 0.25 + grimoire.get("nivel", 1) * 0.05)
        sucesso = random.random() < min(0.95, poder + bonus_fenrir - defesa)

        missao = {
            "id": "MIS-" + uuid.uuid4().hex[:8].upper(),
            "momento": agora(),
            "tipo_alvo": kind,
            "alvo": path.name,
            "equipa": [n["nome"] for n in equipa],
            "poder": round(poder, 4),
            "defesa": round(defesa, 4),
            "sucesso": sucesso,
        }
        estado["missoes"] += 1

        if sucesso:
            estado["sucessos"] += 1
            if kind == "LIVRO":
                dados = ler(path, {})
                dados["estado"] = "RECUPERADO_PELA_ORDEM_ELFICA"
                dados["recuperado_em"] = agora()
                dados["purificado"] = random.random() < chance_purificar
                destino = Path("amulets/cache/recovered_knowledge") / path.name
                save(destino, dados)
                path.unlink(missing_ok=True)
                missao["resultado"] = "Cópia sombria recuperada e isolada."
                estado["itens_recuperados"].append(path.name)
            else:
                artefacto = ler(path, {})
                artefacto["estado"] = "RECUPERADO_PELA_ORDEM_ELFICA"
                artefacto["portador_atual"] = None
                artefacto["purificado"] = random.random() < chance_purificar
                artefacto.setdefault("historia", []).append({
                    "evento": "RECUPERADO_PELA_ORDEM_ELFICA",
                    "momento": agora(),
                    "equipa": missao["equipa"],
                })
                save_relic(artefacto)
                path.unlink(missing_ok=True)
                if artefacto.get("id") in grimoire.get("reliquias_roubadas", []):
                    grimoire["reliquias_roubadas"].remove(artefacto["id"])
                missao["resultado"] = "Relíquia recuperada e devolvida à Arca."
                estado["itens_recuperados"].append(artefacto.get("id"))
        else:
            estado["falhas"] += 1
            missao["resultado"] = "A equipa foi detetada pelas Sentinelas Negras."
            if random.random() < 0.12:
                missao["ninja_corrompido"] = random.choice(equipa)["nome"]

        save(Path("elven_order/mission_archive") / f"{missao['id']}.json", missao)
        events.append(missao)

    estado["nivel"] = 1 + estado["sucessos"] // 3
    save(estado_path, estado)
    save_grimoire(grimoire)
    return estado
