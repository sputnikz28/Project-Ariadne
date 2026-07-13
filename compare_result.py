
import argparse
import json
from pathlib import Path

from legends.registro import registar_lendas


def titulo(n, e):
    if (n, e) == (5, 2): return "LENDA ETERNA"
    if n == 5: return "Aquele que Viu"
    if n == 4: return "Profeta Lunar"
    if n == 3 and e == 2: return "ORÁCULO DE OURO"
    if n == 3: return "Mestre dos Ossos"
    if n == 2: return "Leitor dos Sinais"
    if n == 1: return "Sussurrador do Destino"
    if e: return "Observador Celeste"
    return "Errante das Sombras"


def main():
    parser = argparse.ArgumentParser(
        description="Compara todo o Arquivo do Destino e regista as novas lendas."
    )
    parser.add_argument("--numeros", nargs=5, type=int, required=True)
    parser.add_argument("--estrelas", nargs=2, type=int, required=True)
    parser.add_argument("--top", type=int, default=50)
    args = parser.parse_args()

    arquivo = json.loads(Path("data/arquivo_destino.json").read_text(encoding="utf-8"))
    alvo_n = set(args.numeros)
    alvo_e = set(args.estrelas)
    resultados = []

    for registo in arquivo:
        acertos_n = len(set(registo["numeros"]) & alvo_n)
        acertos_e = len(set(registo["estrelas"]) & alvo_e)
        pontos = acertos_n * 10 + acertos_e * 5 + (8 if acertos_n >= 3 else 0) + (5 if acertos_e == 2 else 0)
        resultados.append({
            **registo,
            "acertos_numeros": acertos_n,
            "acertos_estrelas": acertos_e,
            "pontos_resultado": pontos,
            "titulo_resultado": titulo(acertos_n, acertos_e),
        })

    resultados.sort(
        key=lambda x: (x["acertos_numeros"], x["acertos_estrelas"], x["pontos_resultado"]),
        reverse=True,
    )

    chave_real = {
        "numeros": sorted(args.numeros),
        "estrelas": sorted(args.estrelas),
    }
    novas_lendas = registar_lendas(resultados, chave_real, min_numeros=3, min_estrelas=2)

    linhas = [
        "╔════════════════════════════════════════════════════╗",
        "       ⏳ JULGAMENTO PÓS-SORTEIO DO DESTINO",
        "╚════════════════════════════════════════════════════╝",
        "",
        f"Chave real: {' - '.join(map(str, chave_real['numeros']))} | Estrelas: {' - '.join(map(str, chave_real['estrelas']))}",
        f"Registos pesquisados: {len(arquivo)}",
        f"Novas lendas registadas: {len(novas_lendas)}",
        "",
    ]

    if novas_lendas:
        linhas.append("📖 NOVAS PERSONAGENS LENDÁRIAS")
        for lenda in novas_lendas:
            linhas.append(
                f"- {lenda['nome']} | {lenda['classe']} | {lenda['grau']} | {lenda['feito']}"
            )
        linhas.append("")

    for i, r in enumerate(resultados[:args.top], 1):
        linhas.append(
            f"{i:>3}. Geração {r['geracao']} | {r['nome']} | {r['classe']} | "
            f"{r['numeros']} ⭐ {r['estrelas']} | "
            f"{r['acertos_numeros']}N + {r['acertos_estrelas']}E | {r['titulo_resultado']}"
        )

    saida = Path("reports/generated/comparacao_pos_sorteio.txt")
    saida.write_text("\n".join(linhas), encoding="utf-8")
    print("\n".join(linhas))
    print("\nGuardado em:", saida)


if __name__ == "__main__":
    main()
