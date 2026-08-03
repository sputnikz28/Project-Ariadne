"""Narrative "inspiration seed" generation for the Artifact Library.

Purely creative and read-only: given an already-normalized ArtifactRecord
(see core/services/artifact_schema.py) and a seed, produces a small,
partial set of narrative aspects that could inspire a NEW character
concept. This module never creates or edits a Hero or a Legend, never
touches the filesystem, never recommends numbers/stars, and never
suggests any effect on algorithms, results or probabilities — every
phrase pulled from the artifact passes through a safety filter before it
can reach the output, and every generated sentence is built only from
already-filtered phrases inserted into fixed, pre-approved templates.

Deterministic: the same (record, seed) pair always returns the same
result. Uses only a local random.Random(seed) instance, never the global
random module, and never depends on dict/filesystem iteration order —
every field is read by name in a fixed order.

Inspiration is deliberately partial: each call samples a handful of
aspects rather than the whole record, and always produces at least one
narrative contradiction/tension so the inspired character can never be a
direct copy of the artifact.
"""

from __future__ import annotations

import random
import re
from collections.abc import Mapping, Sequence

from core.services.artifact_schema import ArtifactRecord

_STOPWORDS = {"DA", "DE", "DO", "DOS", "DAS", "E", "SIMBOLO", "TIPO"}

_FORBIDDEN_PATTERNS = (
    re.compile(r"\d"),
    re.compile(r"algoritmo", re.IGNORECASE),
    re.compile(r"probabilidad", re.IGNORECASE),
    re.compile(r"\bresultados?\b", re.IGNORECASE),
    re.compile(r"previs[aã]o", re.IGNORECASE),
    re.compile(r"\bprever\b", re.IGNORECASE),
    re.compile(r"profecia", re.IGNORECASE),
    re.compile(r"\bn[uú]meros?\b", re.IGNORECASE),
)

_FALLBACK_TRACO = "essência ainda por descobrir"
_FALLBACK_VALOR = "valor ainda por descobrir"
_FALLBACK_SIMBOLO = "símbolo ainda por descobrir"
_FALLBACK_APARENCIA = "forma ainda indefinida"

_TENSION_TEMPLATES = (
    "Valoriza {a}, mas ainda tem dificuldade em vivê-lo no dia a dia.",
    "Admira {a} no artefacto, mas sente que ainda não o alcançou em si próprio.",
    "Deseja {a}, mas teme que isso signifique abdicar de {b}.",
    "Sente-se atraído por {a}, mesmo sabendo que {b} pede o oposto disso.",
    "Diz que valoriza {a}, mas as suas escolhas nem sempre o confirmam.",
)

_MISSION_TEMPLATES = (
    "Aprender a expressar {a} nas próprias ações, sem depender do artefacto para isso.",
    "Honrar o espírito de {a}, encontrando a sua própria versão dele.",
    "Provar, através de pequenos gestos, que é capaz de {a}.",
    "Encontrar um equilíbrio pessoal entre {a} e {b}.",
    "Tornar-se, com o tempo, alguém que já não precisa do artefacto para lembrar {a}.",
)

_CONFLICT_TEMPLATES = (
    "A tentação de procurar atalhos quando {a} parece distante demais.",
    "O medo de nunca estar à altura do símbolo que representa {a}.",
    "A dúvida entre confiar em {a} ou confiar apenas em si próprio.",
    "A pressão de outros à sua volta para usar o artefacto de forma que ele próprio recusaria.",
    "A dificuldade em equilibrar {a} com {b} nos momentos mais difíceis.",
)

_RELATION_TEMPLATES = (
    "Vê {nome} como um espelho de {a}, não como uma fonte de poder.",
    "Sente-se guardião temporário de {a}, mais do que dono de {nome}.",
    "Aprende com {nome}, mas sabe que a jornada é sua, não do artefacto.",
    "Respeita {nome} sem depender dele — o crescimento tem de vir de dentro.",
    "Carrega {nome} como lembrança de {a}, não como garantia de nada.",
)


def _humanize(token: str) -> str:
    if not isinstance(token, str) or not token.strip():
        return ""
    parts = [p for p in re.split(r"[_\-]+", token.strip()) if p]
    kept = [p for p in parts if p.upper() not in _STOPWORDS]
    if not kept:
        kept = parts
    return " ".join(p.lower() for p in kept)


def _is_safe_phrase(text: str) -> bool:
    return not any(pattern.search(text) for pattern in _FORBIDDEN_PATTERNS)


def _add(pool: list, value) -> None:
    if not isinstance(value, str):
        return
    text = value.strip()
    if not text or not _is_safe_phrase(text):
        return
    if text not in pool:
        pool.append(text)


def _collect_concepts(record: ArtifactRecord) -> dict:
    tracos: list = []
    valores: list = []
    simbolos: list = []
    aparencia: list = []
    flavor: list = []

    if record.tipo:
        h = _humanize(record.tipo)
        _add(tracos, h)
        _add(simbolos, h)

    if record.raridade:
        _add(simbolos, _humanize(record.raridade))

    if record.estado is not None and record.estado.codigo:
        _add(simbolos, _humanize(record.estado.codigo))

    if record.criador is not None and record.criador.nome:
        _add(simbolos, record.criador.nome)

    if isinstance(record.efeitos, Mapping):
        tipo_efeito = record.efeitos.get("tipo")
        if isinstance(tipo_efeito, str):
            h = _humanize(tipo_efeito)
            _add(tracos, h)
            _add(simbolos, h)

    for tag in record.tags:
        _add(simbolos, tag)

    for evento_hist in record.historia:
        codigo = evento_hist.evento.codigo if evento_hist.evento else None
        if isinstance(codigo, str):
            _add(simbolos, _humanize(codigo))
        extra = evento_hist.extra
        if isinstance(extra, Mapping):
            descricao = extra.get("descricao")
            if isinstance(descricao, Mapping):
                _add(flavor, descricao.get("pt"))
            elif isinstance(descricao, str):
                _add(flavor, descricao)

    extras = record.extras

    bencaos = extras.get("bencaos")
    if isinstance(bencaos, Mapping):
        keys = [k for k in bencaos if isinstance(k, str)]
        mid = (len(keys) + 1) // 2
        for k in keys[:mid]:
            _add(tracos, _humanize(k))
        for k in keys[mid:]:
            _add(valores, _humanize(k))

    inscricao = extras.get("inscricao")
    if isinstance(inscricao, Mapping):
        _add(flavor, inscricao.get("pt"))

    evolucao = extras.get("evolucao")
    if isinstance(evolucao, Mapping):
        _add(valores, evolucao.get("sistema"))
        _add(flavor, evolucao.get("filosofia"))

    ritual = extras.get("ritual")
    if isinstance(ritual, Mapping):
        nome_ritual = ritual.get("nome")
        if isinstance(nome_ritual, Mapping):
            _add(simbolos, nome_ritual.get("pt"))
        mensagens = ritual.get("mensagens")
        if isinstance(mensagens, Mapping):
            pt_msgs = mensagens.get("pt")
            if isinstance(pt_msgs, Sequence) and not isinstance(pt_msgs, (str, bytes)):
                for msg in pt_msgs:
                    _add(flavor, msg)

    rituais = extras.get("rituais")
    if isinstance(rituais, Mapping):
        for fase in ("inicio", "conclusao"):
            bloco = rituais.get(fase)
            if isinstance(bloco, Mapping):
                _add(flavor, bloco.get("mensagem"))

    objetivo = extras.get("objetivo")
    if isinstance(objetivo, Mapping):
        _add(tracos, "objetivo pessoal")
        estado_objetivo = objetivo.get("estado")
        if isinstance(estado_objetivo, str):
            _add(simbolos, _humanize(estado_objetivo))

    paginas_vivas = extras.get("paginas_vivas")
    if isinstance(paginas_vivas, Sequence) and not isinstance(paginas_vivas, (str, bytes)):
        for pagina in paginas_vivas:
            if isinstance(pagina, Mapping):
                tipo_pagina = pagina.get("tipo")
                if isinstance(tipo_pagina, str):
                    _add(simbolos, _humanize(tipo_pagina))
                _add(flavor, pagina.get("texto"))

    guardiao = extras.get("guardiao")
    if isinstance(guardiao, Mapping):
        _add(simbolos, guardiao.get("titulo"))
        _add(flavor, guardiao.get("funcao"))

    celebracao = extras.get("celebracao")
    if isinstance(celebracao, Mapping):
        for flag_key in ("fogos_artificio", "confettis", "brinde"):
            if celebracao.get(flag_key) is True:
                _add(tracos, _humanize(flag_key))
        musica = celebracao.get("musica")
        if isinstance(musica, str):
            _add(simbolos, _humanize(musica))
        mensagens = celebracao.get("mensagens")
        if isinstance(mensagens, Mapping):
            pt_msgs = mensagens.get("pt")
            if isinstance(pt_msgs, Sequence) and not isinstance(pt_msgs, (str, bytes)):
                for msg in pt_msgs:
                    _add(flavor, msg)

    cor_principal = extras.get("cor_principal")
    if isinstance(cor_principal, str):
        h = _humanize(cor_principal)
        _add(aparencia, h)
        _add(simbolos, h)

    cores = extras.get("cores")
    if isinstance(cores, Sequence) and not isinstance(cores, (str, bytes)):
        for cor in cores:
            if isinstance(cor, str):
                h = _humanize(cor)
                _add(aparencia, h)
                _add(simbolos, h)

    material = extras.get("material")
    if isinstance(material, Mapping):
        _add(aparencia, material.get("pt"))
    elif isinstance(material, str):
        _add(aparencia, material)

    aparencia_raw = extras.get("aparencia")
    if isinstance(aparencia_raw, str):
        _add(aparencia, aparencia_raw)
    elif isinstance(aparencia_raw, Mapping):
        for v in aparencia_raw.values():
            _add(aparencia, v)

    for extra_key in ("conforto", "fofura"):
        if extra_key in extras:
            _add(tracos, extra_key)
            _add(simbolos, extra_key)

    if record.lore:
        _add(flavor, record.lore.get("pt"))

    return {
        "tracos": tracos,
        "valores": valores,
        "simbolos": simbolos,
        "aparencia": aparencia,
        "flavor": flavor,
    }


def _dedupe(seq) -> list:
    seen = set()
    out = []
    for item in seq:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _pick_subset(rng: random.Random, pool: list, min_n: int, max_n: int) -> list:
    if not pool:
        return []
    upper = min(max_n, len(pool))
    lower = min(min_n, upper)
    n = rng.randint(lower, upper)
    return rng.sample(pool, n)


def _assert_safe(value) -> None:
    if isinstance(value, str):
        assert _is_safe_phrase(value), f"unsafe phrase leaked into inspiration output: {value!r}"
    elif isinstance(value, Mapping):
        for v in value.values():
            _assert_safe(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            _assert_safe(v)


def generate_inspiration(record: ArtifactRecord, seed: int) -> dict:
    """Pure, deterministic narrative "inspiration seed" for a NEW character
    concept loosely based on `record`. Never mutates record/raw/extras,
    never touches the filesystem. The same (record, seed) pair always
    returns the same result; different seeds may return different
    combinations.

    The safety filter runs over inspiration_aspects and generated_seed
    only — artifact_id is a traceability identifier (e.g.
    "ART-7A3F91C2BE" legitimately contains digits), not narrative
    content, so it is intentionally excluded from the digit-based check.
    """
    rng = random.Random(seed)
    pools = _collect_concepts(record)

    tracos_sel = _pick_subset(rng, pools["tracos"], 2, 4) or [_FALLBACK_TRACO]
    valores_sel = _pick_subset(rng, pools["valores"], 1, 3) or [_FALLBACK_VALOR]
    simbolos_sel = _pick_subset(rng, pools["simbolos"], 2, 4) or [_FALLBACK_SIMBOLO]
    aparencia_sel = _pick_subset(rng, pools["aparencia"], 1, 2) or [_FALLBACK_APARENCIA]
    flavor_sel = _pick_subset(rng, pools["flavor"], 1, 2)

    combined = _dedupe(tracos_sel + valores_sel)
    a = rng.choice(combined)
    remaining = [c for c in combined if c != a] or combined
    b = rng.choice(remaining)

    nome_pt = None
    if record.nome:
        nome_pt = record.nome.get("pt")
    if not nome_pt:
        nome_pt = record.id or "o artefacto"

    n_contra = rng.randint(1, min(2, len(_TENSION_TEMPLATES)))
    contradicoes = [
        template.format(a=a, b=b)
        for template in rng.sample(_TENSION_TEMPLATES, n_contra)
    ]

    missao = rng.choice(_MISSION_TEMPLATES).format(a=a, b=b)
    conflito = rng.choice(_CONFLICT_TEMPLATES).format(a=a, b=b)
    relacao = rng.choice(_RELATION_TEMPLATES).format(a=a, nome=nome_pt)
    if flavor_sel:
        relacao = f'{relacao} "{rng.choice(flavor_sel)}"'

    inspiration_aspects = _dedupe(tracos_sel + valores_sel + simbolos_sel + aparencia_sel)

    result = {
        "artifact_id": record.id,
        "inspiration_aspects": inspiration_aspects,
        "generated_seed": {
            "tracos_sugeridos": tracos_sel,
            "valores": valores_sel,
            "contradicoes": contradicoes,
            "aparencia_inspirada": aparencia_sel,
            "simbolos": simbolos_sel,
            "conflito_possivel": conflito,
            "missao_possivel": missao,
            "relacao_sugerida_com_artefacto": relacao,
        },
    }

    _assert_safe(result["inspiration_aspects"])
    _assert_safe(result["generated_seed"])
    return result
