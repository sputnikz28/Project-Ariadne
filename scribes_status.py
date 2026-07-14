
import json
from pathlib import Path


def ler(path, padrao):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return padrao


def main():
    atlas = ler("orders/scribes/atlas/atlas_do_universo.json", {"eras": []})
    inventarios = list(Path("orders/scribes/inventories").glob("inventario_era_*.json"))
    cronicas = list(Path("orders/scribes/chronicles").glob("cronica_era_*.txt"))
    bios = list(Path("orders/scribes/biographies").glob("*.json"))
    museus = list(Path("orders/scribes/museum").glob("*.json"))

    print("📚 Eras no Atlas:", len(atlas.get("eras", [])))
    print("📦 Inventários:", len(inventarios))
    print("📜 Crónicas:", len(cronicas))
    print("👤 Biografias:", len(bios))
    print("🏛️ Museus:", len(museus))


if __name__ == "__main__":
    main()
