def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> list[str]:
    tokens = text.split()
    chunks = []
    step = chunk_size - overlap
    for i in range(0, len(tokens), step):
        chunks.append(" ".join(tokens[i:i + chunk_size]))
    return chunks

