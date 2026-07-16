from collections import Counter

def calculate(hist):
    fn,fe=Counter(),Counter(); un={n:None for n in range(1,51)}; ue={e:None for e in range(1,13)}; somas=[]
    for i,s in enumerate(hist):
        fn.update(s['numeros']); fe.update(s['estrelas']); somas.append(sum(s['numeros']))
        for n in s['numeros']: un[n]=i
        for e in s['estrelas']: ue[e]=i
    on=[n for n,_ in fn.most_common()]+[n for n in range(1,51) if n not in fn]
    oe=[e for e,_ in fe.most_common()]+[e for e in range(1,13) if e not in fe]
    an={n:len(hist) if un[n] is None else len(hist)-1-un[n] for n in range(1,51)}
    ae={e:len(hist) if ue[e] is None else len(hist)-1-ue[e] for e in range(1,13)}
    mfn=max(fn.values()) if fn else 1; mfe=max(fe.values()) if fe else 1; man=max(an.values()) or 1; mae=max(ae.values()) or 1
    return {'quentes':on[:12],'frios':list(reversed(on[-12:])),'estrelas_quentes':oe[:5],'estrelas_frias':list(reversed(oe[-5:])),'atrasados':sorted(an.items(),key=lambda x:x[1],reverse=True)[:12],'freq_norm':{n:fn.get(n,0)/mfn for n in range(1,51)},'atraso_norm':{n:an[n]/man for n in range(1,51)},'freq_est_norm':{e:fe.get(e,0)/mfe for e in range(1,13)},'atraso_est_norm':{e:ae[e]/mae for e in range(1,13)},'media_soma':sum(somas)/len(somas)}
