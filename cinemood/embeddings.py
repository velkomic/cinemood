import math

import httpx
from langchain_openai import OpenAIEmbeddings
from pydantic import SecretStr

from cinemood.config import DIMENSIONS, MODEL, Settings
from cinemood.usage import embedding_response


class ProviderUnavailable(Exception):
    pass


def embed(texts: list[str], settings: Settings) -> list[list[float]]:
    if not settings.api_key:
        raise ProviderUnavailable("Embedding provider is not configured.")
    try:
        with httpx.Client(event_hooks={"response": [embedding_response]}) as client:
            provider = OpenAIEmbeddings(
                model=MODEL,
                http_client=client,
                dimensions=DIMENSIONS,
                api_key=SecretStr(settings.api_key),
                base_url=settings.base_url,
                timeout=15,
                max_retries=0,
                check_embedding_ctx_length=False,
            )
            vectors = provider.embed_documents(texts)
        if len(vectors) != len(texts):
            raise ValueError("Missing embeddings")
        for vector in vectors:
            if (
                len(vector) != DIMENSIONS
                or not all(math.isfinite(x) for x in vector)
                or not any(x != 0 for x in vector)
            ):
                raise ValueError("Invalid embedding")
        return vectors
    except Exception as exc:
        raise ProviderUnavailable(
            "Embedding provider is unavailable. Try again later."
        ) from exc


def vector_literal(vector: list[float]) -> str:
    return "[" + ",".join(str(x) for x in vector) + "]"
