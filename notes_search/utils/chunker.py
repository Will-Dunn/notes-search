def chunk_text(text, chunk_size=512, overlap=50):
    tokens = text.split()
    chunks = []
    step = chunk_size - overlap
    for i in range(0, len(tokens), step):
        chunks.append(" ".join(tokens[i:i + chunk_size]))
    return chunks                                                             

