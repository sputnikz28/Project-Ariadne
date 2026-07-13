
import json
from pathlib import Path


def ler(path, padrao):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return padrao


def main():
    atlas = ler("scribes/atlas/atlas_do_universo.json", {"eras": []})
    inventarios = list(Path("scribes/inventories").glob("inventario_era_*.json"))
    cronicas = list(Path("scribes/chronicles").glob("cronica_era_*.txt"))
    bios = list(Path("scribes/biographies").glob("*.json"))
    museus = list(Path("scribes/museu").glob("*.json"))

    print("📚 Eras no Atlas:", len(atlas.get("eras", [])))
    print("📦 Inventários:", len(inventarios))
    print("📜 Crónicas:", len(cronicas))
    print("👤 Biografias:", len(bios))
    print("🏛️ Museus:", len(museus))


if __name__ == "__main__":
    main()
