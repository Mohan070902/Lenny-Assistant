# The Lenny Growth Assistant
> **An enterprise-grade, retrieval-augmented generation (RAG) conversational assistant and content synthesis engine strictly grounded in Lenny’s Podcast transcripts.**

Built as a Forward Deployed Engineer take-home assessment, **The Lenny Growth Assistant** empowers product managers, growth leaders, and founders to extract operational tactics from 50+ podcast episodes. The system features exact transcript citations, a dedicated **Ship 30 for 30** long-form essay synthesizer, an in-app side-by-side **Sandboxed Artifact Viewer** (modeled after Claude Artifacts), and seamless runtime toggling between **Local Ollama** models and **Cloud LLMs** (Claude, OpenAI, Gemini).

---

## Architecture Overview

```
lenny-growth-assistant/
├── .env.example               # Complete environment template with safe defaults
├── docker-compose.yml         # 1-command startup: Postgres (pgvector) + Backend + Frontend
├── README.md                  # System overview & operational handoff documentation
├── docs/
│   ├── PRD.md                 # User personas, JTBD, measurable metrics, trade-off matrix
│   ├── architecture.md        # Database schema, API contracts, sequence flows, topology
│   └── design.md              # UI/UX principles, design tokens, accessibility specs
├── agent_transcripts/
│   ├── 01_initial_scaffolding.md
│   ├── 02_debugging_pgvector_indexing.md
│   └── 03_security_and_sandbox_hardening.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── scripts/
│   │   ├── download_transcripts.py  # Ingests 50 markdown transcripts from GitHub
│   │   └── ingest.py                # Semantic chunking, speaker preservation & pgvector storage
│   ├── app/
│   │   ├── main.py            # FastAPI ASGI app with lifespan events & CORS
│   │   ├── config.py          # Pydantic v2 Settings management
│   │   ├── database.py        # Async SQLAlchemy engine with SQLite fallback
│   │   ├── models/            # Relational models & Pydantic request/response schemas
│   │   ├── providers/         # Multi-provider LLM abstraction (Ollama, Claude, OpenAI)
│   │   ├── rag/               # Vector embeddings & cosine distance retriever
│   │   ├── skills/            # Ship 30 for 30 essay engine & Artifact XML parser
│   │   └── api/               # REST & SSE streaming routers (/sessions, /chat, /health)
│   └── tests/                 # Automated pytest suite (12 passing tests)
└── frontend/
    ├── Dockerfile             # Multi-stage build served via Alpine Nginx
    ├── nginx.conf             # Reverse proxy routing /api/ to backend with SPA fallback
    ├── package.json           # React 18 + Vite + TypeScript + Tailwind CSS
    └── src/
        ├── App.tsx            # Main dual-pane layout & state coordination
        ├── components/
        │   ├── Chat/          # Chat thread, session sidebar, model selector, source chips
        │   └── Artifact/      # Sandboxed iframe with DOMPurify & code inspector
        ├── hooks/             # useChatStream SSE streaming hook
        └── lib/               # Typed API client
```

---

## Key Features

1. **Strictly Grounded Answers & Citations:**
   - Retrieves semantic chunks using 384-dimensional vector embeddings with cosine similarity.
   - Every factual claim cites the guest and episode: `[Episode: <Title> (Guest: <Name>), Time: <Timestamp>]`.
   - **Out-of-domain guardrail:** Explicitly acknowledges when Lenny’s archive does not cover a topic, preventing hallucinations.

2. **Ship 30 for 30 Content Engine:**
   - Dedicated writing skill transforming podcast insights into a ~1,250-word high-retention essay.
   - Enforces Ship 30 heuristics: irresistible hook, short 1–3 sentence paragraphs, subheadings, bold anchors on bullets, and an actionable implementation framework.

3. **Claude-Style In-App Artifact Viewer:**
   - Dynamically detects and renders generated Markdown documents or interactive HTML/CSS components side-by-side with the chat.
   - **Defense-in-Depth Security:** HTML artifacts are sanitized via `DOMPurify` and isolated inside an `<iframe>` configured with `sandbox="allow-scripts"` (strictly omitting `allow-same-origin`), guaranteeing that generated code cannot access parent cookies, local storage, or DOM.
   - Includes **Preview**, **Code View**, **Copy to Clipboard**, **Download**, and **Fullscreen Toggle**.

4. **Dual Model Layer (Local Ollama & Cloud):**
   - **Local Model (Mandatory for Demo):** Runs offline using Ollama (`llama3.2:3b`, `llama3.1:8b`, or `mistral:7b`) at zero cost.
   - **Cloud Models:** Supports Anthropic Claude (`claude-3-5-sonnet`), OpenAI (`gpt-4o`), and Google Gemini (`gemini-1.5-flash`).
   - Switchable instantaneously in the UI via the top bar without restarting the app.

---

## Prerequisites

- **Docker & Docker Compose** (v24.0+)
- **Ollama** (for local model demo) — [Download Ollama](https://ollama.com)
  - Recommended model: `ollama run llama3.2:3b` or `ollama run llama3.1:8b`
- *(Optional for cloud inference)* An API key for Anthropic, OpenAI, or Gemini.

---

## Quickstart (One-Command Startup)

### 1. Clone & Configure Environment
```bash
git clone https://github.com/your-username/lenny-growth-assistant.git
cd lenny-growth-assistant

# Copy example environment file
cp .env.example .env
```

### 2. Start Services via Docker Compose
```bash
docker-compose up --build
```
This orchestrates:
- **`db`**: PostgreSQL 16 with `pgvector` on port `5432` (health check enabled).
- **`backend`**: FastAPI ASGI server on port `8000`.
- **`frontend`**: Production React build served via Nginx on port `3000`.

Open your browser at **`http://localhost:3000`**.

---

## Local Development (Without Docker)

### 1. Backend Setup
```bash
cd backend
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt

# Download podcast transcripts (50 episodes)
python scripts/download_transcripts.py

# Ingest transcripts into vector index / local cache
python scripts/ingest.py

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open **`http://localhost:3000`** (or `http://localhost:5173`).

---

## Automated Test Suite

Run the full pytest suite covering API contracts, health probes, model fallbacks, vector embeddings, and artifact parsing:

```bash
cd backend
.venv\Scripts\pytest -v
```

**Results:**
```text
tests/test_api.py::test_root_endpoint PASSED                             [  8%]
tests/test_api.py::test_health_endpoint PASSED                           [ 16%]
tests/test_providers.py::test_provider_factory_default PASSED            [ 25%]
tests/test_providers.py::test_provider_factory_cloud PASSED              [ 33%]
tests/test_providers.py::test_ollama_provider_unreachable PASSED         [ 41%]
tests/test_providers.py::test_cloud_provider_missing_keys PASSED         [ 50%]
tests/test_retrieval.py::test_compute_embedding_dimension_and_norm PASSED [ 58%]
tests/test_retrieval.py::test_batch_embeddings PASSED                    [ 66%]
tests/test_retrieval.py::test_fallback_file_retriever PASSED             [ 75%]
tests/test_skills.py::test_ship30_prompt_formatting PASSED               [ 83%]
tests/test_skills.py::test_artifact_extraction_html PASSED               [ 91%]
tests/test_skills.py::test_artifact_extraction_markdown PASSED           [100%]

============================= 12 passed in 8.03s ==============================
```

---

## Demo Video Script (2–3 Minutes)

When recording your demonstration:
1. **Introduction (0:00–0:30):**
   - Introduce yourself and the objective: *Turning 200+ hours of Lenny's Podcast into an actionable, grounded growth advisor.*
2. **Local Ollama Grounded Q&A (0:30–1:15):**
   - Show the model toggle set to **Local (Ollama)**.
   - Ask: *"What did Adam Mosseri say about AI and taste in product design?"*
   - Highlight the streaming tokens, low latency, and the expandable **Grounded in Podcast Sources** chip citing Adam Mosseri's episode and timestamp.
3. **Ship 30 for 30 Skill (1:15–1:45):**
   - Switch the mode toggle to **Ship 30 for 30**.
   - Ask: *"Write a Ship 30 for 30 essay on finding product-market fit."*
   - Point out the structured format: curiosity hook, 1–3 sentence paragraphs, bold bullet anchors, and actionable takeaways.
4. **Sandboxed Artifact Viewer (1:45–2:30):**
   - Ask: *"Generate an interactive HTML/CSS ROI calculator for growth experiments."*
   - Show the Artifact Viewer automatically sliding out on the right.
   - Interact with the sliders and buttons inside the iframe.
   - Highlight the security badge: `sandbox="allow-scripts"` with parent DOM isolation.
5. **Engineering Trade-off Discussion (2:30–3:00):**
   - Briefly discuss the trade-off between local 3B/8B model speed vs. 70B cloud reasoning, and how the hybrid routing layer provides the best of both worlds.

---

## Operational Handoff & Client Troubleshooting

| Symptom | Probable Cause | Immediate Remediation |
| :--- | :--- | :--- |
| `Ollama Unreachable` warning in chat | Ollama daemon is not running locally | Start Ollama (`ollama serve`) or run `ollama run llama3.2:3b`. |
| `Cloud Provider Not Configured` | API keys missing in `.env` | Add `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in `.env`, or toggle to Local Ollama. |
| Database connection error | PostgreSQL container not ready | Verify Docker container status: `docker-compose ps`. Check logs: `docker-compose logs db`. The app also has an instant auto-fallback to local SQLite (`./lenny_assistant.db`). |
| Empty retrieval results | Query out of domain or transcripts not indexed | Run `python backend/scripts/ingest.py` to ensure chunks are loaded. |

---

## License & Compliance
This software is developed for evaluation purposes. Transcript data is utilized under fair research principles based on Lenny's public starter pack.
