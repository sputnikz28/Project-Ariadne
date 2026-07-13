
import json
from pathlib import Path
from datetime import datetime, timezone

BASE = Path("esquadrao_negro")
SOMBRA = BASE / "biblioteca_sombria"
REFLEXOS = SOMBRA / "reflexos_corrompidos"
ROUBADAS = SOMBRA / "reliquias_roubadas"
RITUAIS = BASE / "arquivo_rituais"
GRIMORIO = SOMBRA / "grimorio_negro.json"


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


def carregar_grimorio():
    return ler(GRIMORIO, {
        "nivel": 1,
        "conhecimento": {},
        "livros_copiados": [],
        "reliquias_roubadas": [],
        "lendas_ressuscitadas": [],
        "execucoes": 0,
    })


def guardar_grimorio(dados):
    guardar(GRIMORIO, dados)
