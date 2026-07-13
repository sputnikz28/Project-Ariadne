
import json
from pathlib import Path
from races.vampires.lineages import create_vampires
from races.gargoyles.lineages import create_gargoyles
from races.treefolks.investigator import investigar_lua_cheia
from library.ariadne.engine import Ariadne


def fmt(key):
    return f"{' - '.join(map(str, key[0]))} | Estrelas: {' - '.join(map(str, key[1]))}"


def main():
    ariadne = Ariadne()
    vampiros = create_vampires()
    gargulas = create_gargoyles()
    treefolk = investigar_lua_cheia()

    linhas = [
        "╔════════════════════════════════════════════════════╗",
        "           📖 V7 — BIBLIOTECA ETERNA",
        "╚════════════════════════════════════════════════════╝",
        "",
        f"Pergaminhos catalogados: {len(ariadne.scrolls)}",
        "",
        "🧛 VAMPIROS — MESTRES DAS TRIPLAS",
    ]
    for v in vampiros:
        linhas += [
            f"{v['nome']} | Linhagem {v['linhagem']}",
            f"Tripla: {v['tripla']}",
            f"Chave: {fmt(v['chave'])}",
            "",
        ]

    linhas.append("🗿 GÁRGULAS — GUARDIÃS DAS DUPLAS")
    for g in gargulas:
        linhas += [
            f"{g['nome']} | Linhagem {g['linhagem']}",
            f"Dupla: {g['dupla']}",
            f"Chave: {fmt(g['chave'])}",
            "",
        ]

    linhas += [
        "🌳 TREEFOLK INVESTIGADOR",
        f"Pergaminhos de Lua Cheia: {treefolk['consulta']['scrolls_encontrados']}",
        f"Confiança: {treefolk['confianca']}",
        f"Fantasma estatístico: {treefolk['fantasma_estatistico']}",
        f"Conclusão: {treefolk['conclusao']}",
        "",
        "Ariadne recorda: padrões históricos não aumentam a probabilidade matemática do sorteio.",
    ]

    out = Path("reports/generated/relatorio_v7_biblioteca_eterna.txt")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(linhas), encoding="utf-8")
    print("\n".join(linhas))
    print("\nRelatório:", out)


if __name__ == "__main__":
    main()
