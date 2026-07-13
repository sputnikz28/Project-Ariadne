from configparser import ConfigParser
from pathlib import Path

def main():
    for path in sorted(Path("mundos").glob("*.ini")):
        cfg=ConfigParser(); cfg.read(path,encoding="utf-8")
        print(f"{path.name}: {cfg.get('UNIVERSO','nome',fallback='Sem nome')} — {cfg.get('UNIVERSO','descricao',fallback='')}")

if __name__=="__main__": main()
