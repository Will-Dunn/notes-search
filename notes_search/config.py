import os
import tomllib
import tomli_w
from dataclasses import dataclass
from pathlib import Path
from notes_search.logger import get_logger

logger = get_logger(__name__)
CONFIG_PATH = Path.home() / ".notes-search" / "config.toml"

DEFAULT_CONFIG = {
    "ollama": {
        "base_url": "http://localhost:11434",
        "llm_model": "llama3.1:8b",
        "embed_model": "nomic-embed-text",
    },
    "embeddings": {"dimensions": 768},
    "chunking": {"chunk_size": 512, "chunk_overlap": 50},
    "search": {"top_k_chunks": 10, "related_notes_count": 5},
    "database": {"path": str(Path.home() / ".notes-search" / "notes.db")},
}


@dataclass
class Config:
    ollama_base_url: str
    llm_model: str
    embed_model: str
    dimensions: int
    chunk_size: int
    chunk_overlap: int
    top_k_chunks: int
    related_notes_count: int
    db_path: Path


def get_config() -> Config:
    if not CONFIG_PATH.exists():
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(tomli_w.dumps(DEFAULT_CONFIG))
        logger.info("Generated default config at %s", CONFIG_PATH)

    with open(CONFIG_PATH, "rb") as f:
        raw = tomllib.load(f)

    try:
        db_path = Path(
            os.environ.get("NOTES_SEARCH_DB_PATH") or raw["database"]["path"]
        ).expanduser()

        return Config(
            ollama_base_url=raw["ollama"]["base_url"],
            llm_model=raw["ollama"]["llm_model"],
            embed_model=raw["ollama"]["embed_model"],
            dimensions=raw["embeddings"]["dimensions"],
            chunk_size=raw["chunking"]["chunk_size"],
            chunk_overlap=raw["chunking"]["chunk_overlap"],
            top_k_chunks=raw["search"]["top_k_chunks"],
            related_notes_count=raw["search"]["related_notes_count"],
            db_path=db_path,
        )
    except KeyError as e:
        raise SystemExit(f"Error: config.toml is missing key: {e}. Delete it to regenerate defaults.") from e
