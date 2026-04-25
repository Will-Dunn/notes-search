from abc import ABC, abstractmethod


class IChunker(ABC):
    @abstractmethod
    def chunk(self, text: str) -> list[str]: ...
