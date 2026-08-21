
import json
from pathlib import Path
from collections import Counter
from datetime import datetime, date


BASE = Path("library")


def ler_json(path, padrao=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {} if padrao is None else padrao


def save_query(name, consulta):
    path = BASE / "cache" / f"{name}.json"
    path.write_text(json.dumps(consulta, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


class Ariadne:
    """LIVE/NORMAL (default, `scrolls=None`): unchanged from before
    Commit 23 — reads library/scrolls/ and library/indexes/ live off
    disk, exactly as always.

    TEMPORAL (`scrolls=<already-loaded pergaminho dicts>`, typically
    core.services.historical_ariadne_source.build_scrolls_for_backtest()):
    scroll_state/search_moon/overdue_numbers/transition_pattern/
    full_history/weekly_echoes/last_known_key operate exclusively over
    that frozen collection — zero additional reads of library/scrolls/.
    This also unifies a LIVE-mode-only inconsistency where some of
    these methods only ever considered 2026 (`self.scrolls`) while
    others re-walked every year fresh each call — in TEMPORAL mode all
    seven now see exactly the same collection (whatever years the
    caller included when building it).

    pairs()/triples()/numero()/least_frequent_numbers() read
    library/indexes/*.json — static snapshots with no timestamp of any
    kind. They are NOT certified for TEMPORAL mode and raise
    RuntimeError there rather than silently answering from a global,
    uncut index (see _require_live_mode()).
    """

    def __init__(self, scrolls=None):
        self.catalogo = ler_json(BASE / "catalogue/catalogo.json", {})
        self._temporal = scrolls is not None
        if self._temporal:
            self._frozen_scrolls = tuple(scrolls)
            self.scrolls = self._frozen_scrolls
        else:
            self._frozen_scrolls = None
            self.scrolls = sorted((BASE / "scrolls/2026").glob("*.json"))

    def _require_live_mode(self, method_name):
        if self._temporal:
            raise RuntimeError(
                f"Ariadne.{method_name}() reads a static library/indexes/*.json "
                "snapshot with no temporal provenance — not certified for a "
                "temporal instance (constructed with scrolls=...). Never "
                "available in temporal mode; regenerating temporally-scoped "
                "indexes is out of scope for this commit."
            )

    def _scope_a_scrolls(self):
        """scroll_state/search_moon/overdue_numbers/transition_pattern.
        LIVE: 2026-only, lazily loaded from self.scrolls (paths) —
        unchanged. TEMPORAL: the full frozen collection.
        """
        if self._temporal:
            return self._frozen_scrolls
        return tuple(ler_json(p) for p in self.scrolls)

    def _scope_b_scrolls(self):
        """full_history/weekly_echoes. LIVE: fresh walk of
        library/scrolls/ across all years — unchanged. TEMPORAL: the
        same frozen collection as _scope_a_scrolls (this is what
        eliminates the pre-Commit-23 2026-only-vs-all-years
        inconsistency).
        """
        if self._temporal:
            return self._frozen_scrolls
        scrolls_root = BASE / "scrolls"
        if not scrolls_root.exists():
            return ()
        out = []
        for pasta_ano in sorted(scrolls_root.iterdir()):
            if not pasta_ano.is_dir():
                continue
            for path in sorted(pasta_ano.glob("*.json")):
                p = ler_json(path)
                if isinstance(p, dict):
                    out.append(p)
        return tuple(out)

    @staticmethod
    def _scroll_state_response(p):
        return {
            "encontrado": True,
            "id": p.get("id"),
            "estado": p.get("estado"),
            "integridade": p.get("assinatura", {}).get("integridade"),
        }

    def scroll_state(self, numero):
        if self._temporal:
            scroll_id = f"PERG-2026-{int(numero):03d}"
            for p in self._frozen_scrolls:
                if p.get("id") == scroll_id:
                    return self._scroll_state_response(p)
            return {"encontrado": False, "estado": "AUSENTE"}
        path = BASE / "scrolls/2026" / f"{int(numero):03d}.json"
        if not path.exists():
            return {"encontrado": False, "estado": "AUSENTE"}
        return self._scroll_state_response(ler_json(path))

    def search_moon(self, fase):
        encontrados = []
        for p in self._scope_a_scrolls():
            if (p.get("astronomia", {}).get("fase_lua") or "").lower() == fase.lower():
                encontrados.append(p)

        numbers = Counter(n for p in encontrados for n in p["extracao"]["numeros"])
        stars = Counter(e for p in encontrados for e in p["extracao"]["estrelas"])
        somas = [p["estatisticas"]["soma"] for p in encontrados if p["estatisticas"]["soma"] is not None]

        resposta = {
            "pergunta": f"Padrões em {fase}",
            "tipo": "DESCRITIVO_NAO_PREDITIVO",
            "scrolls_encontrados": len(encontrados),
            "numeros_mais_frequentes": [
                {"numero": n, "frequencia": f} for n, f in numbers.most_common(10)
            ],
            "estrelas_mais_frequentes": [
                {"estrela": e, "frequencia": f} for e, f in stars.most_common(5)
            ],
            "soma_media": sum(somas) / len(somas) if somas else None,
            "aviso": "Observação histórica; não aumenta a probabilidade de prever um sorteio futuro.",
            "criada_em": datetime.now().isoformat(timespec="seconds"),
        }
        save_query(f"lua_{fase.lower().replace(' ', '_')}", resposta)
        return resposta

    def pairs(self, limite=10):
        self._require_live_mode("pairs")
        dados = ler_json(BASE / "indexes/duplas.json", {})
        return dados.get("duplas_mais_comuns", [])[:limite]

    def triples(self, limite=10):
        self._require_live_mode("triples")
        dados = ler_json(BASE / "indexes/triplas.json", {})
        return dados.get("triplas_mais_comuns", [])[:limite]

    def numero(self, numero):
        self._require_live_mode("numero")
        livro = ler_json(BASE / "indexes/saidas_de_bolas_normalizado.json", {"numeros": []})
        for item in livro["numeros"]:
            if item["numero"] == int(numero):
                return item
        return None

    def overdue_numbers(self, limite=15):
        """Numbers with greatest gap (draws) since last appearance in 2026 pergaminhos."""
        scrolls = self._scope_a_scrolls()
        ultimo_visto = {}
        for idx, p in enumerate(scrolls):
            for n in p.get("extracao", {}).get("numeros", []):
                ultimo_visto[n] = idx

        total = len(scrolls)
        atrasados = []
        for n in range(1, 51):
            if n in ultimo_visto:
                delay = total - 1 - ultimo_visto[n]
            else:
                delay = total
            atrasados.append({"numero": n, "atraso": delay})

        atrasados.sort(key=lambda x: x["atraso"], reverse=True)
        resposta = {
            "tipo": "DESCRITIVO_NAO_PREDITIVO",
            "total_pergaminhos": total,
            "numeros_atrasados": atrasados[:limite],
            "aviso": "Observação histórica; não aumenta a probabilidade de prever um sorteio futuro.",
            "criada_em": datetime.now().isoformat(timespec="seconds"),
        }
        save_query("numeros_atrasados", resposta)
        return atrasados[:limite]

    def least_frequent_numbers(self, limite=20):
        """Historically least frequent numbers from saidas_de_bolas_normalizado.json."""
        self._require_live_mode("least_frequent_numbers")
        livro = ler_json(BASE / "indexes/saidas_de_bolas_normalizado.json", {"numeros": []})
        todos = sorted(livro["numeros"], key=lambda x: x.get("aparicoes_totais", 0))
        result = [
            {"numero": x["numero"], "aparicoes_totais": x.get("aparicoes_totais", 0)}
            for x in todos[:limite]
        ]
        resposta = {
            "tipo": "DESCRITIVO_NAO_PREDITIVO",
            "numeros_menos_frequentes": result,
            "aviso": "Observação histórica; não aumenta a probabilidade de prever um sorteio futuro.",
            "criada_em": datetime.now().isoformat(timespec="seconds"),
        }
        save_query("numeros_menos_frequentes", resposta)
        return result

    def transition_pattern(self):
        """Pattern between penultimate and last key in 2026 pergaminhos."""
        scrolls = self._scope_a_scrolls()
        if len(scrolls) < 2:
            return {"encontrado": False, "aviso": "Menos de 2 pergaminhos disponíveis."}

        pen = scrolls[-2]
        ult = scrolls[-1]
        nums_pen = set(pen.get("extracao", {}).get("numeros", []))
        nums_ult = set(ult.get("extracao", {}).get("numeros", []))
        ests_pen = set(pen.get("extracao", {}).get("estrelas", []))
        ests_ult = set(ult.get("extracao", {}).get("estrelas", []))
        soma_pen = pen.get("estatisticas", {}).get("soma") or 0
        soma_ult = ult.get("estatisticas", {}).get("soma") or 0

        resposta = {
            "tipo": "DESCRITIVO_NAO_PREDITIVO",
            "penultima": {
                "id": pen.get("id"),
                "data": pen.get("data", {}).get("extracao"),
                "numeros": sorted(nums_pen),
                "estrelas": sorted(ests_pen),
                "soma": soma_pen,
            },
            "ultima": {
                "id": ult.get("id"),
                "data": ult.get("data", {}).get("extracao"),
                "numeros": sorted(nums_ult),
                "estrelas": sorted(ests_ult),
                "soma": soma_ult,
            },
            "persistentes": sorted(nums_pen & nums_ult),
            "saidos": sorted(nums_pen - nums_ult),
            "chegados": sorted(nums_ult - nums_pen),
            "estrelas_persistentes": sorted(ests_pen & ests_ult),
            "estrelas_saidas": sorted(ests_pen - ests_ult),
            "estrelas_chegadas": sorted(ests_ult - ests_pen),
            "delta_soma": soma_ult - soma_pen,
            "aviso": "Observação histórica; não aumenta a probabilidade de prever um sorteio futuro.",
            "criada_em": datetime.now().isoformat(timespec="seconds"),
        }
        save_query("padrao_transicao", resposta)
        return resposta

    def weekly_echoes(self, semana_iso):
        """All draws from the same ISO week across all available pergaminho folders."""
        if not self._temporal and not (BASE / "scrolls").exists():
            return {"tipo": "DESCRITIVO_NAO_PREDITIVO", "semana_iso": int(semana_iso), "total_ecos": 0, "ecos": []}

        echoes = []
        for p in self._scope_b_scrolls():
            raw_data = p.get("data")
            if isinstance(raw_data, dict):
                data_str = raw_data.get("extracao")
            elif isinstance(raw_data, str):
                data_str = raw_data
            else:
                continue
            if not data_str:
                continue
            try:
                d = date.fromisoformat(data_str)
                iso = d.isocalendar()
                if iso[1] == int(semana_iso):
                    echoes.append({
                        "id": p.get("id"),
                        "data": data_str,
                        "ano_iso": iso[0],
                        "semana_iso": iso[1],
                        "numeros": p.get("extracao", {}).get("numeros", []),
                        "estrelas": p.get("extracao", {}).get("estrelas", []),
                        "soma": p.get("estatisticas", {}).get("soma"),
                    })
            except (ValueError, AttributeError):
                continue

        resposta = {
            "tipo": "DESCRITIVO_NAO_PREDITIVO",
            "semana_iso": int(semana_iso),
            "total_ecos": len(echoes),
            "ecos": echoes,
            "aviso": "Observação histórica; não aumenta a probabilidade de prever um sorteio futuro.",
            "criada_em": datetime.now().isoformat(timespec="seconds"),
        }
        save_query(f"ecos_semanais_semana_{int(semana_iso):02d}", resposta)
        return resposta

    def full_history(self, desde=None, ate=None, ultimos=None):
        """All draws from all pergaminho folders, sorted by date."""
        history = []

        for p in self._scope_b_scrolls():
            raw_data = p.get("data")
            if isinstance(raw_data, dict):
                data_str = raw_data.get("extracao")
            elif isinstance(raw_data, str):
                data_str = raw_data
            else:
                continue
            if not data_str:
                continue
            numbers = p.get("extracao", {}).get("numeros", [])
            stars = p.get("extracao", {}).get("estrelas", [])
            if not numbers or len(numbers) != 5:
                continue
            try:
                d = date.fromisoformat(data_str)
            except (ValueError, AttributeError):
                continue
            history.append({
                "id": p.get("id"),
                "data": data_str,
                "_data_obj": d,
                "ano": d.year,
                "semana_iso": d.isocalendar()[1],
                "numeros": numbers,
                "estrelas": stars,
                "soma": p.get("estatisticas", {}).get("soma"),
            })

        history.sort(key=lambda x: x["_data_obj"])
        for h in history:
            h.pop("_data_obj")

        if desde:
            history = [h for h in history if h["data"] >= desde]
        if ate:
            history = [h for h in history if h["data"] <= ate]
        if ultimos:
            history = history[-ultimos:]

        return history

    def last_known_key(self):
        """Devolve o último sorteio registado (data, numeros, estrelas)."""
        todos = self.full_history()
        if not todos:
            return None
        u = todos[-1]
        return {
            'id': u['id'],
            'data': u['data'],
            'numeros': u['numeros'],
            'estrelas': u['estrelas'],
        }

    def create_papyrus(self, semana_iso, dados):
        """Saves a Kor Preto papiro to biblioteca/black_kors/papyri/week_XX/."""
        pasta = BASE / f"black_kors/papyri/week_{int(semana_iso):02d}"
        pasta.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = pasta / f"papiro_{ts}.json"
        papiro = {
            "tipo": "PAPIRO_KOR_PRETO",
            "semana_iso": int(semana_iso),
            "criado_em": datetime.now().isoformat(timespec="seconds"),
            **dados,
        }
        path.write_text(json.dumps(papiro, indent=2, ensure_ascii=False), encoding="utf-8")
        return str(path)
