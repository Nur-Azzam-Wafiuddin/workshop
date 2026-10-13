"""Factory embedding (objek LangChain `Embeddings`)."""
from __future__ import annotations

from functools import lru_cache

from langchain_core.embeddings import Embeddings

from migas_shared import config


@lru_cache(maxsize=1)
def get_embeddings() -> Embeddings:
    """Kembalikan model embedding sesuai EMBED_PROVIDER di .env.

    - fastembed : model ONNX dijalankan lokal di CPU (default, tidak butuh API key).
                  Unduhan pertama sekitar 220 MB ke folder EMBED_CACHE_DIR.
    - openai    : endpoint /v1/embeddings kompatibel OpenAI (Ollama, vLLM, TEI, dan sebagainya).
    """
    if config.EMBED_PROVIDER == "fastembed":
        from langchain_community.embeddings import FastEmbedEmbeddings

        return FastEmbedEmbeddings(model_name=config.EMBED_MODEL, cache_dir=config.EMBED_CACHE_DIR)

    if config.EMBED_PROVIDER == "openai":
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(
            model=config.EMBED_MODEL,
            base_url=config.EMBED_BASE_URL,
            api_key=config.EMBED_API_KEY,
            check_embedding_ctx_length=False,  # wajib untuk server non-OpenAI (tanpa tiktoken)
        )

    raise ValueError(f"EMBED_PROVIDER tidak dikenal: {config.EMBED_PROVIDER}")
