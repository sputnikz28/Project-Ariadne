
import argparse
import json
from library.ariadne.engine import Ariadne


def main():
    parser = argparse.ArgumentParser(description="Consulta a consciência da Biblioteca Eterna.")
    sub = parser.add_subparsers(dest="comando", required=True)

    lua = sub.add_parser("lua")
    lua.add_argument("fase")

    numero = sub.add_parser("numero")
    numero.add_argument("valor", type=int)

    pairs = sub.add_parser("duplas")
    pairs.add_argument("--limite", type=int, default=10)

    triples = sub.add_parser("triplas")
    triples.add_argument("--limite", type=int, default=10)

    estado = sub.add_parser("pergaminho")
    estado.add_argument("numero", type=int)

    args = parser.parse_args()
    ariadne = Ariadne()

    if args.comando == "lua":
        resposta = ariadne.search_moon(args.fase)
    elif args.comando == "numero":
        resposta = ariadne.numero(args.valor)
    elif args.comando == "duplas":
        resposta = ariadne.pairs(args.limite)
    elif args.comando == "triplas":
        resposta = ariadne.triples(args.limite)
    else:
        resposta = ariadne.scroll_state(args.numero)

    print(json.dumps(resposta, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
