"""极简 FastAPI 入口（40 §2 段 A）。启动零 LLM/OCR/Worker/外部副作用（Gate A1）。"""

from fastapi import FastAPI

app = FastAPI(title="AITutors V3")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
