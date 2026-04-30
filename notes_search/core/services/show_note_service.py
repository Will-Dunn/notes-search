from notes_search.core.models import SearchResult, NoteWithRelations
from notes_search.ports.note_repository import INotesRepository


class show_note_service:
    def __init__(
            self,
            repo: INotesRepository
    ) -> None:
        self._repo = repo

    def show_note(self, name: str, top_k: int) -> NoteWithRelations:
        note = self._repo.get_note_by_name(name)
        if note is None:
            raise Exception(f"Note with name {name} not found")
        return NoteWithRelations(note, self._repo.get_related_notes(note.id, top_k))
