import chromadb
from backend.core.config import settings

_client: chromadb.ClientAPI | None = None


def get_chroma_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
        )
    return _client


def get_knowledge_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(
        name="fitness_knowledge",
        metadata={"hnsw:space": "cosine"},
    )


def get_user_logs_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(
        name="user_logs_summary",
        metadata={"hnsw:space": "cosine"},
    )
