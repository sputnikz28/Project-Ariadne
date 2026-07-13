
import argparse
from pathlib import Path
from amulets.persistencia import ler_json, guardar_json


def main():
    parser=argparse.ArgumentParser(description="Regista o resultado real num Livro das Extrações por Cumprir.")
    parser.add_argument("ficheiro",help="Ficheiro JSON em amuletos/future_draws/")
    parser.add_argument("--numeros",nargs=5,type=int,required=True)
    parser.add_argument("--estrelas",nargs=2,type=int,required=True)
    parser.add_argument("--fontes",nargs="*",default=[])
    args=parser.parse_args()

    path=Path(args.ficheiro)
    reg=ler_json(path,{})
    if not reg:
        raise SystemExit("Livro não encontrado ou inválido.")
    reg["estado"]="extraida"
    reg["chave_real"]={"numeros":sorted(args.numeros),"estrelas":sorted(args.estrelas)}
    reg["confirmada_por"]=args.fontes
    guardar_json(path,reg)
    print("Extração selada:",path)


if __name__=="__main__":
    main()
