
import json
from pathlib import Path


def ler(path, padrao):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return padrao


def main():
    grimorio = ler("esquadrao_negro/biblioteca_sombria/grimorio_negro.json", {})
    ordem = ler("ordem_elfica/estado_ordem.json", {})
    lendas = ler("lendas/livro_personagens_lendarias.json", {"personagens": []})
    reflexos = list(Path("esquadrao_negro/biblioteca_sombria/reflexos_corrompidos").glob("*.json"))
    roubadas = list(Path("esquadrao_negro/biblioteca_sombria/reliquias_roubadas").glob("*.json"))
    missoes = list(Path("ordem_elfica/arquivo_missoes").glob("*.json"))

    print("🌑 Grimório Negro:", grimorio)
    print("📕 Reflexos sombrios:", len(reflexos))
    print("💍 Relíquias roubadas:", len(roubadas))
    print("🥷 Estado da Ordem:", ordem)
    print("📜 Missões guardadas:", len(missoes))
    print("📖 Lendas:", len(lendas.get("personagens", [])))


if __name__ == "__main__":
    main()
