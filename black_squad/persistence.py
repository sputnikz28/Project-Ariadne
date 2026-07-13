
import json
from pathlib import Path
from datetime import datetime, timezone

BASE = Path("esquadrao_negro")
SOMBRA = BASE / "dark_library"
REFLEXOS = SOMBRA / "reflexos_corrompidos"
ROUBADAS = SOMBRA / "reliquias_roubadas"
RITUAIS = BASE / "ritual_archive"
GRIMORIO = SOMBRA / "grimorio_negro.json"


def agora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ler(path, padrao):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return padrao


def save(path, dados):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8")


def load_grimoire():
    return ler(GRIMORIO, {
        "nivel": 1,
        "conhecimento": {},
        "livros_copiados": [],
        "reliquias_roubadas": [],
        "lendas_ressuscitadas": [],
        "execucoes": 0,
    })


def save_grimoire(dados):
    save(GRIMORIO, dados)
