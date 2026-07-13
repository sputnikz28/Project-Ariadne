
from configparser import ConfigParser
from world.construtor import construir
from amulets.biblioteca import sincronizar_fontes, construir_livros


def main():
    cfg=ConfigParser()
    cfg.read("config.txt",encoding="utf-8")
    mundo,historico=construir(cfg)
    fontes=sincronizar_fontes(cfg)
    resumo=construir_livros(cfg,historico,mundo)
    print("Fontes:",fontes)
    print("Livros:",resumo["livros_criados"])
    print("Extrações:",resumo["total_extracoes"])


if __name__=="__main__":
    main()
