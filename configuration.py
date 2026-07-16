from configparser import ConfigParser
from world.presets.loader import resolve_preset_path

def load_config(caminho="config.txt"):
    cfg=ConfigParser(strict=False)
    cfg.read(caminho,encoding="utf-8")
    world=cfg.get("MUNDO","ficheiro",fallback="").strip()
    if world:
        path=resolve_preset_path(world)
        cfg.read(path,encoding="utf-8")
        cfg.set("MUNDO","ficheiro_carregado",str(path))
    return cfg
