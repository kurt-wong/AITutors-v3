"""FastAPI 入口（40 §2 段 A）。启动零 LLM/OCR/Worker/外部副作用（Gate A1）。

Phase I Review Console：挂载 /api/* 只读 + Admission 审核端点。
EB-008（92号 §5.2）：非 test 环境启动校验 APP_SECRET（review proof fail-closed）。
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import (
    admin,
    candidates,
    documents,
    feedback,
    images,
    inspect,
    questions,
    student_questions,
    tasks,
)
from app.api.deps import effective_db_name
from app.core.config import settings
from app.db.session import is_default_db
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


# QUESTION-VISUAL-INSPECTION-V1：活动库为隔离卷库（非默认库）时只读保护。
# 验收卷库只允许 GET 浏览；唯一例外：反馈登记（观测性写入 question_feedbacks）
# 与 inspect 激活本身。禁止 import / approve / reject 等业务写入触碰验收数据。
_MUTATION_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
_MUTATION_ALLOWLIST_PREFIXES = (
    "/api/feedbacks",       # 反馈登记（观测性，M3b 契约：不改题面/答案/发布）
    "/api/inspect/activate",
)


@app.middleware("http")
async def volume_readonly_guard(request: Request, call_next):
    if request.method in _MUTATION_METHODS and not is_default_db(effective_db_name(request)):
        path = request.url.path
        if not any(path.startswith(p) for p in _MUTATION_ALLOWLIST_PREFIXES):
            return Response(
                content='{"detail":"isolated volume db is read-only"}',
                status_code=403,
                media_type="application/json",
            )
    return await call_next(request)


app.include_router(documents.router, prefix="/api")
app.include_router(candidates.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(questions.router, prefix="/api")
app.include_router(student_questions.router, prefix="/api")
app.include_router(feedback.router, prefix="/api")
app.include_router(images.router, prefix="/api")
app.include_router(inspect.router, prefix="/api")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
