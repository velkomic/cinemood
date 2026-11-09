import hashlib
import os
from dataclasses import dataclass

MODEL = "text-embedding-3-small"
DIMENSIONS = 1536
DOCUMENT_VERSION = "movie-v1"


@dataclass(frozen=True)
class Settings:
    database_url: str
    api_key: str
    base_url: str

    @property
    def provider_fingerprint(self) -> str:
        return hashlib.sha256(self.base_url.rstrip("/").encode()).hexdigest()

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            database_url=os.getenv(
                "DATABASE_URL", "postgresql://cinemood:cinemood@db/cinemood"
            ),
            api_key=os.getenv("OPENAI_API_KEY", ""),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        )
