from notes_search.adapters.ollama_embedder import OllamaEmbedder
from notes_search.adapters.ollama_synthesizer import OllamaSynthesizer
from notes_search.adapters.ollama_tagger import OllamaTagger
from notes_search.adapters.sqlite_repository import SqliteNotesRepository
from notes_search.adapters.word_chunker import WordChunker
from notes_search.config import get_config
from notes_search.core.services.ingest_service import IngestService
from notes_search.core.services.search_service import SearchService


def build_ingest_service() -> IngestService:
    cfg = get_config()
    repo = SqliteNotesRepository(cfg.db_path, cfg.dimensions)
    embedder = OllamaEmbedder(cfg.ollama_base_url, cfg.embed_model)
    tagger = OllamaTagger(cfg.ollama_base_url, cfg.llm_model)
    chunker = WordChunker(cfg.chunk_size, cfg.chunk_overlap)
    return IngestService(repo, embedder, chunker, tagger)


def build_search_service() -> SearchService:
    cfg = get_config()
    repo = SqliteNotesRepository(cfg.db_path, cfg.dimensions)
    embedder = OllamaEmbedder(cfg.ollama_base_url, cfg.embed_model)
    synth_service = OllamaSynthesizer(cfg.ollama_base_url, cfg.llm_model)
    return SearchService(repo, embedder, synth_service)
