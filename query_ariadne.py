
import argparse
import json
from library.ariadne.motor import Ariadne


def main():
    parser = argparse.ArgumentParser(description="Consulta a consciência da Biblioteca Eterna.")
    sub = parser.add_subparsers(dest="comando", required=True)

    lua = sub.add_parser("lua")
    lua.add_argument("fase")

    numero = sub.add_parser("numero")
    numero.add_argument("valor", type=int)

    duplas = sub.add_parser("duplas")
    duplas.add_argument("--limite", type=int, default=10)

    triplas = sub.add_parser("triplas")
    triplas.add_argument("--limite", type=int, default=10)

    estado = sub.add_parser("pergaminho")
    estado.add_argument("numero", type=int)

    args = parser.parse_args()
    ariadne = Ariadne()

    if args.comando == "lua":
        resposta = ariadne.procurar_lua(args.fase)
    elif args.comando == "numero":
        resposta = ariadne.numero(args.valor)
    elif args.comando == "duplas":
        resposta = ariadne.duplas(args.limite)
    elif args.comando == "triplas":
        resposta = ariadne.triplas(args.limite)
    else:
        resposta = ariadne.estado_pergaminho(args.numero)

    print(json.dumps(resposta, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
