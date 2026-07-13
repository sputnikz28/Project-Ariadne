from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Proposal:
    """A single candidate key proposed by a faction for the Council."""
    name: str
    key: tuple          # ([nums], [stars])
    weight: float
    origin: str = ""    # stored in arquivo_destino as 'origem'
    home: str = ""      # stored in registo_externo as 'casa'
    faction_class: str = ""
    extra: dict = field(default_factory=dict)


class Faction(ABC):
    """Contract that all faction implementations must satisfy.

    To create a new faction:
      1. Create factions/<name>/manifest.json (see existing examples)
      2. Create factions/<name>/strategy.py with a class inheriting Faction
      3. Implement propose(context) returning a list of Proposal objects
      4. Set class name in manifest.json under "class"
      No changes to main.py or council registration required.
    """
    manifest: dict = {}

    @property
    def name(self) -> str:
        return self.manifest.get('name', self.__class__.__name__)

    @property
    def origin(self) -> str:
        return self.manifest.get('id', 'unknown')

    @property
    def home(self) -> str:
        return self.manifest.get('home', '')

    @abstractmethod
    def propose(self, context: dict) -> list:
        """Generate candidate proposals for the Council.

        Args:
            context: dict with keys ariadne, seed, cfg, mundo, historico,
                     estatisticas, extracao, biblioteca

        Returns:
            list of Proposal instances
        """
        ...
