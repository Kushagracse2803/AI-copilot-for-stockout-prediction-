import os
import chromadb
from chromadb.utils import embedding_functions

CHROMA_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "chroma_db")


def get_collection():
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    return client.get_or_create_collection(
        name="om_traders_policies",
        embedding_function=embedding_fn,
    )


def retrieve_relevant_chunks(query: str, top_k: int = 3) -> list[dict]:
    collection = get_collection()
    results = collection.query(query_texts=[query], n_results=top_k)

    chunks = []
    for doc, metadata, distance in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
        chunks.append({
            "text": doc,
            "source": metadata["source"],
            "relevance_distance": distance,
        })
    return chunks


if __name__ == "__main__":
    test_query = "What is the safety stock for books during admission season?"
    results = retrieve_relevant_chunks(test_query)

    print(f"Query: {test_query}\n")
    for i, r in enumerate(results, 1):
        print(f"[{i}] Source: {r['source']} (distance: {r['relevance_distance']:.3f})")
        print(f"    {r['text']}\n")