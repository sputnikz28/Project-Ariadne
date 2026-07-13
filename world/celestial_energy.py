
from datetime import datetime
from races.antigas import normalize


def _lista_int(texto):
    return [int(x.strip()) for x in texto.split(",") if x.strip()]


def _multiplicador_titulo(titulo, cfg):
    titulo = (titulo or "").upper()
    if "LENDA" in titulo:
        return cfg.getfloat("RITUAL_CELESTE", "multiplicador_lenda", fallback=5.0)
    if "PROFETA" in titulo or "AQUELE QUE VIU" in titulo:
        return cfg.getfloat("RITUAL_CELESTE", "multiplicador_profeta", fallback=2.0)
    if "MESTRE" in titulo:
        return cfg.getfloat("RITUAL_CELESTE", "multiplicador_mestre", fallback=1.5)
    return 1.0


def _multiplicador_amuletos(amuletos, cfg):
    if not cfg.getboolean("RITUAL_CELESTE", "usar_amuletos", fallback=True):
        return 1.0

    tabela = {
        "Osso Lunar": cfg.getfloat("RITUAL_CELESTE", "multiplicador_osso_lunar", fallback=1.10),
        "Espelho dos Sonhos Esquecidos": cfg.getfloat("RITUAL_CELESTE", "multiplicador_espelho_sonhos", fallback=1.20),
        "Livro dos Ecos": cfg.getfloat("RITUAL_CELESTE", "multiplicador_livro_ecos", fallback=1.30),
        "Presa Imutável de Fenrir": cfg.getfloat("RITUAL_CELESTE", "multiplicador_presa_fenrir", fallback=1.40),
        "Fragmento Divino": cfg.getfloat("RITUAL_CELESTE", "multiplicador_fragmento_divino", fallback=1.50),
    }

    total = 1.0
    for amuleto in amuletos or []:
        name = amuleto.get("nome") if isinstance(amuleto, dict) else str(amuleto)
        total *= tabela.get(name, 1.0)
    return total


def calculate_ritual(cfg, world, evolution_data):
    ativo = cfg.getboolean("RITUAL_CELESTE", "ativo", fallback=False)
    if not ativo:
        return {
            "ativo": False,
            "energia_total": 0.0,
            "contribuicoes": [],
            "chave_humana": None,
        }

    energy_per_point = cfg.getfloat("RITUAL_CELESTE", "energia_por_ponto", fallback=0.001)
    usar_almas = cfg.getboolean("RITUAL_CELESTE", "usar_almas", fallback=True)
    usar_ressuscitados = cfg.getboolean("RITUAL_CELESTE", "usar_ressuscitados", fallback=True)

    souls = []
    if usar_almas:
        souls.extend(evolution_data.get("cemiterio", []))
    if usar_ressuscitados:
        souls.extend(evolution_data.get("ressuscitados", []))

    # Evita duplicação por ID.
    unicas = {}
    for alma in souls:
        unicas[alma.id] = alma
    souls = list(unicas.values())

    contributions = []
    total = 0.0
    mult_ress = cfg.getfloat("RITUAL_CELESTE", "multiplicador_ressuscitado", fallback=2.0)

    for alma in souls:
        score = max(0, float(alma.pontos))
        mult_titulo = _multiplicador_titulo(alma.titulo, cfg)
        mult_estado = mult_ress if "RESSUSCITADO" in alma.estado or alma.raca.startswith("Renascido ") else 1.0
        mult_amuletos = _multiplicador_amuletos(alma.amuletos, cfg)
        energy = score * energy_per_point * mult_titulo * mult_estado * mult_amuletos

        contributions.append({
            "id": alma.id,
            "nome": alma.name,
            "raca": alma.raca,
            "estado": alma.estado,
            "score": score,
            "titulo": alma.titulo,
            "amuletos": alma.amuletos,
            "multiplicador_titulo": round(mult_titulo, 3),
            "multiplicador_estado": round(mult_estado, 3),
            "multiplicador_amuletos": round(mult_amuletos, 3),
            "energia": round(energy, 6),
        })
        total += energy

    contributions.sort(key=lambda x: x["energia"], reverse=True)

    nums = _lista_int(cfg.get("RITUAL_CELESTE", "chave_numeros", fallback="1,10,32,36,43"))
    ests = _lista_int(cfg.get("RITUAL_CELESTE", "chave_estrelas", fallback="5,6"))
    chave_humana = normalize(nums, ests)

    data_hora_inicio = f"{world['data']} {cfg.get('RITUAL_CELESTE', 'inicio', fallback='00:00:00')}"
    data_hora_fim = f"{world['data']} {cfg.get('RITUAL_CELESTE', 'libertacao', fallback='20:00:00')}"
    inicio = datetime.strptime(data_hora_inicio, "%Y-%m-%d %H:%M:%S")
    fim = datetime.strptime(data_hora_fim, "%Y-%m-%d %H:%M:%S")
    duracao_horas = max(0.0, (fim - inicio).total_seconds() / 3600.0)

    return {
        "ativo": True,
        "inicio": inicio.isoformat(),
        "libertacao": fim.isoformat(),
        "duracao_horas": round(duracao_horas, 3),
        "almas_presentes": len(souls),
        "energia_por_ponto": energy_per_point,
        "energia_total": round(total, 6),
        "score_total": round(sum(x["score"] for x in contributions), 3),
        "score_medio": round(
            (sum(x["score"] for x in contributions) / len(contributions))
            if contributions else 0.0,
            3,
        ),
        "contribuicoes": contributions,
        "top_contribuidores": contributions[:20],
        "chave_humana": chave_humana,
        "peso_no_conselho": cfg.getfloat("RITUAL_CELESTE", "peso_no_conselho", fallback=1.5),
        "aviso": "Energia narrativa; não altera a probabilidade matemática do sorteio.",
    }
