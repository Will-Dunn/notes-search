from notes_search.core.models import Note
from notes_search.ports.embedder import IEmbedder
from notes_search.ports.note_repository import INotesRepository


class SearchService:
    def __init__(self, repo: INotesRepository, embedder: IEmbedder) -> None:
        self._repo = repo
        self._embedder = embedder

    def search(self, query: str, top_k: int) -> list[tuple[Note, float]]:
        query_embedding = self._embedder.embed([query])[0]
        chunk_results = self._repo.search_chunks(query_embedding, top_k)

        results: list[tuple[Note, float]] = []
        seen: set[str] = set()
        for chunk, score in chunk_results:
            if chunk.note_id in seen:
                continue
            note = self._repo.get_note_by_id(chunk.note_id)
            if note is not None:
                results.append((note, score))
                seen.add(chunk.note_id)
        return results
