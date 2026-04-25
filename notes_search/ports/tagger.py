from abc import ABC, abstractmethod


class ITagger(ABC):
    @abstractmethod
    def tag(self, content: str) -> list[str]: ...
