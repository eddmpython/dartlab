"""server API 엔드포인트 단위 테스트 — MockCompany + FastAPI TestClient.

coverage 대상:
- server/api/common.py: sanitize_error, serialize_payload, guideDetail
- server/__init__.py: _cors_origins, _SecurityHeadersMiddleware
- server/api/company.py, data.py 등 기본 라우팅
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


# ═══════════════════════════════════════════════════════════
# server/api/common.py — 순수 함수 테스트 (FastAPI 불필요)
# ═══════════════════════════════════════════════════════════


class TestSanitizeError:
    def test_masks_file_path(self):
        from dartlab.server.api.common import sanitize_error

        msg = sanitize_error(ValueError("file not found: C:\\Users\\admin\\secret\\data.txt"))
        assert "admin" not in msg
        assert "<path>" in msg

    def test_masks_unix_path(self):
        from dartlab.server.api.common import sanitize_error

        msg = sanitize_error(ValueError("error at /home/user/secret.key"))
        assert "secret.key" not in msg
        assert "<path>" in msg

    def test_masks_credentials(self):
        from dartlab.server.api.common import sanitize_error

        msg = sanitize_error(ValueError("api_key=sk-abc123 failed"))
        assert "sk-abc123" not in msg
        assert "***" in msg

    def test_masks_token(self):
        from dartlab.server.api.common import sanitize_error

        msg = sanitize_error(ValueError("token: mytoken123"))
        assert "mytoken123" not in msg

    def test_safe_message_unchanged(self):
        from dartlab.server.api.common import sanitize_error

        msg = sanitize_error(ValueError("simple error"))
        assert msg == "simple error"


class TestSerializePayload:
    def test_none(self):
        from dartlab.server.api.common import serialize_payload

        result = serialize_payload(None)
        assert result["type"] == "none"
        assert result["data"] is None

    def test_dict(self):
        from dartlab.server.api.common import serialize_payload

        result = serialize_payload({"key": "value"})
        assert result["type"] == "dict"
        assert result["data"]["key"] == "value"

    def test_string(self):
        from dartlab.server.api.common import serialize_payload

        result = serialize_payload("hello")
        assert result["type"] == "text"
        assert result["data"] == "hello"

    def test_polars_dataframe(self):
        import polars as pl

        from dartlab.server.api.common import serialize_payload

        df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        result = serialize_payload(df)
        assert result["type"] == "table"
        assert result["columns"] == ["a", "b"]
        assert len(result["rows"]) == 3

    def test_max_rows_limit(self):
        import polars as pl

        from dartlab.server.api.common import serialize_payload

        df = pl.DataFrame({"a": list(range(500))})
        result = serialize_payload(df, max_rows=10)
        assert len(result["rows"]) == 10

    def test_list_payload(self):
        from dartlab.server.api.common import serialize_payload

        result = serialize_payload([1, 2, 3])
        assert result["data"] is not None


class TestNormalizeProviderName:
    def test_basic(self):
        from dartlab.server.api.common import normalize_provider_name

        # None → None
        assert normalize_provider_name(None) is None

    def test_known_provider(self):
        from dartlab.server.api.common import normalize_provider_name

        result = normalize_provider_name("gemini")
        assert result is not None


# ═══════════════════════════════════════════════════════════
# server/__init__.py — CORS 설정 테스트
# ═══════════════════════════════════════════════════════════


class TestCorsOrigins:
    def test_default_origins(self, monkeypatch):
        monkeypatch.delenv("DARTLAB_CORS_ORIGINS", raising=False)
        from dartlab.server import _cors_origins

        origins = _cors_origins()
        assert isinstance(origins, list)
        assert len(origins) >= 2
        assert any("8400" in o for o in origins)

    def test_wildcard(self, monkeypatch):
        monkeypatch.setenv("DARTLAB_CORS_ORIGINS", "*")
        from dartlab.server import _cors_origins

        assert _cors_origins() == ["*"]

    def test_custom_origins(self, monkeypatch):
        monkeypatch.setenv("DARTLAB_CORS_ORIGINS", "http://a.com, http://b.com")
        from dartlab.server import _cors_origins

        origins = _cors_origins()
        assert "http://a.com" in origins
        assert "http://b.com" in origins


# ═══════════════════════════════════════════════════════════
# FastAPI TestClient 테스트 — fastapi/starlette 필요
# ═══════════════════════════════════════════════════════════

_has_testclient = False
try:
    from starlette.testclient import TestClient

    _has_testclient = True
except ImportError:
    pass


@pytest.mark.skipif(not _has_testclient, reason="starlette not installed")
class TestServerEndpoints:
    @pytest.fixture(autouse=True)
    def _app(self):
        from dartlab.server import app

        self.client = TestClient(app, raise_server_exceptions=False)

    def test_root(self):
        """루트 경로 — SPA 또는 리다이렉트."""
        resp = self.client.get("/")
        # SPA가 빌드되어 있으면 200, 아니면 다른 코드 → 어쨌든 크래시 아님
        assert resp.status_code in (200, 301, 302, 307, 404)

    def test_security_headers(self):
        """보안 헤더가 모든 응답에 포함."""
        resp = self.client.get("/api/status", follow_redirects=False)
        # status 엔드포인트가 없어도 404 응답에도 헤더가 붙어야 함
        assert "x-content-type-options" in resp.headers
        assert resp.headers["x-content-type-options"] == "nosniff"

    def test_nonexistent_api(self):
        """없는 엔드포인트 → 404 또는 SPA fallback."""
        resp = self.client.get("/api/nonexistent12345")
        assert resp.status_code in (404, 200)

    def test_search_empty(self):
        """검색 쿼리 없이 호출 → 422 (validation error)."""
        resp = self.client.get("/api/search")
        assert resp.status_code == 422

    def test_search_short_query(self):
        """검색 쿼리 빈 문자열 → 422."""
        resp = self.client.get("/api/search?q=")
        assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════
# HANDLED_API_ERRORS 상수 검증
# ═══════════════════════════════════════════════════════════


class TestHandledApiErrors:
    def test_contains_common_errors(self):
        from dartlab.server.api.common import HANDLED_API_ERRORS

        assert ValueError in HANDLED_API_ERRORS
        assert FileNotFoundError in HANDLED_API_ERRORS
        assert KeyError in HANDLED_API_ERRORS
        assert TypeError in HANDLED_API_ERRORS
        assert RuntimeError in HANDLED_API_ERRORS
        assert TimeoutError in HANDLED_API_ERRORS
