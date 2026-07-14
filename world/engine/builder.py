from datetime import datetime
from sources.data import get_history, obter_lua, obter_jackpot


def build(cfg):
    hist,fh=get_history(cfg)
    data=cfg['MUNDO']['data']; hora=cfg['MUNDO']['hora']
    visivel=[s for s in hist if s['data']<data]
    if not visivel: visivel=hist
    lua=obter_lua(cfg); jackpot,fj=obter_jackpot(cfg,visivel)
    dt=datetime.strptime(f'{data} {hora}','%Y-%m-%d %H:%M')
    dias=['segunda','terça','quarta','quinta','sexta','sábado','domingo']
    est='inverno' if dt.month in (12,1,2) else 'primavera' if dt.month in (3,4,5) else 'verão' if dt.month in (6,7,8) else 'outono'
    pressao=0
    for s in reversed(visivel):
        if s.get('vencedores',0)==0: pressao+=1
        else: break
    world={'data':data,'hora':hora,'local':cfg['MUNDO']['local'],'pais':cfg['MUNDO']['pais'],'timezone':cfg['MUNDO']['timezone'],'dia':dias[dt.weekday()],'estacao':est,'fase_lua':lua['fase'],'idade_lua':lua['idade_dias'],'jackpot':jackpot,'pressao_destino':pressao,'fontes':{'historico':fh,'jackpot':fj,'lua':lua['fonte']}}
    return world,visivel
