# Darukaa.Earth — AI Biodiversity Intelligence Chatbot

An AI system that reasons about biodiversity, soil, land use, and climate
metrics together, and produces evidence-backed, multi-metric
recommendations — not a generic LLM wrapper.

## Architecture in one line

Structured input -> completeness check -> (rule-based relationship graph
+ vector DB evidence retrieval) -> LLM synthesis -> structured,
citable output.

The knowledge layer is deliberately split into two parts instead of a
single RAG pipeline:

- `app/knowledge/relationships.json` — a small, hand-curated table of
  known causal relationships between environmental metrics (e.g. soil
  organic carbon -> microbial diversity). This is what guarantees the
  system connects multiple variables instead of answering from a single
  retrieved chunk.
- `app/knowledge/vector_store.py` — ChromaDB + sentence-transformers
  over real source documents (FAO, IPCC, IPBES, peer-reviewed papers).
  This is what grounds the "why it works" text in actual evidence
  instead of the LLM inventing plausible-sounding numbers.

## Folder structure

```
biodiversity-chatbot/
├── app/
│   ├── config.py              # env-driven config, single source of truth
│   ├── main.py                 # FastAPI entrypoint (Checkpoint 2)
│   ├── models/
│   │   └── schemas.py          # Pydantic input/output schemas
│   ├── knowledge/
│   │   ├── relationships.json  # curated metric-relationship table
│   │   ├── relationship_graph.py
│   │   ├── vector_store.py     # ChromaDB wrapper
│   │   └── ingest.py           # chunk + embed source documents
│   ├── reasoning/
│   │   ├── metric_extractor.py # free text -> structured metrics
│   │   └── synthesizer.py      # calls Groq, builds final response
│   ├── conversation/
│   │   ├── session_manager.py  # in-memory multi-turn state
│   │   └── clarifier.py        # missing-field detection + questions
│   ├── api/
│   │   └── routes.py
│   └── utils/
│       └── prompts.py
├── data/
│   ├── sources/                # raw PDFs/text of FAO, IPCC, IPBES etc.
│   └── chroma_db/               # persisted vector store (generated)
├── frontend/
│   └── streamlit_app.py
├── tests/
│   └── test_example_case.py     # validates against the brief's worked example
├── requirements.txt
└── .env.example
```

## Setup

```bash
python -m venv venv
source venv/bin/activate        # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env             # then fill in GROQ_API_KEY
```

## Status

- [x] Folder structure + config + schemas
- [x] Checkpoint 1: knowledge base (sources, relationship table, vector DB)
- [x] Checkpoint 2: core reasoning pipeline
- [x] Checkpoint 3: conversation layer
- [x] Checkpoint 4: input handling + Streamlit UI
- [ ] Checkpoint 5: defense documentation
