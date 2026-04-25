from notes_search.core.models import RelatedNote, SearchResult
from notes_search.ports.embedder import IEmbedder
from notes_search.ports.note_repository import INotesRepository
from notes_search.ports.synthesizer import ISynthesizer


class SearchService:
    def __init__(self, repo: INotesRepository, embedder: IEmbedder, synthesizer: ISynthesizer) -> None:
        self._repo = repo
        self._embedder = embedder
        self._synthesizer = synthesizer

    def search(self, query: str, raw: bool = False, top_k: int = 10) -> SearchResult:
        query_embedding = self._embedder.embed([query])[0]
        chunk_results = self._repo.search_chunks(query_embedding, top_k)

        note_results: list[RelatedNote] = []
        seen: set[str] = set()
        for chunk, score in chunk_results:
            if chunk.note_id in seen:
                continue
            note = self._repo.get_note_by_id(chunk.note_id, include_tags=True)
            if note is not None:
                note_results.append(RelatedNote(note=note, related_chunk=chunk, score=score))
                seen.add(chunk.note_id)

        synth_response = ""
        if not raw and note_results:
            synth_response = self._synthesizer.synthesize(query, [chunk for chunk, _ in chunk_results])

        return SearchResult(generated_response=synth_response, related_notes=note_results)
