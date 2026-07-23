from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from api.app.core.config import ROOT_DIR, settings
from api.app.core.logging import configure_logging
from api.app.routes import admin, ai, backtests, feed, market, members, strategies

configure_logging()
app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description="Platania 量化研究、策略回测、AI StrategySpec 与会员服务 API",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder(
            {"error": {"code": "validation_error", "message": "请求参数无效", "details": {"errors": exc.errors()}}}
        ),
    )


@app.get("/api/health", tags=["system"])
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": "0.2.0",
        "data_mode": settings.data_mode,
        "ai_mode": "deepseek" if settings.deepseek_enabled else "mock",
        "auth_mode": "demo" if settings.demo_auth_enabled else "supabase",
    }


for router in (market.router, strategies.router, backtests.router, ai.router, members.router, feed.router, admin.router):
    app.include_router(router, prefix="/api")


web_dist = ROOT_DIR / "web" / "dist"
if web_dist.exists():
    assets = web_dist / "assets"
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def web_app(path: str) -> FileResponse:
        requested = (web_dist / path).resolve()
        if path and requested.is_file() and web_dist.resolve() in requested.parents:
            return FileResponse(requested)
        return FileResponse(web_dist / "index.html")
