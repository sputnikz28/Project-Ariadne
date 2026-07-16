from configparser import ConfigParser
from world.presets.loader import list_presets

def main():
    for path in list_presets():
        cfg=ConfigParser(); cfg.read(path,encoding="utf-8")
        print(f"{path.name}: {cfg.get('UNIVERSO','nome',fallback='Sem nome')} — {cfg.get('UNIVERSO','descricao',fallback='')}")

if __name__=="__main__": main()
