# -*- coding: utf-8 -*-
"""V3-IMG-OPTION-003 — image static service security & mapping tests."""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture()
def img_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "_imgs"
    paper = root / "paper-2018"
    paper.mkdir(parents=True)
    (paper / "img_ok.jpg").write_bytes(b"\xff\xd8\xff\xe0fakejpeg")
    (paper / "img_ok.png").write_bytes(b"\x89PNGfake")
    (root / "img_top.jpg").write_bytes(b"\xff\xd8fake")
    monkeypatch.setattr("app.core.config.settings.images_root", str(root))
    return root


@pytest.fixture()
def client(img_root: Path):
    from app.api.routers.images import router

    app = FastAPI()
    app.include_router(router, prefix="/api")
    return TestClient(app)


class TestImageServing:
    def test_serves_nested_image(self, client, img_root):
        r = client.get("/api/images/paper-2018/img_ok.jpg")
        assert r.status_code == 200
        assert r.content.startswith(b"\xff\xd8")

    def test_serves_top_level_image(self, client):
        r = client.get("/api/images/img_top.jpg")
        assert r.status_code == 200

    def test_serves_png(self, client):
        r = client.get("/api/images/paper-2018/img_ok.png")
        assert r.status_code == 200

    def test_missing_image_404(self, client):
        r = client.get("/api/images/paper-2018/nope.jpg")
        assert r.status_code == 404

    def test_directory_404(self, client):
        r = client.get("/api/images/paper-2018")
        assert r.status_code in (400, 404)


class TestPathSecurity:
    def test_rejects_dotdot_traversal(self, client):
        for key in (
            "../etc/passwd.jpg",
            "paper-2018/../../etc/passwd.jpg",
            "paper-2018/..%2F..%2Fetc%2Fpasswd.jpg",
            "..\\..\\windows\\win.ini",
        ):
            r = client.get(f"/api/images/{key}")
            assert r.status_code in (400, 404), f"{key} -> {r.status_code}"

    def test_dot_segment_normalized_or_rejected(self, client):
        # HTTP stacks normalise `./` away before the handler; if it arrives
        # intact the server must still reject it. Either way the file is served
        # only under its real key — never via a traversal.
        r = client.get("/api/images/paper-2018/./img_ok.jpg")
        assert r.status_code in (200, 400, 404)

    def test_rejects_non_image_extension(self, client):
        r = client.get("/api/images/paper-2018/evil.html")
        assert r.status_code == 400
        r = client.get("/api/images/evil.php")
        assert r.status_code == 400

    def test_rejects_empty_key(self, client):
        r = client.get("/api/images/")
        assert r.status_code in (400, 404, 405)

    def test_unconfigured_root_503(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr("app.core.config.settings.images_root", "")
        from app.api.routers.images import router

        app = FastAPI()
        app.include_router(router, prefix="/api")
        c = TestClient(app, raise_server_exceptions=False)
        r = c.get("/api/images/paper-2018/img_ok.jpg")
        assert r.status_code == 503

    def test_rejects_absolute_unix_path(self, client):
        r = client.get("/api/images//etc/passwd.jpg")
        assert r.status_code in (400, 404)

    def test_containment_after_resolve(self, client, img_root: Path):
        # symlink escape attempt
        outside = img_root.parent / "outside.jpg"
        outside.write_bytes(b"\xff\xd8outside")
        link = img_root / "paper-2018" / "escape.jpg"
        try:
            link.symlink_to(outside)
        except (OSError, NotImplementedError):
            pytest.skip("symlinks unavailable on this platform")
        r = client.get("/api/images/paper-2018/escape.jpg")
        # either containment reject (400) or, if OS resolves inside root, serve —
        # but never read the outside file content marker
        if r.status_code == 200:
            assert r.content != b"\xff\xd8outside"
        else:
            assert r.status_code in (400, 404)
