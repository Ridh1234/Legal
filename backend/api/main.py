import os
import time
import logging
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from dotenv import load_dotenv

from .routes import router as api_router

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("legal-email-assistant")

# Simple in-memory rate limiter (per-IP)
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.allowance = {}
        self.window = 60

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "anonymous"
        import time
        now = int(time.time())
        bucket = self.allowance.get(client_ip)
        if not bucket:
            bucket = {"reset": now + self.window, "count": 0}
            self.allowance[client_ip] = bucket
        if now > bucket["reset"]:
            bucket["reset"] = now + self.window
            bucket["count"] = 0
        bucket["count"] += 1
        if bucket["count"] > self.requests_per_minute:
            retry_after = max(1, bucket["reset"] - now)
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
                headers={"Retry-After": str(retry_after)},
            )
        response: Response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.requests_per_minute - bucket["count"]))
        response.headers["X-RateLimit-Reset"] = str(bucket["reset"])
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Structured request logging so you see every API hit in the terminal."""
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        client_ip = request.client.host if request.client else "?"
        path = request.url.path
        method = request.method
        try:
            response: Response = await call_next(request)
            status = response.status_code
        except Exception as e:
            status = 500
            logger.exception(f"Unhandled exception on {method} {path}: {e}")
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.info(f"ACCESS {client_ip} {method} {path} {status} {duration_ms:.1f}ms")
        return response


def create_app() -> FastAPI:
    app = FastAPI(title="Legal Email Assistant", version="0.1.0")

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Logging middleware first so it wraps everything, then rate limiting
    app.add_middleware(LoggingMiddleware)

    # Rate limiting
    rpm = int(os.getenv("REQUESTS_PER_MINUTE", "60"))
    app.add_middleware(RateLimitMiddleware, requests_per_minute=rpm)

    # Routes
    app.include_router(api_router, prefix="/api")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
