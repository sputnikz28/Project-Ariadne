
import json
from pathlib import Path


def ler(path, padrao):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return padrao


def main():
    grimorio = ler("black_squad/dark_library/grimorio_negro.json", {})
    ordem = ler("elven_order/estado_ordem.json", {})
    lendas = ler("lendas/livro_personagens_lendarias.json", {"personagens": []})
    reflexos = list(Path("black_squad/dark_library/corrupted_reflections").glob("*.json"))
    roubadas = list(Path("black_squad/dark_library/stolen_relics").glob("*.json"))
    missoes = list(Path("elven_order/mission_archive").glob("*.json"))

    print("🌑 Grimório Negro:", grimorio)
    print("📕 Reflexos sombrios:", len(reflexos))
    print("💍 Relíquias roubadas:", len(roubadas))
    print("🥷 Estado da Ordem:", ordem)
    print("📜 Missões guardadas:", len(missoes))
    print("📖 Lendas:", len(lendas.get("personagens", [])))


if __name__ == "__main__":
    main()
