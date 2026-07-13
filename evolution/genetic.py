import random
from races.antigas import criar,gerar
from artefacts.vivos import forjar,evoluir,herdar
from world.virus_malphas import infetar
from amulets.mosteiro import conceder_audiencia
from artefacts.arca import tentar_encontrar, marcar_perdido

def avaliar(ch,alvo):
    an=len(set(ch[0])&set(alvo["numeros"]));ae=len(set(ch[1])&set(alvo["estrelas"]));p=an*10+ae*5+(8 if an>=3 else 0)+(5 if ae==2 else 0)
    t="LENDA ETERNA" if (an,ae)==(5,2) else "Aquele que Viu" if an==5 else "Profeta Lunar" if an==4 else "Mestre dos Ossos" if an==3 else "Leitor dos Sinais" if an==2 else "Sussurrador do Destino" if an==1 else "Observador Celeste" if ae else "Errante das Sombras"
    return an,ae,p,t

def executar(cfg,ctx):
    tam=cfg.getint("SIMULACAO","populacao_inicial");gens=cfg.getint("SIMULACAO","geracoes");ns=cfg.getint("SIMULACAO","sobreviventes")
    pop=[criar(i+1) for i in range(tam)];contador=tam+1;todos={h.id:h for h in pop};cem=[];ress=[];resumo=[];regs=[];eventos_v=[];eventos_a=[];eventos_livros=[];encontrados_persistentes=0
    for g in range(1,gens+1):
        infetar(cfg,pop,g,eventos_v)
        encontrados_persistentes=tentar_encontrar(cfg,pop,g,encontrados_persistentes,eventos_a)
        for heroi in pop:
            conceder_audiencia(cfg,heroi,g,eventos_livros)
        alvo=ctx["historico"][(g-1)%len(ctx["historico"])]
        for h in pop:
            ch=gerar(h,ctx);an,ae,p,t=avaliar(ch,alvo);h.pontos+=p;h.titulo=t;h.chaves.append({"geracao":g,"numeros":ch[0],"estrelas":ch[1]})
            regs.append({"geracao":g,"id":h.id,"nome":h.nome,"classe":h.raca,"casa":h.casa,"numeros":ch[0],"estrelas":ch[1],"origem":"racas_antigas","virus":h.genoma.get("virus_malphas")})
        pop.sort(key=lambda x:x.pontos,reverse=True);elite=pop[:ns];eliminados=pop[ns:]
        if cfg.getboolean("ARTEFACTOS_VIVOS","ativo",fallback=True):
            evoluir(pop,cfg.getfloat("ARTEFACTOS_VIVOS","energia_por_geracao",fallback=.05))
            chance=cfg.getfloat("ARTEFACTOS_VIVOS","chance_forja",fallback=.08)
            for h in elite[:3]:
                if random.random()<chance:
                    a=forjar(h,g,cfg,ctx.get('seed'));h.amuletos.append(a);eventos_a.append({"evento":"FORJA","geracao":g,"dono":h.nome,"artefacto":a})
            if cfg.getboolean("ARTEFACTOS_VIVOS","heranca",fallback=True):
                for h in eliminados:
                    for artefacto in list(h.amuletos):
                        if random.random()<0.30:
                            marcar_perdido(artefacto,h.nome,g)
                    for origem,destino,a in herdar(h,elite):eventos_a.append({"evento":"HERANCA","geracao":g,"origem":origem,"destino":destino,"artefacto":a})
        if cfg.getboolean("CAMINHO_1000_ALMAS","ativo"):
            for h in eliminados:h.estado="CAMINHO_1000_ALMAS";h.treinos+=1;cem.append(h)
            for a in cem:a.treinos+=1
        regress=[]
        if cfg.getboolean("CAMINHO_1000_ALMAS","ativo") and g%cfg.getint("CAMINHO_1000_ALMAS","intervalo_torneio")==0 and g<gens:
            cand=[a for a in cem if a.treinos>=cfg.getint("CAMINHO_1000_ALMAS","min_treinos")];random.shuffle(cand);regress=cand[:cfg.getint("CAMINHO_1000_ALMAS","max_ressuscitados")]
            for a in regress:a.estado="RESSUSCITADO";a.raca="Renascido "+a.raca;a.pontos//=2
            ress+=regress;cem=[a for a in cem if a not in regress]
        resumo.append({"geracao":g,"melhor":elite[0].nome,"raca":elite[0].raca,"pontos":elite[0].pontos,"eliminados":len(eliminados),"ressuscitados":len(regress)})
        if g==gens:pop=elite;break
        nova=elite+regress
        while len(nova)<tam:
            p1,p2=random.sample(elite,2);f=criar(contador,g+1,[p1.id,p2.id]);contador+=1;f.raca=random.choice([p1.raca.replace("Renascido ",""),p2.raca.replace("Renascido ","")]);f.casa=random.choice([p1.casa,p2.casa]);todos[f.id]=f;nova.append(f)
        pop=nova
    return {"populacao_final":pop,"todos":todos,"cemiterio":cem,"ressuscitados":ress,"resumo":resumo,"registos":regs,"eventos_virus":eventos_v,"eventos_artefactos":eventos_a,"eventos_livros":eventos_livros}
