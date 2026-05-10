# ☕ BrewMind

> AI-powered specialty coffee intelligence for Munich — and beyond.

**BrewMind** is a RAG (Retrieval Augmented Generation) application that helps specialty coffee lovers find the right cafe and improve their home brewing. Unlike Google Maps, BrewMind understands coffee — roast profiles, brewing methods, flavour notes, and your personal taste preferences — and uses that understanding to make genuinely personalised recommendations.

Built as a portfolio project to demonstrate end-to-end AI engineering: data collection, semantic embeddings, vector search, LLM integration, and production deployment.

---

## 🎯 The problem

Google Maps knows where cafes are. It does not know that you prefer light roast Ethiopian V60 and want somewhere quiet to work on a Tuesday morning. It gives the same results to everyone.

BrewMind understands what you mean, not just what you type. Ask it anything:

- *"Quiet place in Maxvorstadt for light roast coffee while I work"*
- *"Where can I find a serious third-wave espresso near the Isar?"*
- *"I want somewhere with great filter coffee that's not too intimidating"*
- *"Find me a cafe that cares about sustainable sourcing"*

---

## 🏗️ How it works

BrewMind uses the **RAG (Retrieval Augmented Generation)** pattern — the dominant architecture for enterprise AI applications in 2025/2026.

```
User query
    │
    ▼
Embed query          ← sentence-transformers (local, free)
    │
    ▼
Vector similarity     ← pgvector in PostgreSQL (Supabase)
search over cafes
    │
    ▼
Retrieve top 5        ← semantically relevant cafes
most relevant cafes
    │
    ▼
Augment prompt        ← cafe data + user taste profile
    │
    ▼
Claude generates      ← Anthropic API
personalised
recommendation
    │
    ▼
Streamed response     ← FastAPI → React frontend
to user
```

**Why RAG and not fine-tuning?**
Fine-tuning would require retraining a model every time a new cafe opens or closes. RAG keeps the knowledge in a database — updatable in seconds, no retraining required. This is why RAG is the standard approach for domain-specific AI applications.

---

## 🛠️ Tech stack

| Layer | Technology | Why this choice |
|-------|-----------|-----------------|
| **Backend** | FastAPI (Python) | Async support, auto docs, production-standard for AI APIs |
| **Embeddings** | sentence-transformers (`all-MiniLM-L6-v2`) | Local, free, no API cost, 384-dim vectors, good quality |
| **Vector DB** | pgvector on PostgreSQL | No extra service needed — vector search inside existing DB |
| **Hosted DB** | Supabase | Free tier, pgvector pre-installed, Frankfurt region |
| **LLM** | Claude API (Anthropic) | Conversational quality, consistent with dev tooling |
| **Frontend** | React + Tailwind | Clean chat interface, Vercel deployment |
| **Deployment** | Railway (backend) + Vercel (frontend) | Free tier, zero infra config, real URL |
| **Dev tooling** | Claude Code (VS Code extension) | AI-assisted development on Ubuntu |

---

## 📁 Project structure

```
brewmind/
├── app/
│   ├── api/
│   │   ├── chat.py          # /chat endpoint — main RAG pipeline
│   │   └── profile.py       # /profile endpoint — user taste profile
│   ├── core/
│   │   ├── config.py        # Environment variables and settings
│   │   └── database.py      # SQLAlchemy connection to Supabase
│   ├── models/
│   │   ├── cafe.py          # Cafe database model
│   │   └── profile.py       # User taste profile model
│   ├── services/
│   │   ├── embedding.py     # sentence-transformers embedding service
│   │   ├── retrieval.py     # pgvector similarity search
│   │   └── claude.py        # Claude API integration + prompt engineering
│   ├── data/
│   │   └── cafes_seed.json  # Curated Munich specialty cafe dataset
│   └── main.py              # FastAPI app entry point
├── scripts/
│   ├── collect_data.py      # Google Places API data collection
│   ├── extract_coffee.py    # Claude-based coffee attribute extraction
│   └── seed_db.py           # Embed and load cafes into Supabase
├── frontend/                # React chat interface
├── tests/                   # pytest test suite
├── .env.example             # Environment variable template
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## 🗄️ Data model

Each cafe in BrewMind has two representations:

**Structured fields** — for filtering and display:
```json
{
  "name": "Man Versus Machine Coffee Roasters",
  "neighborhood": "Isarvorstadt",
  "roast_profile": {
    "value": ["light", "medium-light"],
    "confidence": "high",
    "evidence": "Own roastery, Nordic Approach sourcing, light-focused philosophy"
  },
  "brewing_methods": { "value": ["espresso", "V60", "aeropress", "syphon"] },
  "character": ["third-wave serious"],
  "good_for_working": false,
  "wifi": { "value": false }
}
```

**embed_text** — what actually gets embedded for semantic search:
```
"Man Versus Machine Coffee Roasters is one of Munich's most serious
specialty coffee destinations in Isarvorstadt. They roast their own
beans on site, developing individual roast profiles for each coffee.
Light to medium-light roast style. Brewing methods include espresso,
V60, Aeropress, Syphon, and Kalita. Minimal and uncompromising —
no Latte Macchiato, no flavoured syrups. Quiet on weekday mornings."
```

The `embed_text` is written as natural language — not a list of keywords — because sentence-transformers was trained on natural sentences and understands meaning expressed that way.

**Why one embed_text instead of separate vectors per field?**
A user query expresses a combined intention — *"quiet light roast Schwabing"* is one thought, not three separate searches. Matching one combined query vector against one combined cafe vector preserves the contextual relationship between fields and is computationally cheaper at query time.

---

## 🧠 Key design decisions

**Confidence metadata on all data fields**

Every extracted attribute carries a `confidence` level (`high`, `medium`, `low`, `none`) and an `evidence` string. This is standard data engineering practice — a field marked `medium` triggers human review before it goes into production. Two of the seven seed cafes are flagged `needs_visit: true` where roast profile confidence is medium.

**Local embeddings over API embeddings**

sentence-transformers runs entirely on your local machine. No API call, no cost, no data leaving your system. At portfolio scale (< 1000 cafes), the quality difference vs OpenAI embeddings is negligible. In production at millions of vectors, this decision would be revisited.

**pgvector over dedicated vector databases**

For < 10,000 vectors, pgvector inside PostgreSQL is indistinguishable in performance from Pinecone or Weaviate, but eliminates an entire infrastructure dependency. The decision point for migrating to a dedicated vector DB would be: > 1M vectors, need for hybrid search at scale, or sub-10ms P99 latency requirements.

**Structured extraction with confidence**

Cafe coffee attributes (roast profile, brewing methods, flavour notes) are extracted from unstructured text (Instagram bios, website copy, Google reviews) using Claude API with a structured prompt that returns JSON with confidence levels and evidence quotes. This is the same LLM-based structured extraction pattern used in enterprise data pipelines.

---

## 🚀 Getting started

### Prerequisites
- Python 3.11+
- Supabase account (free)
- Anthropic API key

### Setup

```bash
# Clone the repo
git clone https://github.com/yourusername/brewmind.git
cd brewmind

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Supabase connection string and Anthropic API key

# Run database migrations (creates tables and enables pgvector)
python scripts/setup_db.py

# Seed the database with Munich cafes
python scripts/seed_db.py

# Start the development server
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`
Auto-generated docs at `http://localhost:8000/docs`

### Environment variables

```bash
# .env.example
DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
ANTHROPIC_API_KEY=your-anthropic-api-key
APP_ENV=development
```

---

## 📊 Current dataset

7 curated Munich specialty cafes — hand-researched and verified:

| Cafe | Roast | Character | Data quality |
|------|-------|-----------|-------------|
| Man Versus Machine | Light | Third-wave serious | ✅ Complete |
| Suuapinga | Light | Nordic, accessible | ✅ Complete |
| The Barn | Light only | Internationally renowned | ✅ Complete |
| Café Blá | Light | Nordic, owner-roasted | ✅ Complete |
| Fausto | Medium–Dark | Local institution | 🔄 Needs visit |
| Humpback Whale | Light–Med | Champion-led, intimate | 🔄 Needs visit |
| ALRIGHTY | Mixed | Mission-driven, industrial | ✅ Complete |

---

## 🗺️ Roadmap

**v1 — Munich (current)**
- [x] Curated seed dataset — 7 cafes
- [ ] Database schema + pgvector setup
- [ ] Embedding pipeline
- [ ] RAG search endpoint
- [ ] Claude recommendation generation
- [ ] User taste profile system
- [ ] React chat frontend
- [ ] Railway deployment

**v2 — Expand**
- [ ] Google Places API integration for structured data collection
- [ ] Claude-based extraction pipeline for new cafes
- [ ] Expand to Berlin, Amsterdam, London
- [ ] Home brewing advice module
- [ ] Map view

---

## ✍️ What I learned building this

*This section will be written as the project progresses — honest reflections on what was harder than expected, what broke, and what I'd do differently.*

---

## 📬 Contact

**Vaibhav Singh Tomar**
Senior Data Engineer → AI Engineer
Munich, Germany

[LinkedIn](https://linkedin.com/in/vaibhavtomar/) · [Email](mailto:vaibhav.vst@gmail.com)

---

*Built with Claude Code · Deployed on Railway + Vercel · Data from Google Places API, Instagram, and personal cafe visits*
