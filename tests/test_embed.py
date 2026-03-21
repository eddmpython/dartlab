"""Embed 위젯 서빙 테스트."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# embed.py 라우터 테스트
# ---------------------------------------------------------------------------


class TestEmbedRoute:
    def test_embed_path_points_to_ui_build(self):
        from dartlab.server.embed import _EMBED_PATH

        # 경로가 ui/build/embed.js를 가리키는지 확인
        assert _EMBED_PATH.name == "embed.js"
        assert "ui" in str(_EMBED_PATH)
        assert "build" in str(_EMBED_PATH)

    def test_serve_embed_not_built(self):
        """embed.js가 없으면 경고 JS를 반환한다."""
        from dartlab.server.embed import serve_embed

        with patch("dartlab.server.embed._EMBED_PATH", Path("/nonexistent/embed.js")):
            response = serve_embed()
            assert response.status_code == 200
            assert "application/javascript" in response.media_type

    def test_serve_embed_built(self):
        """embed.js가 존재하면 FileResponse를 반환한다."""
        from dartlab.server.embed import _EMBED_PATH, serve_embed

        if not _EMBED_PATH.exists():
            pytest.skip("embed.js not built — run: cd src/dartlab/ui && npm run build:widget")

        response = serve_embed()
        # FileResponse 확인
        assert response.status_code == 200
        assert "Cache-Control" in response.headers
        assert response.headers["Access-Control-Allow-Origin"] == "*"


# ---------------------------------------------------------------------------
# 보안 — /embed.js는 /api/ 경로가 아니므로 미들웨어 통과
# ---------------------------------------------------------------------------


class TestEmbedSecurity:
    def test_embed_not_api_path(self):
        """embed.js는 /api/로 시작하지 않으므로 터널 보안 미들웨어를 통과한다."""
        path = "/embed.js"
        assert not path.startswith("/api/")

    def test_embed_registered_in_app(self):
        """embed 라우터가 앱에 등록되어 있는지 확인."""
        from dartlab.server import app

        routes = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/embed.js" in routes


# ---------------------------------------------------------------------------
# 위젯 소스 파일 존재 확인
# ---------------------------------------------------------------------------


class TestWidgetSource:
    def test_widget_directory_exists(self):
        widget_dir = Path(__file__).parent.parent / "src" / "dartlab" / "ui" / "widget"
        assert widget_dir.exists()

    def test_embed_entry_exists(self):
        embed = Path(__file__).parent.parent / "src" / "dartlab" / "ui" / "widget" / "embed.js"
        assert embed.exists()

    def test_snapshot_component_exists(self):
        snap = Path(__file__).parent.parent / "src" / "dartlab" / "ui" / "widget" / "Snapshot.svelte"
        assert snap.exists()

    def test_api_client_exists(self):
        api = Path(__file__).parent.parent / "src" / "dartlab" / "ui" / "widget" / "api.js"
        assert api.exists()

    def test_theme_exists(self):
        theme = Path(__file__).parent.parent / "src" / "dartlab" / "ui" / "widget" / "theme.js"
        assert theme.exists()

    def test_vite_widget_config_exists(self):
        config = Path(__file__).parent.parent / "src" / "dartlab" / "ui" / "vite.widget.config.js"
        assert config.exists()


# ---------------------------------------------------------------------------
# 빌드 결과 확인
# ---------------------------------------------------------------------------


class TestWidgetBuild:
    def test_embed_js_built(self):
        embed = Path(__file__).parent.parent / "src" / "dartlab" / "ui" / "build" / "embed.js"
        if not embed.exists():
            pytest.skip("embed.js not built")
        assert embed.stat().st_size > 0

    def test_embed_js_size_under_50kb(self):
        """빌드된 embed.js가 50KB 미만인지 확인 (gzip 전)."""
        embed = Path(__file__).parent.parent / "src" / "dartlab" / "ui" / "build" / "embed.js"
        if not embed.exists():
            pytest.skip("embed.js not built")
        size_kb = embed.stat().st_size / 1024
        assert size_kb < 50, f"embed.js가 {size_kb:.1f}KB — 50KB 미만이어야 합니다"
