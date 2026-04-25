from dataclasses import dataclass, field
from typing import Iterator


@dataclass
class Note:
    id: str
    title: str
    content: str
    source_path: str
    source_type: str
    is_ocr: bool = False
    is_generated: bool = False
    created_at: str = ""
    updated_at: str = ""

@dataclass
class TaggedNote(Note):
    tags: list[str] = field(default_factory=list)

@dataclass
class Chunk:
    id: str
    note_id: str
    content: str
    chunk_index: int


@dataclass
class Tag:
    id: str
    name: str

@dataclass
class RelatedNote:
    note: TaggedNote
    related_chunk: Chunk
    score: float

@dataclass
class SearchResult:
    generated_response: Iterator[str] | None
    related_notes: list[RelatedNote] = field(default_factory=list)
