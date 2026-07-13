
from datetime import datetime
from racas.antigas import normalizar


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
        nome = amuleto.get("nome") if isinstance(amuleto, dict) else str(amuleto)
        total *= tabela.get(nome, 1.0)
    return total


def calcular_ritual(cfg, mundo, evolucao):
    ativo = cfg.getboolean("RITUAL_CELESTE", "ativo", fallback=False)
    if not ativo:
        return {
            "ativo": False,
            "energia_total": 0.0,
            "contribuicoes": [],
            "chave_humana": None,
        }

    energia_por_ponto = cfg.getfloat("RITUAL_CELESTE", "energia_por_ponto", fallback=0.001)
    usar_almas = cfg.getboolean("RITUAL_CELESTE", "usar_almas", fallback=True)
    usar_ressuscitados = cfg.getboolean("RITUAL_CELESTE", "usar_ressuscitados", fallback=True)

    almas = []
    if usar_almas:
        almas.extend(evolucao.get("cemiterio", []))
    if usar_ressuscitados:
        almas.extend(evolucao.get("ressuscitados", []))

    # Evita duplicação por ID.
    unicas = {}
    for alma in almas:
        unicas[alma.id] = alma
    almas = list(unicas.values())

    contribuicoes = []
    total = 0.0
    mult_ress = cfg.getfloat("RITUAL_CELESTE", "multiplicador_ressuscitado", fallback=2.0)

    for alma in almas:
        score = max(0, float(alma.pontos))
        mult_titulo = _multiplicador_titulo(alma.titulo, cfg)
        mult_estado = mult_ress if "RESSUSCITADO" in alma.estado or alma.raca.startswith("Renascido ") else 1.0
        mult_amuletos = _multiplicador_amuletos(alma.amuletos, cfg)
        energia = score * energia_por_ponto * mult_titulo * mult_estado * mult_amuletos

        contribuicoes.append({
            "id": alma.id,
            "nome": alma.nome,
            "raca": alma.raca,
            "estado": alma.estado,
            "score": score,
            "titulo": alma.titulo,
            "amuletos": alma.amuletos,
            "multiplicador_titulo": round(mult_titulo, 3),
            "multiplicador_estado": round(mult_estado, 3),
            "multiplicador_amuletos": round(mult_amuletos, 3),
            "energia": round(energia, 6),
        })
        total += energia

    contribuicoes.sort(key=lambda x: x["energia"], reverse=True)

    nums = _lista_int(cfg.get("RITUAL_CELESTE", "chave_numeros", fallback="1,10,32,36,43"))
    ests = _lista_int(cfg.get("RITUAL_CELESTE", "chave_estrelas", fallback="5,6"))
    chave_humana = normalizar(nums, ests)

    data_hora_inicio = f"{mundo['data']} {cfg.get('RITUAL_CELESTE', 'inicio', fallback='00:00:00')}"
    data_hora_fim = f"{mundo['data']} {cfg.get('RITUAL_CELESTE', 'libertacao', fallback='20:00:00')}"
    inicio = datetime.strptime(data_hora_inicio, "%Y-%m-%d %H:%M:%S")
    fim = datetime.strptime(data_hora_fim, "%Y-%m-%d %H:%M:%S")
    duracao_horas = max(0.0, (fim - inicio).total_seconds() / 3600.0)

    return {
        "ativo": True,
        "inicio": inicio.isoformat(),
        "libertacao": fim.isoformat(),
        "duracao_horas": round(duracao_horas, 3),
        "almas_presentes": len(almas),
        "energia_por_ponto": energia_por_ponto,
        "energia_total": round(total, 6),
        "score_total": round(sum(x["score"] for x in contribuicoes), 3),
        "score_medio": round(
            (sum(x["score"] for x in contribuicoes) / len(contribuicoes))
            if contribuicoes else 0.0,
            3,
        ),
        "contribuicoes": contribuicoes,
        "top_contribuidores": contribuicoes[:20],
        "chave_humana": chave_humana,
        "peso_no_conselho": cfg.getfloat("RITUAL_CELESTE", "peso_no_conselho", fallback=1.5),
        "aviso": "Energia narrativa; não altera a probabilidade matemática do sorteio.",
    }
