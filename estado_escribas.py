
import json
from pathlib import Path


def ler(path, padrao):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return padrao


def main():
    atlas = ler("escribas/atlas/atlas_do_universo.json", {"eras": []})
    inventarios = list(Path("escribas/inventarios").glob("inventario_era_*.json"))
    cronicas = list(Path("escribas/cronicas").glob("cronica_era_*.txt"))
    bios = list(Path("escribas/biografias").glob("*.json"))
    museus = list(Path("escribas/museu").glob("*.json"))

    print("📚 Eras no Atlas:", len(atlas.get("eras", [])))
    print("📦 Inventários:", len(inventarios))
    print("📜 Crónicas:", len(cronicas))
    print("👤 Biografias:", len(bios))
    print("🏛️ Museus:", len(museus))


if __name__ == "__main__":
    main()
