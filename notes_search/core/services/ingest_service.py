import uuid
from datetime import datetime, timezone
from pathlib import Path

from notes_search.core.models import Chunk, Note
from notes_search.ports.chunker import IChunker
from notes_search.ports.embedder import IEmbedder
from notes_search.ports.note_repository import INotesRepository
from notes_search.ports.tagger import ITagger

SUPPORTED_EXTENSIONS = (".md", ".txt")


class IngestService:
    def __init__(
        self,
        repo: INotesRepository,
        embedder: IEmbedder,
        chunker: IChunker,
        tagger: ITagger,
    ) -> None:
        self._repo = repo
        self._embedder = embedder
        self._chunker = chunker
        self._tagger = tagger

    def ingest(self, path: Path) -> tuple[int, int]:
        """Ingest a file or directory. Returns (ingested, skipped)."""
        if path.is_dir():
            files = list(path.rglob("*.md")) + list(path.rglob("*.txt"))
        else:
            files = [path]
        files = [f for f in files if f.suffix in SUPPORTED_EXTENSIONS]

        ingested = 0
        skipped = 0
        for file in files:
            source_path = str(file.resolve())
            if self._repo.note_exists(source_path):
                skipped += 1
                continue

            content = file.read_text()
            if not content.strip():
                continue

            source_type = "markdown" if file.suffix == ".md" else "text"
            now = datetime.now(timezone.utc).isoformat()
            note = Note(
                id=str(uuid.uuid4()),
                title=file.stem,
                content=content,
                source_path=source_path,
                source_type=source_type,
                created_at=now,
                updated_at=now,
            )
            self._repo.save_note(note)

            text_chunks = self._chunker.chunk(content)
            embeddings = self._embedder.embed(text_chunks)
            for i, (chunk_text, embedding) in enumerate(zip(text_chunks, embeddings)):
                chunk = Chunk(
                    id=str(uuid.uuid4()),
                    note_id=note.id,
                    content=chunk_text,
                    chunk_index=i,
                )
                self._repo.save_chunk(chunk, embedding)

            tags = self._tagger.tag(content)
            self._repo.save_tags(note.id, tags)
            ingested += 1

        return ingested, skipped
