from configparser import ConfigParser
from pathlib import Path

PRESETS_DIR = Path(__file__).parent


def list_presets():
    return sorted(PRESETS_DIR.glob("*.ini"))


def resolve_preset_path(name_or_path):
    path = Path(name_or_path)
    if not path.suffix:
        path = path.with_suffix(".ini")
    if not path.exists():
        candidate = PRESETS_DIR / path.name
        if candidate.exists():
            path = candidate
    if not path.exists():
        raise FileNotFoundError(f"Ficheiro de mundo não encontrado: {path}")
    return path


def load_preset(name_or_path):
    path = resolve_preset_path(name_or_path)
    cfg = ConfigParser(strict=False)
    cfg.read(path, encoding="utf-8")
    return cfg, path
