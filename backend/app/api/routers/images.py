"""Image resource serving (V3-IMG-OPTION-003).

Serves source-extracted figure images from a fixed, explicit root directory.
Only image extensions; path traversal outside the root is rejected.

URL shape: GET /api/images/{key}
  key = path under the images root, e.g.
        `2018北京夏季高中会考地理（教师版）(1)/img_in_image_box_114_100_392_229.jpg`

Source markdown keeps document-relative refs like `../../_imgs/<paper>/img_xxx.jpg`.
The frontend maps `_imgs/...` → `/api/images/...` before requesting.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.core.config import settings

router = APIRouter(prefix="/images", tags=["images"])

_ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".avif"}


def images_root() -> Path:
    """Explicit image root. Fail-closed if unset."""
    raw = getattr(settings, "images_root", "") or ""
    if not raw:
        raise HTTPException(status_code=503, detail="images_root not configured")
    root = Path(raw)
    if not root.is_dir():
        raise HTTPException(status_code=503, detail="images_root is not a directory")
    return root.resolve()


def _safe_resolve(key: str) -> Path:
    """Resolve `key` under images_root; reject traversal / absolute / non-image."""
    if not key or "\0" in key:
        raise HTTPException(status_code=400, detail="invalid image key")
    # normalise separators; never pass raw `..` to the filesystem
    rel = key.replace("\\", "/").lstrip("/")
    segs = rel.split("/")
    if any(s in ("..", ".", "") for s in segs):
        raise HTTPException(status_code=400, detail="path traversal rejected")
    if rel.startswith("//") or (len(rel) > 1 and rel[1] == ":"):
        raise HTTPException(status_code=400, detail="absolute path rejected")
    ext = Path(rel).suffix.lower()
    if ext not in _ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="unsupported image type")

    root = images_root()
    target = (root / rel).resolve()
    # containment check after resolve (handles symlink / crafted names)
    if not str(target).startswith(str(root)):
        raise HTTPException(status_code=400, detail="path traversal rejected")
    return target


@router.get("/{key:path}")
async def get_image(key: str) -> FileResponse:
    target = _safe_resolve(key)
    if not target.is_file():
        raise HTTPException(status_code=404, detail="image not found")
    return FileResponse(target)
