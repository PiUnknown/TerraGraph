from app.knowledge.vector_store import VectorStore

TEST_QUERIES = [
    "soil organic carbon and microbial diversity",
    "rainfall and species survival in drylands",
    "land use change and habitat fragmentation",
    "agroforestry effect on pollinator diversity",
    "monoculture cropping impact on biodiversity",
]


def run_validation():
    store = VectorStore()
    print(f"Collection holds {store.count()} chunks.\n")

    if store.count() == 0:
        print("Vector store is empty — run `python -m app.knowledge.ingest` first.")
        return

    for query in TEST_QUERIES:
        print(f"Query: \"{query}\"")
        results = store.retrieve(query, k=3)
        for rank, chunk in enumerate(results, start=1):
            snippet = chunk["text"][:180].replace("\n", " ")
            print(f"  [{rank}] source={chunk['source']}  distance={chunk['distance']:.4f}")
            print(f"      {snippet}...")
        print()


if __name__ == "__main__":
    run_validation()