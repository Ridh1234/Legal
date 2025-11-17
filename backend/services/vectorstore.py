import os
import logging
from typing import List

from dotenv import load_dotenv

try:
    import faiss  # type: ignore
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    from langchain.docstore.document import Document
    from langchain_community.vectorstores import FAISS
    HAVE_FAISS = True
except Exception:
    HAVE_FAISS = False

load_dotenv()
logger = logging.getLogger(__name__)

_VECTOR_DIR = os.getenv("VECTOR_DB_DIR") or os.path.join(os.path.dirname(__file__), "..", "data", "vectorstore")
_CONTRACT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "contract"))
_DEFAULT_SNIPPET = os.path.join(_CONTRACT_DIR, "default_snippet.txt")

_INDEX = None


def _load_contract_snippets() -> List[str]:
    snippets: List[str] = []
    try:
        if os.path.exists(_DEFAULT_SNIPPET):
            with open(_DEFAULT_SNIPPET, "r", encoding="utf-8") as f:
                text = f.read().strip()
                if text:
                    snippets.append(text)
    except Exception as e:
        logger.warning(f"Failed to load default contract snippet: {e}")
    return snippets


def _ensure_index():
    global _INDEX
    if _INDEX is not None:
        return
    if not HAVE_FAISS:
        logger.warning("FAISS or embeddings not available; using simple fallback retrieval")
        _INDEX = False
        return
    snippets = _load_contract_snippets()
    if not snippets:
        _INDEX = False
        return
    texts = snippets
    docs = [Document(page_content=t) for t in texts]
    # Try latest embedding model first, fallback to legacy
    emb_model = os.getenv("GEMINI_EMBEDDING_MODEL") or "text-embedding-004"
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model=emb_model, api_key=os.getenv("GEMINI_API_KEY"))
    except Exception:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", api_key=os.getenv("GEMINI_API_KEY"))
    _INDEX = FAISS.from_documents(docs, embeddings)
    try:
        os.makedirs(_VECTOR_DIR, exist_ok=True)
    except Exception:
        pass


def retrieve_relevant_clauses(query: str, k: int = 3) -> str:
    _ensure_index()
    if not query:
        # default fallback
        try:
            with open(_DEFAULT_SNIPPET, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            return ""
    if _INDEX is False or _INDEX is None:
        # naive fallback: return default snippet if any keyword from query overlaps
        base = ""
        try:
            with open(_DEFAULT_SNIPPET, "r", encoding="utf-8") as f:
                base = f.read().strip()
        except Exception:
            return ""
        # crude filter
        q_words = set([w.lower() for w in query.split() if len(w) > 3])
        if any(w in base.lower() for w in q_words):
            return base
        return base[:1000]

    try:
        results = _INDEX.similarity_search(query, k=k)
        return "\n\n".join([d.page_content for d in results])
    except Exception as e:
        logger.warning(f"Vector search failed: {e}")
        try:
            with open(_DEFAULT_SNIPPET, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            return ""
