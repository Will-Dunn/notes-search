from abc import ABC, abstractmethod

from notes_search.core.models import Chunk, Note


class INotesRepository(ABC):
    @abstractmethod
    def save_note(self, note: Note) -> None: ...

    @abstractmethod
    def save_chunk(self, chunk: Chunk, embedding: list[float]) -> None: ...

    @abstractmethod
    def save_tags(self, note_id: str, tags: list[str]) -> None: ...

    @abstractmethod
    def note_exists(self, source_path: str) -> bool: ...

    @abstractmethod
    def search_chunks(
        self, embedding: list[float], top_k: int
    ) -> list[tuple[Chunk, float]]: ...

    @abstractmethod
    def get_note_by_id(self, note_id: str) -> Note | None: ...
