from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .catalog import STOCKS
from .config import ROOT_DIR, settings
from .data import MarketDataError
from .service import market_overview, repository, stock_analysis
from .strategies import STRATEGIES, StrategyName


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="A-share daily research, strategy signals and backtesting API.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name, "version": "0.1.0"}


@app.get("/api/stocks")
def stocks() -> dict[str, object]:
    return {
        "stocks": [{"symbol": symbol, **metadata} for symbol, metadata in STOCKS.items()],
        "strategies": [{"id": strategy, **metadata} for strategy, metadata in STRATEGIES.items()],
    }


@app.get("/api/overview")
def overview() -> dict[str, object]:
    return market_overview()


@app.get("/api/stocks/{symbol}/analysis")
def analysis(
    symbol: str,
    strategy: StrategyName = Query(default="trend"),
    chart_bars: int = Query(default=260, ge=120, le=520),
) -> dict[str, object]:
    if symbol not in STOCKS:
        raise HTTPException(status_code=404, detail="不支持的股票代码")
    return stock_analysis(symbol, strategy, chart_bars=chart_bars)


@app.post("/api/stocks/{symbol}/refresh")
def refresh(
    symbol: str,
    source: Literal["auto", "akshare", "demo"] = Query(default="auto"),
) -> dict[str, object]:
    if symbol not in STOCKS:
        raise HTTPException(status_code=404, detail="不支持的股票代码")
    try:
        bars, meta = repository.refresh(symbol, source)
    except MarketDataError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"symbol": symbol, "bar_count": len(bars), "data_meta": meta}


frontend_dist = ROOT_DIR / "frontend" / "dist"
if frontend_dist.exists():
    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str) -> FileResponse:
        requested = frontend_dist / path
        if path and requested.is_file() and frontend_dist in requested.resolve().parents:
            return FileResponse(requested)
        return FileResponse(frontend_dist / "index.html")

