
import json
from pathlib import Path
from datetime import datetime, timezone

BASE = Path("amuletos")
LIVROS = BASE / "livros"
CACHE = BASE / "cache"
FUTURAS = BASE / "extracoes_futuras"


def ler_json(caminho, padrao=None):
    path = Path(caminho)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {} if padrao is None else padrao


def guardar_json(caminho, dados):
    path = Path(caminho)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8")


def agora_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def guardar_livro(nome_ficheiro, conteudo):
    conteudo = dict(conteudo)
    conteudo.setdefault("atualizado_em", agora_iso())
    guardar_json(LIVROS / nome_ficheiro, conteudo)
    return LIVROS / nome_ficheiro
