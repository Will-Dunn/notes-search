# Notes Search

Local, offline-capable CLI for ingesting, searching, and generating personal notes using locally hosted AI models — no data leaves your machine.

## Features

- Ingest typed notes (`.md`, `.txt`, `.docx`) and handwritten notes (`.jpg`, `.jpeg`, `.png`, `.heic`, `.pdf` via OCR)
- Semantic search with RAG synthesis: embed your query, retrieve matching chunks, get an LLM-synthesized answer grounded in your own notes
- `--raw` flag returns ranked source notes without LLM synthesis
- Auto-tag every note on ingest using Llama 3.1 8B; manually add or remove tags with `notes tag`
- View full note content, tags, and up to 5 related notes via `notes show`
- Create notes inline from the CLI with `notes create`
- Update an existing note's chunks and embeddings with `notes update`
- Generate new notes from a prompt, optionally enriched with RAG context from existing notes; saves with `ai-generated` tag
- HEIC images converted to PNG in-memory (no temp file) before OCR
- All inference runs through Ollama — fully offline after initial model pulls

## Tech Stack

- **Language**: Python 3.11+
- **CLI**: Typer
- **Database**: SQLite + sqlite-vec (single-file, no server, ANN vector search)
- **LLM**: Llama 3.1 8B via Ollama
- **Embeddings**: nomic-embed-text via Ollama (768 dimensions)
- **OCR**: PaddleOCR
- **HEIC conversion**: pillow-heif
- **DOCX parsing**: python-docx
- **Packaging**: uv + pyproject.toml

## Getting Started

### Requirements

- Python 3.11+
- [Ollama](https://ollama.com) installed and running (`ollama serve`)
- uv (`pip install uv` or `brew install uv`)

### Install

```bash
git clone <repo>
cd notes-search
uv sync
```

### Pull models

```bash
./scripts/setup_models.sh
```

This pulls `llama3.1:8b` and `nomic-embed-text` via Ollama and pre-downloads PaddleOCR model weights so they don't download mid-ingest.

### Run

```bash
notes ingest ./my-note.md
notes search "what did I write about machine learning"
notes show <note-id>
```

Config and database are auto-initialized at `~/.notes-search/` on first run.

### Transfer to a new machine

Copy `~/.notes-search/` to the new machine, then follow the install steps above. All notes, embeddings, and tags are preserved in the copied database.

### Override database path

```bash
export NOTES_SEARCH_DB_PATH=/path/to/custom/notes.db
```
