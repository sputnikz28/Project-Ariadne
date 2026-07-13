import random
from collections import Counter
from races.antigas import normalizar,gaps

def filtrar(cands):
    z=[]; eventos=[]
    for o,ch,p in cands:
        if 90<=sum(ch[0])<=170: z.append((o,ch,p)); continue
        ns=ch[0][:]
        for _ in range(100):
            s=sum(ns)
            if 90<=s<=170: break
            i=random.randrange(5); cand=[n for n in range(1,51) if n not in ns and ((s<90 and n>ns[i]) or (s>170 and n<ns[i]))] or [n for n in range(1,51) if n not in ns]; ns[i]=random.choice(cand)
        nova=normalizar(ns,ch[1]); eventos.append({'origem':o,'antes':ch,'depois':nova}); z.append((o+' [infectada]',nova,p))
    a=[]; rej=[]
    for o,ch,p in z:
        gs=gaps(ch[0]); en=100-(70 if gs.count(1)>=3 else 0)-(35 if max(gs)>25 else 0)-(40 if max(gs)<=3 else 0)+(10 if len(set(gs))>=3 else 0)
        (a if en>=50 else rej).append((o,ch,p) if en>=50 else {'origem':o,'chave':ch,'gaps':gs,'energia':en})
    return a,eventos,rej

def votar(cands):
    vn,ve=Counter(),Counter()
    for _,ch,p in cands:
        for n in ch[0]: vn[n]+=p
        for e in ch[1]: ve[e]+=p
    return {'chave':normalizar([n for n,_ in vn.most_common(5)],[e for e,_ in ve.most_common(2)]),'votos_numeros':vn.most_common(15),'votos_estrelas':ve.most_common(8)}

def corromper(cfg,ch):
    rn=[int(x) for x in cfg['CORRUPTOR']['range_numeros'].split(',')]; re=[int(x) for x in cfg['CORRUPTOR']['range_estrelas'].split(',')]; ns=[]; es=[]; an=[]; ae=[]
    for n in ch[0]: d=random.randint(*rn); x=max(1,min(50,n+d)); ns.append(x); an.append({'original':n,'deslocamento':d,'novo':x})
    for e in ch[1]: d=random.randint(*re); x=max(1,min(12,e+d)); es.append(x); ae.append({'original':e,'deslocamento':d,'novo':x})
    return {'entidade':cfg['CORRUPTOR']['nome'],'chave_original':ch,'chave_corrompida':normalizar(ns,es),'alteracoes_numeros':an,'alteracoes_estrelas':ae}
