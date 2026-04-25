from abc import ABC, abstractmethod

from notes_search.core.models import Chunk


class ISynthesizer(ABC):
    @abstractmethod
    def summarize(self, relatedChunks: list[Chunk]) -> str: ...
    @abstractmethod
    def answer(self, question: str, relatedChunks: list[Chunk]) -> str: ...

