
import json
import re
import shutil
import subprocess
import sys
import time
from configparser import ConfigParser
from configuration import load_config
from datetime import datetime
from pathlib import Path

from scribes.arquivistas import (
    inventariar_era,
    create_biographies,
    atualizar_atlas,
    create_museum,
    write_chronicle,
    summary_inventory,
)


def extrair(pattern, texto, padrao=None):
    m = re.search(pattern, texto)
    return m.group(1).strip() if m else padrao


def parse_key(texto):
    try:
        return json.loads(texto.replace("(", "[").replace(")", "]").replace("'", '"'))
    except Exception:
        return texto


def main():
    cfg = load_config("config.txt")
    rodadas = cfg.getint("CAMPANHA", "numero_de_rodadas", fallback=5)
    name = cfg.get("UNIVERSO", "nome", fallback="Crónicas das Eras")
    pausa = cfg.getint("CAMPANHA", "pausa_entre_rodadas_ms", fallback=0) / 1000.0
    max_bios = cfg.getint("ESCRIBAS_V6", "max_biografias_por_rodada", fallback=12)

    campanha_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    pasta = Path("campanhas") / f"campanha_{campanha_id}"
    pasta.mkdir(parents=True, exist_ok=True)

    resumos = []
    for era in range(1, rodadas + 1):
        antes_relatorios = set(Path("reports/generated").glob("relatorio_*.txt"))
        proc = subprocess.run(
            [sys.executable, "main.py"],
            capture_output=True,
            text=True,
            timeout=360,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"Falha na era {era}:\n{proc.stderr}")

        stdout = proc.stdout
        novos = sorted(set(Path("reports/generated").glob("relatorio_*.txt")) - antes_relatorios)
        relatorio = novos[-1] if novos else None

        resumo = {
            "era": era,
            "seed": extrair(r"Semente do universo:\s*(\d+)", stdout),
            "energia_celeste": extrair(r"Energia celeste:\s*([0-9.]+)", stdout),
            "almas": extrair(r"Almas no ritual:\s*(\d+)", stdout),
            "individuos": int(extrair(r"Indivíduos únicos:\s*(\d+)", stdout, "0")),
            "chaves_antigas": int(extrair(r"Chaves das raças antigas:\s*(\d+)", stdout, "0")),
            "magos_negros": int(extrair(r"Magos Negros:\s*(\d+)", stdout, "0")),
            "missoes_elficas": int(extrair(r"Missões Élficas:\s*(\d+)", stdout, "0")),
            "esqueletos": int(extrair(r"Esqueletos:\s*(\d+)", stdout, "0")),
            "invocacoes_sombrias": int(extrair(r"Invocações sombrias:\s*(\d+)", stdout, "0")),
            "chave_original": parse_key(extrair(r"Chave original:\s*(.+)", stdout)),
            "chave_corrompida": parse_key(extrair(r"Chave corrompida:\s*(.+)", stdout)),
            "relatorio": str(relatorio) if relatorio else None,
        }

        inventory = inventariar_era(era, resumo)
        biografias = create_biographies(era, max_bios)
        atlas = atualizar_atlas(era, inventory)
        museu = create_museum(era, inventory)
        chronicle = write_chronicle(era, inventory)

        resumo["inventario"] = f"escribas/inventarios/inventario_era_{era:03d}.json"
        resumo["cronica"] = str(chronicle)
        resumo["biografias"] = biografias
        resumo["inventario_resumido"] = summary_inventory(inventory)
        resumos.append(resumo)

        if relatorio and relatorio.exists():
            shutil.copy2(relatorio, pasta / f"relatorio_era_{era:03d}.txt")
        shutil.copy2(chronicle, pasta / f"cronica_era_{era:03d}.txt")

        print(f"Era {era}/{rodadas} concluída — Conselho: {resumo['chave_original']}")
        if pausa:
            time.sleep(pausa)

    numbers = {}
    stars = {}
    for r in resumos:
        key = r["chave_original"]
        if isinstance(key, list) and len(key) == 2:
            for n in key[0]:
                numbers[n] = numbers.get(n, 0) + 1
            for e in key[1]:
                stars[e] = stars.get(e, 0) + 1

    conselho_dos_conselhos = {
        "numeros": [n for n, _ in sorted(numbers.items(), key=lambda x: (-x[1], x[0]))[:5]],
        "estrelas": [e for e, _ in sorted(stars.items(), key=lambda x: (-x[1], x[0]))[:2]],
    }

    campanha = {
        "id": campanha_id,
        "nome": name,
        "rodadas": rodadas,
        "criada_em": datetime.now().isoformat(timespec="seconds"),
        "eras": resumos,
        "conselho_dos_conselhos": conselho_dos_conselhos,
    }
    (pasta / "campanha.json").write_text(
        json.dumps(campanha, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    linhas = [
        "╔════════════════════════════════════════════════════╗",
        "         🌌 V6 — CRÓNICAS DAS CINCO ERAS",
        "╚════════════════════════════════════════════════════╝",
        "",
        f"Campanha: {name}",
        f"Rodadas: {rodadas}",
        "",
    ]
    for r in resumos:
        linhas += [
            f"ERA {r['era']}",
            f"  Seed: {r['seed']}",
            f"  Conselho: {r['chave_original']}",
            f"  Linha corrompida: {r['chave_corrompida']}",
            f"  Indivíduos: {r['individuos']}",
            f"  Artefactos: {r['inventario_resumido']['artefactos']}",
            f"  Livros: {r['inventario_resumido']['livros']}",
            f"  Lendas: {r['inventario_resumido']['lendas']}",
            "",
        ]
    linhas += [
        "🏛️ CONSELHO DOS CONSELHOS",
        f"Números: {conselho_dos_conselhos['numeros']}",
        f"Estrelas: {conselho_dos_conselhos['estrelas']}",
        "",
        "Os Escribas selaram as cinco eras no Atlas do Universo.",
    ]
    relatorio_campanha = pasta / "relatorio_campanha_v6.txt"
    relatorio_campanha.write_text("\n".join(linhas), encoding="utf-8")

    print("\nCampanha V6 concluída.")
    print("Relatório:", relatorio_campanha)
    print("Conselho dos Conselhos:", conselho_dos_conselhos)


if __name__ == "__main__":
    main()
