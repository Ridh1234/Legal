<div align="center"># Legal Email Assistant



# Legal Email AssistantA full-stack, production-quality portfolio project showcasing a legal email AI assistant with a Python backend (FastAPI + LangChain + LangGraph + Gemini) and a modern Next.js + Tailwind + Material UI frontend.



### AI-Powered Legal Response Generation with RAG## Highlights



A production-grade full-stack application that analyzes legal emails and generates professional responses using LangChain, LangGraph, and Google Gemini LLM with intelligent contract clause retrieval.- Two-step AI workflow using LangGraph:

  1) Analyze legal email to structured JSON

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)  2) Draft a professional legal reply referencing clauses 9.1, 9.2, 10.2

[![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)- Gemini LLM (via `langchain-google-genai`) with safe JSON parsing

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org/)- RAG-lite: FAISS vector store for contract clauses (with fallback when offline)

[![LangChain](https://img.shields.io/badge/LangChain-121212?style=for-the-badge)](https://langchain.com/)- In-memory + optional SQLite cache

[![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)- Rate limiting middleware

- Pydantic schemas, strong typing, and error handling

</div>- Optional “debug” mode logs internal reasoning trace (without revealing chain-of-thought to users)

- Automated tests with pytest + TestClient

---- Modern UI: Next.js, Tailwind, MUI, Framer Motion animations, JSON viewer, Compare Drafts, dark mode, and export



## Overview## Architecture



This application demonstrates enterprise-grade AI engineering with a two-stage LangGraph workflow, retrieval-augmented generation (RAG), and a polished React frontend. Built to showcase production-ready practices including caching, rate limiting, comprehensive testing, and graceful degradation.```mermaid

flowchart LR

## Screenshots  A[Frontend (Next.js)] -- /api --> B[FastAPI]

  B -- LangGraph --> C[Analyze Node]

<div align="center">  B -- LangGraph --> D[Draft Node]

  D -- Retrieval --> E[Vector Store (FAISS)]

### System Architecture  C & D -- LLM --> F[Gemini via LangChain]

![Architecture Diagram](architecture.png)  B -- Cache --> G[SQLite / Memory]

```

### User Interface

![Application Interface](interface.png)## Repository Structure



</div>```

backend/

## Key Features  api/

    main.py          # FastAPI app, CORS, rate limiting, routes

### Backend (FastAPI + LangChain)    routes.py        # /api/analyze, /api/draft, /api/process

- **LangGraph State Machine**: Two-node AI workflow for email analysis and response generation  agents/

- **RAG with FAISS**: Semantic search over contract clauses with intelligent retrieval    analyze_node.py  # Node 1: email analysis -> JSON

- **Google Gemini Integration**: Production LLM via `langchain-google-genai` with structured output parsing    draft_node.py    # Node 2: draft reply (uses retrieval + analysis)

- **Dual-Layer Caching**: In-memory + SQLite for performance optimization    graph.py         # LangGraph wiring + runner

- **Production Middleware**: Rate limiting, CORS, comprehensive error handling  models/

- **Type Safety**: Pydantic schemas throughout with strict validation    schemas.py       # Pydantic schemas

- **Automated Testing**: Pytest suite with mock LLM for CI/CD stability  services/

    llm.py           # Gemini wrapper; mock fallback for offline

### Frontend (Next.js + React)    cache.py         # Memory + SQLite cache with TTL

- **Modern UI/UX**: Material-UI components with Tailwind CSS styling    vectorstore.py   # FAISS retrieval; fallback if embeddings unavailable

- **Interactive Features**: Real-time JSON analysis viewer, draft comparison, dark mode  tests/

- **Smooth Animations**: Framer Motion for professional transitions    test_analysis.py # API + analyzer tests

- **Export Capabilities**: PDF and Word document generation    test_drafting.py # Draft + process pipeline tests

- **Responsive Design**: Mobile-first approach with adaptive layouts    test_vectorstore.py

  contract/

## Technical Architecture    default_snippet.txt

  .env               # GEMINI_API_KEY=YOUR_GEMINI_API_KEY

```mermaid  requirements.txt

flowchart LRfrontend/

  A[Next.js Frontend] -->|REST API| B[FastAPI Backend]  src/

  B --> C[LangGraph Orchestrator]    pages/

  C --> D[Analysis Node]      _app.js

  C --> E[Draft Node]      index.js

  E -->|Semantic Search| F[FAISS Vector Store]    components/

  D & E -->|LLM Calls| G[Google Gemini]      Editor.js, AnalysisViewer.js, DraftPreview.js, Sidebar.js, ThemeToggle.js, CompareDrafts.js

  B -->|Cache Layer| H[SQLite + Memory]    hooks/

        useLocalStorage.js

  style A fill:#0070f3    styles/

  style B fill:#009688      globals.css

  style G fill:#4285f4  package.json

  style F fill:#ff6b6b  tailwind.config.js

```  postcss.config.js

```

## Workflow Pipeline

## Backend: Running Locally

1. **Email Input** → User submits legal email via React interface

2. **Analysis Phase** → LangGraph Node 1 extracts structured data (parties, topics, risk assessment)1) Create and activate a virtualenv (optional) and install requirements.

3. **Retrieval Phase** → FAISS searches contract clauses relevant to identified topics2) Add your key in `backend/.env`:

4. **Generation Phase** → LangGraph Node 2 synthesizes professional legal response

5. **User Review** → Interactive UI displays analysis JSON and draft with export options```

GEMINI_API_KEY=YOUR_GEMINI_API_KEY

---```



## Quick Start3) Start the API server (default http://localhost:8000):



### Prerequisites```powershell

- Python 3.10+cd backend

- Node.js 18+python -m pip install -r requirements.txt

- Google Gemini API keyuvicorn api.main:app --reload --port 8000

```

### Backend Setup

- Health: GET http://localhost:8000/health

```bash- API base: http://localhost:8000/api

cd backend

python -m pip install -r requirements.txt### API Endpoints



# Create .env file- POST /api/analyze

echo "GEMINI_API_KEY=your_api_key_here" > .env  - body: { email_text: string, contract_snippet?: string, debug?: boolean }

  - returns: Analysis JSON

# Start server- POST /api/draft

uvicorn api.main:app --reload --port 8000  - body: { email_text: string, analysis?: AnalysisJSON, contract_snippet?: string, debug?: boolean }

```  - returns: { draft: string, risk_score?: number }

- POST /api/process

**API Endpoints:**  - body: { email_text: string, contract_snippet?: string, debug?: boolean }

- `GET /health` - Health check  - returns: { analysis: AnalysisJSON, draft: string, risk_score?: number }

- `POST /api/analyze` - Extract structured data from email

- `POST /api/draft` - Generate legal response draft### Tests

- `POST /api/process` - Full pipeline (analyze + draft)

```powershell

### Frontend Setupcd backend

pytest -q

```bash```

cd frontend

npm installNote: If `GEMINI_API_KEY` is not set, the backend uses a deterministic Mock LLM so tests still pass.

npm run dev

```## Frontend: Running Locally



Access the application at `http://localhost:3000`1) Install dependencies and start dev server (http://localhost:3000):



### Running Tests```powershell

cd frontend

```bashnpm install

cd backendnpm run dev

pytest -q```

```

2) Ensure the backend is running at http://localhost:8000. The frontend calls `NEXT_PUBLIC_API_BASE` (defaults to this URL). To change:

Tests run with mock LLM if `GEMINI_API_KEY` is not set, ensuring CI/CD compatibility.

```powershell

---# Example

$env:NEXT_PUBLIC_API_BASE = "http://localhost:8001"; npm run dev

## Project Structure```



```## Screenshots (placeholders)

backend/

├── api/- Analysis JSON viewer

│   ├── main.py              # FastAPI app with middleware- Draft preview with export

│   └── routes.py            # API endpoint definitions- Compare Drafts side-by-side

├── agents/

│   ├── analyze_node.py      # Email analysis logic## Prompt Versioning

│   ├── draft_node.py        # Response generation logic

│   ├── graph.py             # LangGraph orchestration- Analyze prompt version: 1.0.0

│   └── heuristics.py        # Business rules- Draft prompt version: 1.0.0

├── services/

│   ├── llm.py               # Gemini LLM wrapperThese are defined in `backend/services/llm.py` and included in cache keys.

│   ├── cache.py             # Caching layer

│   └── vectorstore.py       # FAISS retrieval## Why This Project Stands Out

├── models/

│   └── schemas.py           # Pydantic data models- Clear, modular architecture and strong typing

└── tests/                   # Comprehensive test suite- Production-minded: rate limiting, caching, environment management

- RAG-ready via FAISS with graceful fallbacks

frontend/- Automated tests and local-offline mock to ensure CI stability

├── src/- Polished UI with animations, theme support, and power-user features (compare drafts, autosave, export)

│   ├── pages/

│   │   ├── _app.js          # Next.js app wrapper## Roadmap

│   │   └── index.js         # Main application page

│   ├── components/- Multi-document contract ingestion, chunking, and advanced retrieval

│   │   ├── Editor.js        # Email input component- User auth + saved histories

│   │   ├── AnalysisViewer.js- PDF export backend service

│   │   ├── DraftPreview.js- Milvus/pgvector integration for scalable vector stores

│   │   └── CompareDrafts.js- Fine-grained risk analysis with explanations (internal-only logs)

│   └── hooks/- Organization style guide tuning and prompt A/B testing

│       └── useLocalStorage.js

└── styles/## Troubleshooting

    └── globals.css          # Tailwind + custom styles

```- If imports like `langgraph` or `langchain-google-genai` fail, confirm versions in `backend/requirements.txt` and re-install.

- FAISS optional: If embedding or FAISS errors occur, the system falls back to a basic snippet loader.

---- CORS issues: backend has permissive CORS; confirm ports (8000 API, 3000 frontend).


## Technology Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | Next.js 14, React 18, Material-UI, Tailwind CSS, Framer Motion |
| **Backend** | FastAPI, Uvicorn, Python 3.10+ |
| **AI/ML** | LangChain, LangGraph, Google Gemini, FAISS |
| **Data** | SQLite, Pydantic |
| **Testing** | Pytest, httpx |
| **DevOps** | Python-dotenv, Watchfiles |

---

## Production Considerations

### Implemented
- Rate limiting to prevent API abuse
- Dual-layer caching for performance
- Graceful degradation with mock LLM fallback
- Comprehensive error handling
- CORS configuration for cross-origin requests
- Environment-based configuration
- Automated testing suite

### Roadmap
- User authentication and session management
- Multi-document contract ingestion
- Advanced chunking strategies for long documents
- Vector database scaling (Milvus/pgvector)
- Prompt versioning and A/B testing
- Real-time collaboration features
- PDF export backend service

---

## Configuration

### Environment Variables

**Backend (`backend/.env`):**
```env
GEMINI_API_KEY=your_gemini_api_key
CACHE_TTL=3600
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

**Frontend:**
```env
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

---

## API Examples

### Analyze Email
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "email_text": "We need to discuss the delivery timeline...",
    "contract_snippet": "Clause 9.1: Delivery must occur within 30 days..."
  }'
```

### Generate Draft Response
```bash
curl -X POST http://localhost:8000/api/process \
  -H "Content-Type: application/json" \
  -d '{
    "email_text": "When can we expect delivery?",
    "debug": false
  }'
```

---

## Why This Project Stands Out

- **Production-Ready Architecture**: Not a proof-of-concept, but a fully functional application
- **Modern AI Stack**: Leverages cutting-edge LangChain/LangGraph patterns
- **Type Safety**: End-to-end type checking with Pydantic
- **Comprehensive Testing**: Mock strategies ensure CI/CD reliability
- **Polished UX**: Professional interface with animations and thoughtful interactions
- **Scalable Design**: Modular structure ready for enterprise deployment

---

## Troubleshooting

**Import errors for `langgraph` or `langchain-google-genai`:**
- Verify `backend/requirements.txt` versions and reinstall dependencies

**FAISS/embedding errors:**
- System automatically falls back to basic snippet loader

**CORS issues:**
- Confirm backend runs on port 8000 and frontend on port 3000
- Check CORS configuration in `backend/api/main.py`

**Tests failing:**
- Ensure mock LLM is properly configured
- Run `pytest -v` for detailed output

---

<div align="center">

**Built with modern AI engineering practices | Ready for production deployment**

</div>
