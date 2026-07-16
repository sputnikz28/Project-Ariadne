
import hashlib
import json
import re
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from pathlib import Path

from artifacts.amulets.persistence import CACHE, save_json


def unload(name, url, timeout=8):
    result = {
        "fonte": name,
        "url": url,
        "consultado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "estado": "falhou",
        "conteudo_sha256": None,
        "tamanho": 0,
        "estatisticas_extraidas": {},
    }
    if not url:
        result["erro"] = "URL vazia"
        return result

    try:
        req = Request(url, headers={
            "User-Agent": "OraculosGeneticos/4.5 (+biblioteca-estatistica; uso moderado)"
        })
        with urlopen(req, timeout=timeout) as resposta:
            bruto = resposta.read()
            charset = resposta.headers.get_content_charset() or "utf-8"
        html = bruto.decode(charset, errors="replace")
        result["estado"] = "ok"
        result["tamanho"] = len(bruto)
        result["conteudo_sha256"] = hashlib.sha256(bruto).hexdigest()
        result["estatisticas_extraidas"] = extrair_frequencias_genericas(html)
        cache_path = CACHE / f"{name}.html"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(html, encoding="utf-8")
    except (URLError, HTTPError, TimeoutError, OSError, ValueError) as erro:
        result["erro"] = str(erro)

    save_json(CACHE / f"{name}_estado.json", result)
    return result


def extrair_frequencias_genericas(html):
    """
    Tentativa conservadora: procura pares 'número + frequência' no texto.
    Estes dados remotos servem para comparação; os livros canónicos são
    calculados a partir do histórico local validado.
    """
    texto = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.I | re.S)
    texto = re.sub(r"<[^>]+>", " ", texto)
    texto = re.sub(r"\s+", " ", texto)

    candidates = {}
    # Padrões frequentes em tabelas de estatística: número seguido de contagem.
    for numero in range(1, 51):
        padroes = [
            rf"(?:^|\s){numero}\s+(\d{{2,4}})(?:\s|$)",
            rf"(?:n[uú]mero\s*)?{numero}\D{{0,30}}(?:frequ[eê]ncia|vezes)\D{{0,10}}(\d{{1,4}})",
        ]
        valores = []
        for padrao in padroes:
            valores.extend(int(x) for x in re.findall(padrao, texto, flags=re.I))
        valores = [v for v in valores if 0 <= v <= 5000]
        if valores:
            candidates[str(numero)] = max(valores)
    return candidates
