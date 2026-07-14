
from configparser import ConfigParser
from world.engine.builder import build
from amulets.books import synchronize_sources, build_books


def main():
    cfg=ConfigParser()
    cfg.read("config.txt",encoding="utf-8")
    world,history=build(cfg)
    fontes=synchronize_sources(cfg)
    resumo=build_books(cfg,history,world)
    print("Fontes:",fontes)
    print("Livros:",resumo["livros_criados"])
    print("Extrações:",resumo["total_extracoes"])


if __name__=="__main__":
    main()
