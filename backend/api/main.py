"""FastAPI gateway — VN Stock Advisory API.

Endpoints:
  GET /health
  GET /api/v1/screener
  GET /api/v1/stock/{ticker}
  GET /api/v1/valuation/{ticker}

CORS origins read from env CORS_ORIGINS (comma-separated).
Data source injected via app.state.stock_service for testability.
"""

import os
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

try:
    from prometheus_fastapi_instrumentator import Instrumentator
    # Probe compatibility: expose() calls add_route which varies by starlette version.
    # A quick attribute check is enough — actual wiring happens inside create_app().
    _PROMETHEUS_OK = hasattr(Instrumentator, "expose")
except (ImportError, Exception):
    _PROMETHEUS_OK = False

from backend.api.models import (
    DISCLAIMER,
    FinancialsResponse,
    ScreenerResponse,
    StockDetail,
    ValuationResponse,
)
from backend.api.stock_service import StockService

# ---------------------------------------------------------------------------
# CORS — env-driven (audit C2)
# ---------------------------------------------------------------------------

_DEFAULT_ORIGINS = "http://localhost:3000,http://localhost:3001"
_CORS_ORIGINS = [
    o.strip()
    for o in os.environ.get("CORS_ORIGINS", _DEFAULT_ORIGINS).split(",")
    if o.strip()
]

# ---------------------------------------------------------------------------
# App factory — accepts injected service for DI / tests
# ---------------------------------------------------------------------------


def create_app(stock_service: Optional[StockService] = None) -> FastAPI:
    """Build and configure the FastAPI application.

    Args:
        stock_service: Pre-built StockService; if None, the default
                       CachedDataSource(VnstockSource()) is constructed lazily
                       on first request.
    """
    app = FastAPI(
        title="VN Stock Advisory API",
        description="P2 screener + P3 valuation endpoints for VN equities",
        version="2.0.0",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Prometheus (optional — skip if incompatible with installed starlette)
    if _PROMETHEUS_OK:
        try:
            Instrumentator().instrument(app).expose(app)
        except Exception as _prom_err:
            logger.warning(f"Prometheus instrumentation skipped: {_prom_err}")

    # Store service on app state; build default lazily if not injected
    app.state.stock_service = stock_service  # may be None until first request

    # ------------------------------------------------------------------
    # Dependency helper
    # ------------------------------------------------------------------

    def _get_service(request: Request) -> StockService:
        svc = request.app.state.stock_service
        if svc is None:
            svc = _build_default_service()
            request.app.state.stock_service = svc
        return svc

    # ------------------------------------------------------------------
    # Routes
    # ------------------------------------------------------------------

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "vn-stock-advisory"}

    @app.get("/api/v1/screener", response_model=ScreenerResponse)
    async def get_screener(request: Request):
        """Ranked watchlist from P2 screener engine."""
        svc = _get_service(request)
        items = svc.get_screener()
        return ScreenerResponse(items=items, count=len(items), disclaimer=DISCLAIMER)

    @app.get("/api/v1/stock/{ticker}", response_model=StockDetail)
    async def get_stock(ticker: str, request: Request):
        """Price summary + company info + key ratios for a ticker."""
        svc = _get_service(request)
        detail = svc.get_stock_detail(ticker.upper())
        if detail is None:
            raise HTTPException(status_code=404, detail=f"Ticker {ticker} not found")
        return detail

    @app.get("/api/v1/stock/{ticker}/financials", response_model=FinancialsResponse)
    async def get_stock_financials(ticker: str, request: Request, period_type: str = "year"):
        """Stored BS/IS/CF statements for a ticker (collected from vnstock → DB)."""
        svc = _get_service(request)
        return svc.get_financials(ticker.upper(), period_type)

    @app.get("/api/v1/valuation/{ticker}", response_model=ValuationResponse)
    async def get_valuation(ticker: str, request: Request):
        """Full valuation pipeline (DCF + relative + quality) for a ticker."""
        svc = _get_service(request)
        result = svc.get_valuation(ticker.upper())
        if result is None:
            raise HTTPException(status_code=404, detail=f"Valuation failed for {ticker}")
        return result

    # ------------------------------------------------------------------
    # Generic error handler
    # ------------------------------------------------------------------

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        logger.error(f"Unhandled error on {request.url}: {exc}")
        return JSONResponse(status_code=500, content={"error": "Internal server error"})

    return app


def _build_default_service() -> StockService:
    """Construct default production service — called lazily on first request."""
    from data.vn import build_default_source
    from config import system  # noqa: F401 — reads cache_dir from config

    try:
        import yaml
        with open("config/system.yaml") as f:
            sys_cfg = yaml.safe_load(f) or {}
        cache_dir = sys_cfg.get("cache_dir", "./data/cache")
    except Exception:
        cache_dir = "./data/cache"

    source = build_default_source(cache_dir=cache_dir)
    logger.info(f"Default StockService built (DNSE OHLCV + vnstock fundamentals), cache_dir={cache_dir}")
    return StockService(source)


# Module-level app instance (used by uvicorn / gunicorn)
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8090, reload=True)
