import httpx
import typer
from pathlib import Path

from notes_search.config import get_config
from notes_search.container import build_ingest_service, build_search_service
from notes_search.logger import get_logger

logger = get_logger(__name__)
app = typer.Typer(help="Local, offline-capable note search and generation CLI.")


def _check_ollama(base_url: str, llm_model: str, embed_model: str) -> None:
    """Verify Ollama is reachable and required models are available. Exit 1 on failure."""
    try:
        response = httpx.get(f"{base_url}/api/tags", timeout=5)
        response.raise_for_status()
    except (httpx.ConnectError, httpx.TimeoutException):
        typer.echo(
            f"Error: Ollama is not reachable at {base_url}.\n"
            "Start it with: ollama serve",
            err=True,
        )
        logger.error("Ollama not reachable at %s", base_url)
        raise SystemExit(1)
    except httpx.HTTPStatusError as e:
        typer.echo(f"Error: Ollama returned an unexpected response: {e}", err=True)
        logger.error("Ollama health check failed: %s", e)
        raise SystemExit(1)

    available = {m["name"] for m in response.json().get("models", [])}

    missing = []
    for model in (llm_model, embed_model):
        if not any(m == model or m.startswith(model + ":") for m in available):
            missing.append(model)

    if missing:
        for model in missing:
            typer.echo(f"Error: Model '{model}' is not available. Run:", err=True)
            typer.echo(f"  ollama pull {model}", err=True)
        logger.error("Missing Ollama models: %s", missing)
        raise SystemExit(1)

    logger.info("Ollama health check passed (models: %s, %s)", llm_model, embed_model)


@app.callback(invoke_without_command=True)
def startup(ctx: typer.Context) -> None:
    """Run on every invocation before any subcommand."""
    if ctx.invoked_subcommand is None:
        return
    config = get_config()
    _check_ollama(config.ollama_base_url, config.llm_model, config.embed_model)
    ctx.ensure_object(dict)
    ctx.obj["config"] = config
    logger.info("Startup complete")


@app.command()
def ingest(
    ctx: typer.Context,
    path: Path = typer.Argument(..., help="Path to a note file or directory"),
) -> None:
    """Ingest a note or directory of notes into the database."""
    if not path.is_dir() and path.suffix not in (".md", ".txt"):
        typer.echo(
            f"Error: unsupported file type '{path.suffix}'. Supported types: .md, .txt",
            err=True,
        )
        raise typer.Exit(1)

    service = build_ingest_service()
    ingested, skipped = service.ingest(path)

    if ingested == 0 and skipped == 0:
        typer.echo("No eligible files found.", err=True)
        raise typer.Exit(1)

    if skipped:
        typer.echo(f"Skipped {skipped} already-ingested file(s).", err=True)
    typer.echo(f"Ingested {ingested} note(s).")


@app.command()
def search(
    ctx: typer.Context,
    query: str = typer.Argument(..., help="Search query"),
    top_k: int = typer.Option(10, help="Number of results to return"),
) -> None:
    """Search notes by semantic similarity."""
    service = build_search_service()
    results = service.search(query, top_k)
    if not results:
        typer.echo("No results found.")
        return
    for note, score in results:
        typer.echo(f"[{score:.4f}] {note.title}  ({note.source_path})")


if __name__ == "__main__":
    app()
