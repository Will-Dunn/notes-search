from notes_search.core.models import Note, SearchResult, RelatedNote
from notes_search.ports.embedder import IEmbedder
from notes_search.ports.note_repository import INotesRepository
from notes_search.ports.synthesizer import ISynthesizer


class SearchService:
    def __init__(self, repo: INotesRepository, embedder: IEmbedder, synth_service: ISynthesizer) -> None:
        self._repo = repo
        self._embedder = embedder
        self._synth_service = synth_service

    def search(self, query: str, question: str = "", raw: bool = False, top_k: int = 10) -> SearchResult:
        query_embedding = self._embedder.embed([query])[0]
        chunk_results = self._repo.search_chunks(query_embedding, top_k)

        notesResults: list[RelatedNote] = []
        seen: set[str] = set()
        for chunk, score in chunk_results:
            if chunk.note_id in seen:
                continue
            note = self._repo.get_note_by_id(chunk.note_id , include_tags=True)
            if note is not None:
                notesResults.append(RelatedNote(note = note, score = score, related_chunk = chunk))
                seen.add(chunk.note_id)
        synthResponse: str= "";
        if question:
            synthResponse = self._synth_service.answer(question, [chunk for chunk, _ in chunk_results])
        elif not raw:
            synthResponse = self._synth_service.summarize([chunk for chunk, _ in chunk_results])
        return SearchResult(synthResponse, notesResults)
