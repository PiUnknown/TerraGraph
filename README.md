# Darukaa.Earth — AI Biodiversity Intelligence Chatbot

An AI system that reasons across soil, water, land-use, and biodiversity
metrics to produce evidence-backed, multi-metric recommendations —
built for the Darukaa.Earth hackathon assignment.

**This is deliberately not a "chatbot wrapped around an LLM."** The
assignment explicitly ruled out generic LLM-only solutions, so the
core design decision here was to separate *what the system knows*
from *how it talks about what it knows* — a curated relationship
graph handles the former deterministically, the LLM handles only the
latter.

---

## The problem this solves

Given a description of a piece of land (soil condition, rainfall,
current land use, region type), the system:

1. Asks clarifying questions if the description is incomplete
2. Identifies which known ecological relationships apply
3. Retrieves supporting evidence from real scientific sources for each
4. Synthesizes grounded, cited, multi-metric recommendations —
   never a generic "use sustainable practices"

Example: told that soil organic carbon is 0.3%, rainfall is low, the
land is monoculture wheat, in a semi-arid region, the system
independently returns ~10 recommendations spanning soil biology,
water retention, and land-use change — each with a mechanism, an
impacted metric, a time horizon, a confidence level, and a citation
to FAO, IPBES, or peer-reviewed sources.

---

## Architecture

```
Structured/text input
        ↓
Completeness check (deterministic)
        ↓
   ┌────────────────┬─────────────────────┐
   │ Relationship    │  Vector DB          │
   │ graph lookup    │  retrieval          │
   │ (rule-based)    │  (ChromaDB +        │
   │                 │   sentence-         │
   │                 │   transformers)     │
   └────────────────┴─────────────────────┘
        ↓
LLM synthesis (Groq, strict schema + no-invention rules)
        ↓
Structured output (action, mechanism, metrics, effect,
time horizon, confidence, source)
```

### Why a relationship graph *and* a vector DB, not just RAG

A standard RAG pipeline retrieves chunks per query and lets the LLM
reason over them. That's a reasonable default, but it makes
**multi-metric reasoning** — the assignment's explicitly named
differentiator — dependent on the LLM happening to retrieve the right
chunks and correctly inferring connections between them. There's no
architectural guarantee it works; it's a hope, not a design.

Instead, this system hand-curates ~15 relationships (`soil organic
carbon ↔ microbial diversity`, `rainfall ↔ soil moisture/NPP feedback
loop`, `land-use change ↔ species richness`, etc.) as structured data,
each with a real citation. Given an input, matching which relationships
apply is deterministic — same input, same matches, every time,
independent of the LLM. The vector DB's job is narrower and different:
given a matched relationship, retrieve supporting evidence chunks from
the actual source PDFs so the LLM's explanation is grounded in real
text, not paraphrased from training data.

This also means the knowledge system is directly demonstrable and
testable in isolation — matching can be unit-tested with zero LLM
calls (see `tests/test_example_case.py`), and retrieval quality can be
checked independently (see `app/knowledge/validate_retrieval.py`)
before either is combined with LLM synthesis.

### Why the LLM is used narrowly

The LLM has exactly two jobs in this system, both bounded:

1. **Free-text → structured fields.** Turning "biodiversity is
   declining on my land, it's pretty dry here" into
   `EnvironmentalInput(rainfall="low", ...)`. This is genuine natural
   language understanding, and it's the one place ambiguity is
   unavoidable.
2. **Synthesis.** Given the deterministically matched relationships
   and their retrieved evidence, write the final recommendation text.
   The system prompt explicitly forbids inventing facts/numbers,
   forbids merging distinct relationships into one recommendation, and
   requires exactly one recommendation per matched relationship — so
   the LLM's freedom is in *phrasing*, not in *deciding what's true*.

Everything else — which relationships apply, whether a clarifying
question is needed, whether a message is small talk, multi-turn field
accumulation — is deterministic Python, with no LLM call and no
token cost.

---

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Backend | FastAPI | Async, typed, auto-generates OpenAPI docs for live testing |
| Knowledge base | ChromaDB + sentence-transformers (`all-MiniLM-L6-v2`) | Persistent local vector store, no external service dependency |
| LLM | Groq (`llama-3.3-70b-versatile`) | Fast inference suitable for live demo latency |
| Schema/validation | Pydantic v2 | Enforces output shape; a "vague recommendation" has nowhere to hide in the schema |
| Frontend | Streamlit | Assignment explicitly deprioritizes UI polish in favor of reasoning depth; a minimal chat UI redirects effort to the knowledge/reasoning layers |
| PDF ingestion | pypdf | Lightweight text extraction, sufficient for text-heavy scientific reports |

**Notably not used: LangChain.** The retrieval pipeline has exactly
one pattern (embed a query, get top-k chunks with metadata). LangChain's
retriever abstractions earn their keep when composing multiple
retrievers or chaining with other LangChain components — for a single,
simple retrieval call, direct `chromadb` client calls are more
transparent and easier to defend line-by-line than an abstraction
layer that isn't doing meaningful work here.

---

## Knowledge base sources

Five real, citable documents, chosen to cover the assignment's three
required cross-links (soil↔biodiversity, water↔species survival,
land-use↔habitat fragmentation):

- FAO (2017), *Soil Organic Carbon: The Hidden Potential*
- IPCC SRCCL, Chapter 4 — Land Degradation
- IPBES Global Assessment, Summary for Policymakers (2019)
- MDPI *Sustainability* (2019), 11(10):2879 — Agroforestry and Biodiversity
- Frontiers in Agronomy (2025) — Diversified vs. monoculture cropping systems

## Folder structure

```
TerraGraph/
├── app/
│   ├── config.py               # env-driven config, single source of truth
│   ├── main.py                 # FastAPI entrypoint
│   ├── models/schemas.py       # Pydantic input/output schemas
│   ├── knowledge/
│   │   ├── relationships.json  # curated metric-relationship table (~15 entries)
│   │   ├── relationship_graph.py  # deterministic matching engine
│   │   ├── vector_store.py     # ChromaDB wrapper
│   │   ├── ingest.py           # chunk + embed source documents
│   │   └── validate_retrieval.py  # standalone retrieval sanity check
│   ├── reasoning/
│   │   ├── metric_extractor.py # free text -> structured metrics (LLM)
│   │   └── synthesizer.py      # orchestrates matching + evidence + LLM synthesis
│   ├── conversation/
│   │   ├── session_manager.py  # in-memory multi-turn state
│   │   ├── clarifier.py        # missing-field detection + question templates
│   │   └── small_talk.py       # deterministic greeting/thanks/farewell handling
│   ├── api/routes.py           # /chat (text) and /chat/structured (JSON) endpoints
│   └── utils/prompts.py        # LLM system prompts
├── data/
│   ├── sources/                # raw source PDFs
│   └── chroma_db/              # persisted vector store
├── frontend/streamlit_app.py
└── tests/test_example_case.py  # validates against the assignment's own worked example
```

## Running it

```bash
python -m venv venv
venv\Scripts\activate           # or source venv/bin/activate on macOS/Linux
pip install -r requirements.txt
cp .env.example .env             # fill in GROQ_API_KEY

# populate the knowledge base (one-time, or after adding new PDFs)
python -m app.knowledge.ingest
python -m app.knowledge.validate_retrieval   # sanity check, optional

# run the backend
uvicorn app.main:app --reload

# in a second terminal, run the frontend
streamlit run frontend/streamlit_app.py
```

Validate the core pipeline independently of the UI:
```bash
python -m tests.test_example_case
```

## Known limitations

- **Knowledge base coverage is cropland-focused.** The 5 curated
  sources and ~15 relationships cover monoculture, agroforestry, cover
  cropping, and related soil/land-use dynamics well. Land types outside
  that scope (pasture, forestry, wetlands) will correctly return "no
  matching evidence" rather than a fabricated answer — this is
  intentional (no false positives), but it does mean coverage is
  narrower than the space of all possible land descriptions.
- **Confidence levels are LLM-assigned, not derived from a fixed
  rule.** A future iteration could compute confidence from whether
  the relationship's `estimated_effect` contains a hard number versus
  qualitative language.
- **Session memory is in-process and non-persistent.** A server
  restart clears all conversation state. Fine for a demo/single-session
  use case; a production version would need Redis or similar.
- **Matching uses lightweight keyword/stem matching, not semantic
  similarity**, for the relationship trigger conditions. This keeps
  matching deterministic and auditable, at the cost of requiring
  trigger conditions to be worded reasonably close to expected input
  phrasing.
