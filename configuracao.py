from configparser import ConfigParser
from pathlib import Path

def carregar_config(caminho="config.txt"):
    cfg=ConfigParser(strict=False)
    cfg.read(caminho,encoding="utf-8")
    mundo=cfg.get("MUNDO","ficheiro",fallback="").strip()
    if mundo:
        path=Path(mundo)
        if not path.exists():
            raise FileNotFoundError(f"Ficheiro de mundo não encontrado: {path}")
        cfg.read(path,encoding="utf-8")
        cfg.set("MUNDO","ficheiro_carregado",str(path))
    return cfg
