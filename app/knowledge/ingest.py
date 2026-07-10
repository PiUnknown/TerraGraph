import os
from pypdf import PdfReader

from app.knowledge.vector_store import VectorStore

SOURCES_DIR = "data/sources"
CHUNK_SIZE = 700
CHUNK_OVERLAP = 100


def extract_text_from_pdf(path: str) -> str:
    reader = PdfReader(path)
    pages_text = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages_text)


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


def ingest_all_sources() -> None:
    store = VectorStore()

    pdf_files = [f for f in os.listdir(SOURCES_DIR) if f.lower().endswith(".pdf")]
    if not pdf_files:
        print(f"No PDFs found in {SOURCES_DIR}/ — download the sources first.")
        return

    total_chunks = 0

    for filename in pdf_files:
        path = os.path.join(SOURCES_DIR, filename)
        print(f"Processing {filename}...")

        text = extract_text_from_pdf(path)
        if not text.strip():
            print(f"  WARNING: no extractable text in {filename}. Skipping.")
            continue

        chunks = chunk_text(text)
        ids = [f"{filename}_{i}" for i in range(len(chunks))]
        metadatas = [{"source": filename, "chunk_index": i} for i in range(len(chunks))]

        store.add_chunks(ids=ids, texts=chunks, metadatas=metadatas)
        print(f"  Added {len(chunks)} chunks from {filename}")
        total_chunks += len(chunks)

    print(f"\nDone. {total_chunks} chunks indexed across {len(pdf_files)} documents.")
    print(f"Collection now holds {store.count()} chunks total.")


if __name__ == "__main__":
    ingest_all_sources()