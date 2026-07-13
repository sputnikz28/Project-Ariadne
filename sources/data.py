import json
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen


def ler_json(path, default):
    p = Path(path)
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        return default


def guardar_json(path, data):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


def obter_historico(cfg):
    url = cfg.get('FONTES','euromilhoes_url',fallback='').strip()
    if cfg.getboolean('FONTES','usar_api_euromilhoes',fallback=True) and url:
        try:
            req=Request(url,headers={'User-Agent':'OraculosGeneticos/4.0'})
            with urlopen(req,timeout=cfg.getint('FONTES','timeout_segundos',fallback=3)) as r:
                data=json.loads(r.read().decode())
            if isinstance(data,dict): data=data.get('draws') or data.get('results') or data.get('data') or []
            out=[]
            for x in data:
                nums=x.get('numbers') or x.get('numeros'); stars=x.get('stars') or x.get('estrelas'); date=x.get('date') or x.get('data')
                if nums and stars and date:
                    out.append({'data':str(date)[:10],'numeros':sorted(map(int,nums))[:5],'estrelas':sorted(map(int,stars))[:2],'jackpot':int(x.get('jackpot') or 0),'vencedores':int(x.get('winners') or 0)})
            out.sort(key=lambda z:z['data'])
            if out:
                guardar_json('data/historico_cache.json',out)
                return out,'api_euromilhoes'
        except Exception:
            pass
    return ler_json('data/historico_cache.json',[]),'cache_historico'


def obter_lua(cfg):
    data=cfg['MUNDO']['data']; hora=cfg['MUNDO']['hora']
    ref=datetime(2000,1,6,18,14); dt=datetime.strptime(f'{data} {hora}','%Y-%m-%d %H:%M')
    idade=((dt-ref).total_seconds()/86400)%29.53058867
    if idade<1.5 or idade>28: fase='nova'
    elif idade<7.4: fase='crescente'
    elif idade<9.4: fase='quarto crescente'
    elif idade<14.8: fase='gibosa crescente'
    elif idade<16.8: fase='cheia'
    elif idade<22.1: fase='gibosa minguante'
    elif idade<24.1: fase='quarto minguante'
    else: fase='minguante'
    return {'fase':fase,'idade_dias':round(idade,2),'fonte':'calculo_local_fallback'}


def obter_jackpot(cfg,historico):
    if historico and historico[-1].get('jackpot'):
        return historico[-1]['jackpot'],'historico/cache'
    return 0,'indisponivel'
