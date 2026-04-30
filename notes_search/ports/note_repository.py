from abc import ABC, abstractmethod

from notes_search.core.models import Chunk, Note, TaggedNote


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
    def get_note_by_id(self, note_id: str, include_tags: bool = False) -> Note | None: ...

    @abstractmethod
    def save_note_embedding(self, note_id: str, embedding: list[float]) -> None: ...

    @abstractmethod
    def get_related_notes(self, note_id: str, top_k: int) -> list[Note] | None: ...

    @abstractmethod
    def get_note_by_name(self, name: str) -> TaggedNote | None: ...
