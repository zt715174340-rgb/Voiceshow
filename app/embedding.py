"""Embedding model boundary for product and knowledge indexing."""

def embed_text(text: str) -> list[float]:
    # Replace with a configured embedding provider in the real implementation.
    return embedding_client.embed(text)


def embed_batch(texts: list[str]) -> list[list[float]]:
    return embedding_client.embed_batch(texts)
