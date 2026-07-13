
import json
from pathlib import Path
from vampiros.linhagens import criar_vampiros
from gargulas.linhagens import criar_gargulas
from treefolks.investigador import investigar_lua_cheia
from biblioteca.ariadne.motor import Ariadne


def fmt(chave):
    return f"{' - '.join(map(str, chave[0]))} | Estrelas: {' - '.join(map(str, chave[1]))}"


def main():
    ariadne = Ariadne()
    vampiros = criar_vampiros()
    gargulas = criar_gargulas()
    treefolk = investigar_lua_cheia()

    linhas = [
        "╔════════════════════════════════════════════════════╗",
        "           📖 V7 — BIBLIOTECA ETERNA",
        "╚════════════════════════════════════════════════════╝",
        "",
        f"Pergaminhos catalogados: {len(ariadne.pergaminhos)}",
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
        f"Pergaminhos de Lua Cheia: {treefolk['consulta']['pergaminhos_encontrados']}",
        f"Confiança: {treefolk['confianca']}",
        f"Fantasma estatístico: {treefolk['fantasma_estatistico']}",
        f"Conclusão: {treefolk['conclusao']}",
        "",
        "Ariadne recorda: padrões históricos não aumentam a probabilidade matemática do sorteio.",
    ]

    out = Path("relatorios/gerados/relatorio_v7_biblioteca_eterna.txt")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(linhas), encoding="utf-8")
    print("\n".join(linhas))
    print("\nRelatório:", out)


if __name__ == "__main__":
    main()
