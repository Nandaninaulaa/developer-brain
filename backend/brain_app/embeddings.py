"""
Embedding provider abstraction so the rest of the app doesn't care whether
embeddings come from a local model or a hosted API.

Default is "local" (fastembed, torch-free) — zero cost, no API key, works
offline. Switch EMBEDDING_PROVIDER=openai in .env for better quality once
you have a key.
"""
from functools import lru_cache

from . import config


class EmbeddingProvider:
    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]


class LocalEmbeddingProvider(EmbeddingProvider):
    def __init__(self, model_name: str):
        from fastembed import TextEmbedding
        self._model = TextEmbedding(model_name=model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [v.tolist() for v in self._model.embed(texts)]


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, model_name: str, api_key: str):
        from openai import OpenAI
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set but EMBEDDING_PROVIDER=openai")
        self._client = OpenAI(api_key=api_key)
        self._model = model_name

    def embed(self, texts: list[str]) -> list[list[float]]:
        # OpenAI's batch embedding endpoint — send in chunks of 96 to stay safe.
        out = []
        batch_size = 96
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            resp = self._client.embeddings.create(model=self._model, input=batch)
            out.extend([d.embedding for d in resp.data])
        return out


@lru_cache(maxsize=1)
def get_embedding_provider() -> EmbeddingProvider:
    if config.EMBEDDING_PROVIDER == "openai":
        return OpenAIEmbeddingProvider(config.OPENAI_EMBEDDING_MODEL, config.OPENAI_API_KEY)
    return LocalEmbeddingProvider(config.LOCAL_EMBEDDING_MODEL)
