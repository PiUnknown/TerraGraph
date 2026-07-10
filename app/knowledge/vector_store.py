import chromadb
from chromadb.utils import embedding_functions

from app.config import CHROMA_PERSIST_DIR, CHROMA_COLLECTION_NAME, EMBEDDING_MODEL


class VectorStore:
    def __init__(self):
        self._client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

        self._embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )

        self._collection = self._client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME,
            embedding_function=self._embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(self, ids: list[str], texts: list[str], metadatas: list[dict]) -> None:
        self._collection.add(ids=ids, documents=texts, metadatas=metadatas)

    def retrieve(self, query: str, k: int = 5) -> list[dict]:
        results = self._collection.query(query_texts=[query], n_results=k)

        chunks = []
        for text, metadata, distance in zip(
            results["documents"][0], results["metadatas"][0], results["distances"][0]
        ):
            chunks.append({
                "text": text,
                "source": metadata.get("source", "unknown"),
                "distance": distance,
            })
        return chunks

    def count(self) -> int:
        return self._collection.count()