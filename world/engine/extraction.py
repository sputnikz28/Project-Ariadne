from datetime import datetime, timedelta
import random


def simulate_draw(cfg, world):
    if not cfg.getboolean('EXTRACAO', 'ativo', fallback=True):
        return {'ativo': False, 'inicio_oficial': None, 'atraso_arranque': 0.0, 'eventos': []}

    inicio = datetime.strptime(
        f"{world['data']} {cfg.get('EXTRACAO', 'hora_oficial', fallback='20:00:00')}",
        '%Y-%m-%d %H:%M:%S'
    )
    delay = random.uniform(
        cfg.getfloat('EXTRACAO', 'delay_arranque_min', fallback=2.0),
        cfg.getfloat('EXTRACAO', 'delay_arranque_max', fallback=15.0),
    )
    media = cfg.getfloat('EXTRACAO', 'tempo_medio_bola', fallback=7.5)
    variacao = cfg.getfloat('EXTRACAO', 'variacao_segundos', fallback=2.0)
    instante = inicio + timedelta(seconds=delay)
    events = []

    for indice in range(1, 8):
        events.append({
            'ordem': indice,
            'tipo': 'numero' if indice <= 5 else 'estrela',
            'instante_iso': instante.isoformat(timespec='milliseconds'),
            'hora': instante.strftime('%H:%M:%S.%f')[:-3],
            'segundo': instante.second,
            'milissegundo': instante.microsecond // 1000,
            'segundos_desde_inicio': round((instante - inicio).total_seconds(), 3),
        })
        passo = max(0.5, random.gauss(media, variacao))
        instante += timedelta(seconds=passo)

    return {
        'ativo': True,
        'inicio_oficial': inicio.isoformat(),
        'atraso_arranque': round(delay, 3),
        'eventos': events,
    }
