"""FastAPI 入口（40 §2 段 A）。启动零 LLM/OCR/Worker/外部副作用（Gate A1）。

Phase I Review Console：挂载 /api/* 只读 + Admission 审核端点。
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import admin, candidates, documents, tasks

app = FastAPI(title="AITutors V3")

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
