from core.services.combinations import normalize_candidate


def generate_temporal_key(name, extraction, world, rng, index=0):
    if not extraction.get('eventos'):
        return {
            'nome': name,
            'tipo': 'Cronomante',
            'chave': normalize_candidate(rng.sample(range(1, 51), 5), rng.sample(range(1, 13), 2), rng),
            'precisao_temporal': 0.0,
            'assinatura_temporal': [],
        }

    moon_age = float(world.get('idade_lua', 0.0))
    signature = []
    numbers = []
    stars = []

    for event in extraction['eventos'][:5]:
        energy = (
            event['segundo']
            + (event['milissegundo'] % 100)
            + moon_age
            + index * 3
        )
        value = int(energy % 50) + 1
        signature.append(round(energy, 3))
        numbers.append(value)

    for event in extraction['eventos'][5:]:
        energy = event['segundo'] + (event['milissegundo'] % 12) + index
        stars.append(int(energy % 12) + 1)

    key = normalize_candidate(numbers, stars, rng)
    precision = round(max(0.05, 0.65 - abs(extraction['atraso_arranque'] - 8.0) / 30.0), 3)
    return {
        'nome': name,
        'tipo': 'Cronomante',
        'chave': key,
        'precisao_temporal': precision,
        'assinatura_temporal': signature,
    }


def create_chronomancers(cfg, extraction, world, rng):
    quantity = cfg.getint('EXTRACAO', 'quantidade_cronomantes', fallback=4)
    names = [
        'Aurel dos Segundos Perdidos',
        'Chrona da Ampulheta Partida',
        'Kairon do Último Instante',
        'Selvar, Guardião do Pulso',
        'Nym do Relógio Lunar',
    ]
    return [
        generate_temporal_key(names[i % len(names)], extraction, world, rng, i)
        for i in range(quantity)
    ]
