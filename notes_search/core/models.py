from dataclasses import dataclass, field


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
class Chunk:
    id: str
    note_id: str
    content: str
    chunk_index: int


@dataclass
class Tag:
    id: str
    name: str
