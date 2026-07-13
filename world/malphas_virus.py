import random
TIPOS=["Semente da Corrupção","Espelho Negro","Raiz Negra","Lua Vermelha","Praga da Ganância","Paradoxo Temporal"]

def infetar(cfg,pop,g,events):
    if not cfg.getboolean("VIRUS_MALPHAS","ativo",fallback=False):return
    chance=cfg.getfloat("VIRUS_MALPHAS","chance_infeccao",fallback=.04);oculto=cfg.getboolean("VIRUS_MALPHAS","ocultar_portador",fallback=True);bonus=cfg.getfloat("VIRUS_MALPHAS","bonus_score_infectado",fallback=1.2)
    for h in pop:
        if h.genoma.get("virus_malphas"):continue
        if random.random()<chance:
            v=random.choice(TIPOS);h.genoma["virus_malphas"]=v;h.genoma["infeccao_oculta"]=oculto;h.genoma["geracao_infeccao"]=g;h.pontos=int(h.pontos*bonus)
            events.append({"geracao":g,"id":h.id,"nome":h.name,"raca":h.raca,"virus":v,"oculto":oculto})

def choose_carrier(cfg,herois):
    inf=[h for h in herois if h.genoma.get("virus_malphas")]
    if not inf:return None
    if random.random()>cfg.getfloat("VIRUS_MALPHAS","chance_revelacao_conselho",fallback=.75):return None
    return max(inf,key=lambda h:h.pontos)
