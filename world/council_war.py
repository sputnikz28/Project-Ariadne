import random
from races.antigas import normalizar

def corrupcao(ch,portador):
    ns=[];es=[];an=[];ae=[]
    for n in ch[0]:
        d=random.randint(-3,3);x=max(1,min(50,n+d));ns.append(x);an.append({"original":n,"deslocamento":d,"novo":x})
    for e in ch[1]:
        d=random.randint(-1,1);x=max(1,min(12,e+d));es.append(x);ae.append({"original":e,"deslocamento":d,"novo":x})
    return {"entidade":f"{portador.nome}, Quebra-Conselhos","portador_original":portador.nome,"virus":portador.genoma.get("virus_malphas"),"chave_original":ch,"chave_corrompida":normalizar(ns,es),"alteracoes_numeros":an,"alteracoes_estrelas":ae,"origem_corrupcao":"portador_interno"}

def resolver(cfg,ch,portador,ritual):
    if not cfg.getboolean("GUERRA_CONSELHO","ativo",fallback=False):return None
    if portador is None:return {"houve_guerra":False,"resultado":"Nenhum portador infetado chegou ao Conselho.","corrupcao":None,"energia_gasta":0.0}
    energia=float(ritual.get("energia_total",0));custo=cfg.getfloat("GUERRA_CONSELHO","custo_purificacao",fallback=1.5);base=cfg.getfloat("GUERRA_CONSELHO","chance_base_deteccao",fallback=.35)
    bonus_f=.15 if cfg.getboolean("GUERRA_CONSELHO","usar_fenrir",fallback=True) else 0
    bonus_c=min(.35,energia/20) if cfg.getboolean("GUERRA_CONSELHO","usar_clerigos",fallback=True) else 0
    chance=min(.95,base+bonus_f+bonus_c);purificado=energia>=custo and random.random()<chance
    if purificado:return {"houve_guerra":True,"resultado":"Conselho purificado pelos Clérigos e por Fenrir.","portador":portador.nome,"virus":portador.genoma.get("virus_malphas"),"corrupcao":None,"energia_gasta":custo,"chance_purificacao":round(chance,3)}
    return {"houve_guerra":True,"resultado":"O portador revelou-se e corrompeu a chave final.","portador":portador.nome,"virus":portador.genoma.get("virus_malphas"),"corrupcao":corrupcao(ch,portador),"energia_gasta":0.0,"chance_purificacao":round(chance,3)}
