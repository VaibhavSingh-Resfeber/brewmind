from sentence_transformers import SentenceTransformer

# Model is loaded once at module import time, not inside functions.
# Loading a sentence-transformers model reads ~90 MB from disk and
# initialises PyTorch weights — doing this on every call would add
# ~1-2 s of latency per request and spike memory allocations.
# Module-level initialisation happens exactly once per Python process.
_model = SentenceTransformer("all-MiniLM-L6-v2")
print("✅ Embedding model loaded")


def embed_text(text: str) -> list[float]:
    """Return a 384-dimensional embedding for a single string."""
    return _model.encode(text).tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Return embeddings for multiple strings in a single batched forward pass.

    Batching is significantly faster than calling embed_text() in a loop
    because the model processes all inputs in one GPU/CPU kernel invocation.
    """
    return _model.encode(texts).tolist()


if __name__ == "__main__":
    vector = embed_text("quiet light roast cafe Munich")
    print("First 5 values:", vector[:5])
    print("Vector length:", len(vector))
