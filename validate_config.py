from configuration import carregar_config

def main():
    cfg=carregar_config("config.txt")
    rodadas=cfg.getint("CAMPANHA","numero_de_rodadas",fallback=5)
    if rodadas<1: raise SystemExit("numero_de_rodadas deve ser pelo menos 1")
    if rodadas>10000: raise SystemExit("máximo de segurança: 10000")
    print("Configuração válida.")
    print("Mundo:",cfg.get("UNIVERSO","nome",fallback="Sem nome"))
    print("Rodadas:",rodadas)
    print("Ficheiro:",cfg.get("MUNDO","ficheiro_carregado",fallback=""))

if __name__=="__main__": main()
