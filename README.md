# Legal Email Assistant

A full-stack, production-quality portfolio project showcasing a legal email AI assistant with a Python backend (FastAPI + LangChain + LangGraph + Gemini) and a modern Next.js + Tailwind + Material UI frontend.

## Highlights

- Two-step AI workflow using LangGraph:
  1) Analyze legal email to structured JSON
  2) Draft a professional legal reply referencing clauses 9.1, 9.2, 10.2
- Gemini LLM (via `langchain-google-genai`) with safe JSON parsing
- RAG-lite: FAISS vector store for contract clauses (with fallback when offline)
- In-memory + optional SQLite cache
- Rate limiting middleware
- Pydantic schemas, strong typing, and error handling
- Optional “debug” mode logs internal reasoning trace (without revealing chain-of-thought to users)
- Automated tests with pytest + TestClient
- Modern UI: Next.js, Tailwind, MUI, Framer Motion animations, JSON viewer, Compare Drafts, dark mode, and export

## Architecture

```mermaid
flowchart LR
  A[Frontend (Next.js)] -- /api --> B[FastAPI]
  B -- LangGraph --> C[Analyze Node]
  B -- LangGraph --> D[Draft Node]
  D -- Retrieval --> E[Vector Store (FAISS)]
  C & D -- LLM --> F[Gemini via LangChain]
  B -- Cache --> G[SQLite / Memory]
```

## Repository Structure

```
backend/
  api/
    main.py          # FastAPI app, CORS, rate limiting, routes
    routes.py        # /api/analyze, /api/draft, /api/process
  agents/
    analyze_node.py  # Node 1: email analysis -> JSON
    draft_node.py    # Node 2: draft reply (uses retrieval + analysis)
    graph.py         # LangGraph wiring + runner
  models/
    schemas.py       # Pydantic schemas
  services/
    llm.py           # Gemini wrapper; mock fallback for offline
    cache.py         # Memory + SQLite cache with TTL
    vectorstore.py   # FAISS retrieval; fallback if embeddings unavailable
  tests/
    test_analysis.py # API + analyzer tests
    test_drafting.py # Draft + process pipeline tests
    test_vectorstore.py
  contract/
    default_snippet.txt
  .env               # GEMINI_API_KEY=YOUR_GEMINI_API_KEY
  requirements.txt
frontend/
  src/
    pages/
      _app.js
      index.js
    components/
      Editor.js, AnalysisViewer.js, DraftPreview.js, Sidebar.js, ThemeToggle.js, CompareDrafts.js
    hooks/
      useLocalStorage.js
    styles/
      globals.css
  package.json
  tailwind.config.js
  postcss.config.js
```

## Backend: Running Locally

1) Create and activate a virtualenv (optional) and install requirements.
2) Add your key in `backend/.env`:

```
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```

3) Start the API server (default http://localhost:8000):

```powershell
cd backend
python -m pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
```

- Health: GET http://localhost:8000/health
- API base: http://localhost:8000/api

### API Endpoints

- POST /api/analyze
  - body: { email_text: string, contract_snippet?: string, debug?: boolean }
  - returns: Analysis JSON
- POST /api/draft
  - body: { email_text: string, analysis?: AnalysisJSON, contract_snippet?: string, debug?: boolean }
  - returns: { draft: string, risk_score?: number }
- POST /api/process
  - body: { email_text: string, contract_snippet?: string, debug?: boolean }
  - returns: { analysis: AnalysisJSON, draft: string, risk_score?: number }

### Tests

```powershell
cd backend
pytest -q
```

Note: If `GEMINI_API_KEY` is not set, the backend uses a deterministic Mock LLM so tests still pass.

## Frontend: Running Locally

1) Install dependencies and start dev server (http://localhost:3000):

```powershell
cd frontend
npm install
npm run dev
```

2) Ensure the backend is running at http://localhost:8000. The frontend calls `NEXT_PUBLIC_API_BASE` (defaults to this URL). To change:

```powershell
# Example
$env:NEXT_PUBLIC_API_BASE = "http://localhost:8001"; npm run dev
```

## Screenshots (placeholders)

- Analysis JSON viewer
- Draft preview with export
- Compare Drafts side-by-side

## Prompt Versioning

- Analyze prompt version: 1.0.0
- Draft prompt version: 1.0.0

These are defined in `backend/services/llm.py` and included in cache keys.

## Why This Project Stands Out

- Clear, modular architecture and strong typing
- Production-minded: rate limiting, caching, environment management
- RAG-ready via FAISS with graceful fallbacks
- Automated tests and local-offline mock to ensure CI stability
- Polished UI with animations, theme support, and power-user features (compare drafts, autosave, export)

## Roadmap

- Multi-document contract ingestion, chunking, and advanced retrieval
- User auth + saved histories
- PDF export backend service
- Milvus/pgvector integration for scalable vector stores
- Fine-grained risk analysis with explanations (internal-only logs)
- Organization style guide tuning and prompt A/B testing

## Troubleshooting

- If imports like `langgraph` or `langchain-google-genai` fail, confirm versions in `backend/requirements.txt` and re-install.
- FAISS optional: If embedding or FAISS errors occur, the system falls back to a basic snippet loader.
- CORS issues: backend has permissive CORS; confirm ports (8000 API, 3000 frontend).
