import os
import chromadb
from chromadb.utils import embedding_functions

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "documents")
CHROMA_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "chroma_db")


def chunk_text(text: str) -> list[str]:
    """
    Split a document into chunks by blank lines (paragraphs / numbered sections).
    This is a simple but effective approach for structured policy documents
    like ours, where each numbered point is already a self-contained idea.
    """
    raw_chunks = text.split("\n\n")
    chunks = [c.strip() for c in raw_chunks if c.strip()]
    return chunks


def ingest_documents():
    # --- set up a local embedding model (runs free, no API key) ---
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    collection = client.get_or_create_collection(
        name="om_traders_policies",
        embedding_function=embedding_fn,
    )

    doc_files = [f for f in os.listdir(DOCS_DIR) if f.endswith(".txt")]
    print(f"Found {len(doc_files)} documents: {doc_files}")

    all_chunks, all_ids, all_metadata = [], [], []

    for filename in doc_files:
        filepath = os.path.join(DOCS_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_ids.append(f"{filename}_{i}")
            all_metadata.append({"source": filename, "chunk_index": i})

        print(f"  {filename} -> {len(chunks)} chunks")

    # add (or overwrite) into the vector database
    collection.upsert(
        documents=all_chunks,
        ids=all_ids,
        metadatas=all_metadata,
    )

    print(f"\nTotal chunks stored: {len(all_chunks)}")
    print(f"Vector DB saved -> {CHROMA_DB_DIR}")


if __name__ == "__main__":
    ingest_documents()