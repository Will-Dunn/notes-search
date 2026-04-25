from notes_search.ports.chunker import IChunker


class WordChunker(IChunker):
    def __init__(self, chunk_size: int, chunk_overlap: int) -> None:
        self._size = chunk_size
        self._overlap = chunk_overlap

    def chunk(self, text: str) -> list[str]:
        tokens = text.split()
        chunks = []
        step = self._size - self._overlap
        for i in range(0, len(tokens), step):
            chunks.append(" ".join(tokens[i : i + self._size]))
        return chunks
