"""
Run: python -m backend.knowledge.ingest
Loads fitness/nutrition knowledge into ChromaDB fitness_knowledge collection.
"""
import asyncio
from langchain_openai import OpenAIEmbeddings
from backend.db.chroma_client import get_knowledge_collection
from backend.knowledge.documents import KNOWLEDGE_DOCS

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")


async def ingest():
    collection = get_knowledge_collection()
    existing = collection.count()
    print(f"Existing documents: {existing}")

    texts = [doc["text"] for doc in KNOWLEDGE_DOCS]
    metadatas = [doc["metadata"] for doc in KNOWLEDGE_DOCS]
    ids = [doc["id"] for doc in KNOWLEDGE_DOCS]

    vectors = await embeddings.aembed_documents(texts)

    collection.upsert(
        documents=texts,
        embeddings=vectors,
        metadatas=metadatas,
        ids=ids,
    )
    print(f"Ingested {len(texts)} documents into fitness_knowledge collection.")


if __name__ == "__main__":
    asyncio.run(ingest())
