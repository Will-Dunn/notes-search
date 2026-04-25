from abc import ABC, abstractmethod

from notes_search.core.models import Chunk


class ISynthesizer(ABC):
    @abstractmethod
    def synthesize(self, query: str, chunks: list[Chunk]) -> str: ...
