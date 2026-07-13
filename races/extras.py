import random,heapq
from itertools import combinations
from collections import Counter
from races.antigas import normalizar,gaps


def anoes(cfg,ctx):
    out=[]; est=ctx['estatisticas']; nomes=['Barbas de Ferro','Cristal Azul','Forja Negra']
    for nome in nomes[:cfg.getint('ANOES','numero_clas')]:
        pool=list(dict.fromkeys(est['quentes'][:8]+est['frios'][:5]+ctx['historico'][-1]['numeros']))
        while len(pool)<20:
            n=random.randint(1,50)
            if n not in pool: pool.append(n)
        ep=list(dict.fromkeys(est['estrelas_quentes'][:2]+est['estrelas_frias'][:2]+ctx['historico'][-1]['estrelas']))
        while len(ep)<4:
            e=random.randint(1,12)
            if e not in ep: ep.append(e)
        cart=[]; cnums=list(combinations(sorted(pool[:20]),5)); random.shuffle(cnums)
        for ns in cnums:
            if 85<=sum(ns)<=190:
                for es in combinations(sorted(ep[:4]),2):
                    cart.append(normalizar(list(ns),list(es)))
                    if len(cart)>=cfg.getint('ANOES','chaves_por_cla'): break
            if len(cart)>=cfg.getint('ANOES','chaves_por_cla'): break
        out.append({'nome':nome,'lider':'Rei '+random.choice(['Thorin','Borin','Dain']),'pool':sorted(pool[:20]),'estrelas_pool':sorted(ep[:4]),'carteira':cart})
    return out


def fadas(cfg,ctx):
    if not cfg.getboolean('FADAS','ativo'): return []
    nq=[int(x) for x in cfg['FADAS']['numeros_quotidiano'].split(',')]; eq=[int(x) for x in cfg['FADAS']['estrelas_quotidiano'].split(',')]; est=ctx['estatisticas']; out=[]
    for i in range(cfg.getint('FADAS','quantidade')):
        rank=[]
        for n in range(1,51):
            sc=.4*(1-abs(n-25.5)/25.5)+.25*est['atraso_norm'][n]+.2*est['freq_norm'][n]+.15*(n in nq); rank.append((n,max(.001,sc)))
        nums=[n for n,_ in rank]; pesos=[s for _,s in rank]; chave=None
        for _ in range(2000):
            c=list(dict.fromkeys(random.choices(nums,weights=pesos,k=12)))
            if len(c)<5: continue
            ns=sorted(random.sample(c,5)); pares=sum(n%2==0 for n in ns)
            if any(n<=10 for n in ns) and set(ns)&set(est['quentes']) and set(ns)&set(est['frios']) and 100<=sum(ns)<=170 and pares in (2,3): chave=ns; break
        if chave is None: chave=sorted(random.sample(range(1,51),5))
        re=sorted(((e,.5*est['freq_est_norm'][e]+.35*est['atraso_est_norm'][e]+.15*(e in eq)) for e in range(1,13)),key=lambda x:x[1],reverse=True)
        out.append({'nome':f'Lunélia-{i+1}','tipo':'Fada','chave':normalizar(chave,[e for e,_ in re[:2]])})
    return out


def fitness(ch,est):
    ns,es=ch; s=sum(ns); gs=gaps(ns); p=30 if 110<=s<=160 else 15 if 90<=s<=170 else -20; p+=20 if sum(n%2==0 for n in ns) in (2,3) else 0; p+=20 if sum(n<=25 for n in ns) in (2,3) else 0; p-=35 if gs.count(1)>=3 else 0; p+=15 if len(set(gs))>=3 else 0; p-=15 if max(gs)>25 else 0; p+=2*len(set(ns)&set(est['quentes']))+len(set(ns)&set(est['frios'])); return p


def melforks(cfg,ctx):
    if not cfg.getboolean('MELFORKS','ativo'): return []
    est=ctx['estatisticas']; tam=cfg.getint('MELFORKS','populacao_chaves'); pop=[normalizar(random.sample(range(1,51),5),random.sample(range(1,13),2)) for _ in range(tam)]
    for _ in range(cfg.getint('MELFORKS','geracoes_chaves')):
        av=sorted(((fitness(c,est),c) for c in pop),key=lambda x:x[0],reverse=True); elite=[c for _,c in av[:cfg.getint('MELFORKS','elite')]]; nova=elite[:]
        while len(nova)<tam:
            a,b=random.sample(elite,2); pn=list(dict.fromkeys(a[0]+b[0])); pe=list(dict.fromkeys(a[1]+b[1])); nova.append(normalizar(random.sample(pn,5),random.sample(pe,2)))
        pop=nova
    top=sorted(((fitness(c,est),c) for c in pop),key=lambda x:x[0],reverse=True)[:cfg.getint('MELFORKS','representantes')]
    return [{'nome':f'Clérigo-{i+1}','tipo':'Melfork','fitness':f,'chave':c} for i,(f,c) in enumerate(top)]


def lobisomens(cfg,ctx):
    fase=ctx['mundo']['fase_lua']; ativo=cfg.getboolean('LOBISOMENS','ativo') and (not cfg.getboolean('LOBISOMENS','apenas_semana_lua_cheia') or fase in {'gibosa crescente','cheia','gibosa minguante'})
    if not ativo: return {'ativo':False,'simulacoes':0,'finalistas':[]}
    heap=[]; sims=cfg.getint('LOBISOMENS','simulacoes_monte_carlo'); reps=cfg.getint('LOBISOMENS','representantes')
    for _ in range(sims):
        c=(sorted(random.sample(range(1,51),5)),sorted(random.sample(range(1,13),2))); f=fitness(c,ctx['estatisticas']); r=(f,tuple(c[0]),tuple(c[1]))
        if len(heap)<100: heapq.heappush(heap,r)
        elif f>heap[0][0]: heapq.heapreplace(heap,r)
    top=sorted(heap,reverse=True)[:reps]
    return {'ativo':True,'simulacoes':sims,'finalistas':[{'nome':f'Fenrir-{i+1}','tipo':'Lobisomem','fitness':f,'chave':normalizar(list(n),list(e))} for i,(f,n,e) in enumerate(top)]}


def treefolks(cfg,ctx):
    if not cfg.getboolean('TREEFOLKS','ativo'): return []
    est=ctx['estatisticas']; out=[]
    for i in range(cfg.getint('TREEFOLKS','quantidade')):
        tr=round(random.uniform(.7,.95),3); te=round(random.uniform(.08,.3),3); fa=round(tr-te,3); rn=sorted(((n,.45*est['freq_norm'][n]+.35*est['atraso_norm'][n]+.2*random.random()) for n in range(1,51)),key=lambda x:x[1],reverse=True); re=sorted(((e,.55*est['freq_est_norm'][e]+.3*est['atraso_est_norm'][e]+.15*random.random()) for e in range(1,13)),key=lambda x:x[1],reverse=True)
        out.append({'nome':f'Raiz-{i+1}','tipo':'Treefolk','modelo':random.choice(['Random Forest','Rede Neural','LSTM','Bayesiano']),'treino':tr,'teste':te,'fantasma':fa,'peso':max(.02,1-fa),'chave':normalizar([n for n,_ in rn[:5]],[e for e,_ in re[:2]])})
    return out


def superiores(ctx):
    est=ctx['estatisticas']; vis=[]
    for i in range(2): vis.append({'nome':f'Mago-{i+1}','tipo':'Mago','chave':normalizar(random.sample([n for n,_ in est['atrasados'][:5]],2)+random.sample(est['quentes'],3),random.sample(est['estrelas_quentes'],2))})
    for i in range(2): vis.append({'nome':f'Druida-{i+1}','tipo':'Druida','chave':normalizar(random.sample(est['quentes'],5),random.sample(est['estrelas_quentes'],2))})
    for i in range(2): vis.append({'nome':f'Djinn-{i+1}','tipo':'Djinn','chave':normalizar([max(1,min(50,n+random.choice([-5,-3,-1,1,3,5]))) for n in ctx['historico'][-1]['numeros']],[max(1,min(12,e+random.choice([-2,-1,1,2]))) for e in ctx['historico'][-1]['estrelas']])})
    vn,ve=Counter(),Counter()
    for v in vis: vn.update(v['chave'][0]); ve.update(v['chave'][1])
    return vis,{'nome':'Aion','tipo':'Deus','chave':normalizar([n for n,_ in vn.most_common(5)],[e for e,_ in ve.most_common(2)])}
