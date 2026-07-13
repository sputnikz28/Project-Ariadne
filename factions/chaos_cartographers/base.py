import json
import re
import unicodedata
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path


LIVROS_PATH = Path("library/books/cartographers")


def _slug(texto):
    norm = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    norm = re.sub(r"[^\w\s-]", "", norm.lower())
    return re.sub(r"[-\s]+", "_", norm).strip("_")


class CartografoDoCaos(ABC):
    nome: str
    especialidade: str

    def __init__(self, ariadne):
        self.ariadne = ariadne

    @abstractmethod
    def analisar(self, historico):
        """Receive the full historico list and return a result dict (must include 'titulo')."""

    def criar_livro(self, titulo, dados):
        LIVROS_PATH.mkdir(parents=True, exist_ok=True)
        path = LIVROS_PATH / f"{_slug(self.nome)}.json"
        livro = {
            "titulo": titulo,
            "autor": self.nome,
            "especialidade": self.especialidade,
            "tipo": "DESCRITIVO_NAO_PREDITIVO",
            "criado_em": datetime.now().isoformat(timespec="seconds"),
            "aviso": "Observação histórica; não aumenta a probabilidade de prever um sorteio futuro.",
            **dados,
        }
        path.write_text(json.dumps(livro, indent=2, ensure_ascii=False), encoding="utf-8")
        return str(path)

    def executar(self, historico):
        resultado = self.analisar(historico)
        titulo = resultado.pop("titulo")
        caminho = self.criar_livro(titulo, resultado)
        return {
            "cartografo": self.nome,
            "livro_titulo": titulo,
            "livro_path": caminho,
            "total_sorteios": resultado.get("total_sorteios", 0),
        }
