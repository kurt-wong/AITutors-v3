"""FastAPI 入口（40 §2 段 A）。启动零 LLM/OCR/Worker/外部副作用（Gate A1）。

Phase I Review Console：挂载 /api/* 只读 + Admission 审核端点。
EB-008（92号 §5.2）：非 test 环境启动校验 APP_SECRET（review proof fail-closed）。
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import admin, candidates, documents, tasks
from app.core.config import settings
from app.domains.evidence.proof import require_app_secret


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    # EB-008 §5.2：APP_SECRET 启动校验（≥32 字节）。test 环境豁免（conftest 注入）。
    if settings.app_env != "test":
        require_app_secret()
    yield


app = FastAPI(title="AITutors V3", lifespan=_lifespan)

# Phase I Review Console：Vite dev server (5173) → FastAPI (8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api")
app.include_router(candidates.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
