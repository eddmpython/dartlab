"""Server API 엔드포인트 테스트.

데이터 독립 테스트 (status, configure, models, spec, stats, search, SPA)와
데이터 의존 테스트 (company, modules, preview, export)를 분리한다.
"""

from unittest.mock import MagicMock

import pytest
from starlette.testclient import TestClient

from dartlab.server import app

from tests.conftest import SAMSUNG, _has_data

_has_samsung_docs = _has_data(SAMSUNG, "docs")
_has_samsung_finance = _has_data(SAMSUNG, "finance")
_has_any_samsung = _has_samsung_docs or _has_samsung_finance

requires_samsung_any = pytest.mark.skipif(
    not _has_any_samsung, reason="삼성전자 데이터 없음"
)


@pytest.fixture(scope="module")
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# ── 데이터 독립 테스트 ──


class TestStatus:
    def test_status_basic(self, client):
        """GET /api/status — provider 상태 + 버전 반환."""
        resp = client.get("/api/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "providers" in data
        assert "version" in data
        assert isinstance(data["providers"], dict)
        for prov_info in data["providers"].values():
            assert "available" in prov_info

    def test_status_ollama_detail(self, client):
        """GET /api/status — ollama 상세 정보 포함."""
        resp = client.get("/api/status")
        data = resp.json()
        assert "ollama" in data
        assert "installed" in data["ollama"]
        assert "running" in data["ollama"]

    def test_status_codex_detail(self, client):
        """GET /api/status — codex 상세 정보 포함."""
        resp = client.get("/api/status")
        data = resp.json()
        assert "codex" in data
        assert "installed" in data["codex"]

    def test_status_version_not_unknown(self, client):
        """GET /api/status — 버전이 'unknown'이 아님."""
        resp = client.get("/api/status")
        data = resp.json()
        assert data["version"] != "unknown"


class TestConfigure:
    def test_configure_ollama(self, client):
        """POST /api/configure — provider 설정 변경."""
        resp = client.post(
            "/api/configure",
            json={"provider": "ollama"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["provider"] == "ollama"
        assert "available" in data

    def test_configure_with_model(self, client):
        """POST /api/configure — model 지정."""
        resp = client.post(
            "/api/configure",
            json={"provider": "ollama", "model": "qwen3"},
        )
        assert resp.status_code == 200
        assert resp.json()["ok"] is True


class TestModels:
    def test_static_providers(self, client):
        """GET /api/models/{provider} — 정적 모델 목록."""
        for prov in ("chatgpt", "codex", "claude-code"):
            resp = client.get(f"/api/models/{prov}")
            assert resp.status_code == 200
            data = resp.json()
            assert "models" in data
            assert isinstance(data["models"], list)
            assert len(data["models"]) > 0

    def test_ollama_models(self, client):
        """GET /api/models/ollama — Ollama 모델 목록 (형식 확인)."""
        resp = client.get("/api/models/ollama")
        assert resp.status_code == 200
        data = resp.json()
        assert "models" in data
        assert isinstance(data["models"], list)
        assert "recommendations" in data

    def test_unknown_provider(self, client):
        """GET /api/models/{unknown} — 빈 목록."""
        resp = client.get("/api/models/nonexistent")
        assert resp.status_code == 200
        assert resp.json()["models"] == []

    def test_openai_without_key(self, client):
        """GET /api/models/openai — API 키 없으면 fallback 목록."""
        resp = client.get("/api/models/openai")
        assert resp.status_code == 200
        data = resp.json()
        assert "models" in data
        assert len(data["models"]) > 0

    def test_claude_without_key(self, client):
        """GET /api/models/claude — API 키 없으면 fallback 목록."""
        resp = client.get("/api/models/claude")
        assert resp.status_code == 200
        data = resp.json()
        assert "models" in data
        assert len(data["models"]) > 0


class TestSpec:
    def test_spec_summary(self, client):
        """GET /api/spec — 시스템 스펙 summary."""
        resp = client.get("/api/spec")
        assert resp.status_code == 200
        assert isinstance(resp.json(), dict)

    def test_spec_engine_insight(self, client):
        """GET /api/spec?engine=insight — 엔진별 스펙."""
        resp = client.get("/api/spec", params={"engine": "insight"})
        assert resp.status_code == 200

    def test_spec_unknown_engine(self, client):
        """GET /api/spec?engine=nonexistent — 404."""
        resp = client.get("/api/spec", params={"engine": "nonexistent"})
        assert resp.status_code == 404


class TestDataStats:
    def test_data_stats(self, client):
        """GET /api/data/stats — 데이터 현황."""
        resp = client.get("/api/data/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "version" in data
        assert "docs" in data
        assert "finance" in data
        assert isinstance(data["docs"]["count"], int)
        assert isinstance(data["finance"]["count"], int)


class TestSearch:
    def test_search_valid(self, client):
        """GET /api/search?q=삼성 — 종목 검색."""
        resp = client.get("/api/search", params={"q": "삼성"})
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert isinstance(data["results"], list)
        if data["results"]:
            row = data["results"][0]
            assert "corpName" in row
            assert "stockCode" in row

    def test_search_empty_query(self, client):
        """GET /api/search?q= — 빈 쿼리 → 422."""
        resp = client.get("/api/search", params={"q": ""})
        assert resp.status_code == 422

    def test_search_no_results(self, client):
        """GET /api/search — 결과 없는 쿼리."""
        resp = client.get("/api/search", params={"q": "zzznonexistent999"})
        assert resp.status_code == 200
        assert resp.json()["results"] == []

    def test_search_code(self, client):
        """GET /api/search?q=삼성전자 — 정확한 종목명 검색."""
        resp = client.get("/api/search", params={"q": "삼성전자"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["results"]) >= 1
        assert data["results"][0]["stockCode"] == "005930"

    def test_search_max_results(self, client):
        """GET /api/search — 결과 최대 20개."""
        resp = client.get("/api/search", params={"q": "한"})
        assert resp.status_code == 200
        assert len(resp.json()["results"]) <= 20


class TestSPA:
    def test_spa_root(self, client):
        """GET / — SPA 반환 (200 or 503)."""
        resp = client.get("/")
        assert resp.status_code in (200, 503)


class TestTemplates:
    def test_list_templates(self, client):
        """GET /api/export/templates — 목록."""
        resp = client.get("/api/export/templates")
        assert resp.status_code == 200
        data = resp.json()
        assert "templates" in data
        assert isinstance(data["templates"], list)

    def test_template_not_found(self, client):
        """GET /api/export/templates/{id} — 404."""
        resp = client.get("/api/export/templates/nonexistent_id")
        assert resp.status_code == 404

    def test_delete_preset_template(self, client):
        """DELETE /api/export/templates/{preset} — 프리셋 삭제 불가 → 400."""
        resp = client.delete("/api/export/templates/preset_full")
        assert resp.status_code == 400


class TestOAuth:
    def test_oauth_status(self, client):
        """GET /api/oauth/status — 상태 확인."""
        resp = client.get("/api/oauth/status")
        assert resp.status_code == 200
        assert "done" in resp.json()

    def test_oauth_logout(self, client):
        """POST /api/oauth/logout — 토큰 제거."""
        resp = client.post("/api/oauth/logout")
        assert resp.status_code == 200
        assert resp.json()["ok"] is True


# ── 데이터 의존 테스트 ──


class TestCompanyAPI:
    @requires_samsung_any
    def test_company_info(self, client):
        """GET /api/company/{code} — 기업 기본 정보."""
        resp = client.get(f"/api/company/{SAMSUNG}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["stockCode"] == SAMSUNG
        assert "삼성전자" in data["corpName"]

    def test_company_not_found(self, client):
        """GET /api/company/{code} — 없는 종목 → 404."""
        resp = client.get("/api/company/999999")
        assert resp.status_code == 404


class TestDataSources:
    @requires_samsung_any
    def test_data_sources(self, client):
        """GET /api/data/sources/{code} — 데이터 소스 목록."""
        resp = client.get(f"/api/data/sources/{SAMSUNG}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["stockCode"] == SAMSUNG
        assert "categories" in data
        assert "totalSources" in data
        assert "availableSources" in data
        assert data["totalSources"] > 0

    def test_data_sources_not_found(self, client):
        """GET /api/data/sources/{code} — 없는 종목 → 404."""
        resp = client.get("/api/data/sources/999999")
        assert resp.status_code == 404

    @requires_samsung_any
    def test_company_modules(self, client):
        """GET /api/company/{code}/modules — 모듈 목록."""
        resp = client.get(f"/api/company/{SAMSUNG}/modules")
        assert resp.status_code == 200
        assert "modules" in resp.json()


class TestDataPreview:
    @pytest.mark.skipif(not _has_samsung_finance, reason="삼성전자 finance 데이터 없음")
    def test_preview_annual_IS(self, client):
        """GET /api/data/preview — finance IS."""
        resp = client.get(f"/api/data/preview/{SAMSUNG}/annual.IS")
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "table"
        assert data["module"] == "annual.IS"
        assert "columns" in data
        assert "rows" in data
        assert len(data["rows"]) > 0
        if "meta" in data:
            assert "sortOrder" in data["meta"]
            assert "labels" in data["meta"]

    @pytest.mark.skipif(not _has_samsung_finance, reason="삼성전자 finance 데이터 없음")
    def test_preview_annual_BS(self, client):
        """GET /api/data/preview — finance BS."""
        resp = client.get(f"/api/data/preview/{SAMSUNG}/annual.BS")
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "table"

    @pytest.mark.skipif(not _has_samsung_finance, reason="삼성전자 finance 데이터 없음")
    def test_preview_ratios(self, client):
        """GET /api/data/preview — ratios."""
        resp = client.get(f"/api/data/preview/{SAMSUNG}/ratios")
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] in ("table", "dict")

    def test_preview_not_found_company(self, client):
        """GET /api/data/preview — 없는 종목."""
        resp = client.get("/api/data/preview/999999/annual.IS")
        assert resp.status_code == 404

    @requires_samsung_any
    def test_preview_not_found_module(self, client):
        """GET /api/data/preview — 없는 모듈."""
        resp = client.get(f"/api/data/preview/{SAMSUNG}/nonexistent_module")
        assert resp.status_code == 404

    @pytest.mark.skipif(not _has_samsung_docs, reason="삼성전자 docs 데이터 없음")
    def test_preview_docs_module(self, client):
        """GET /api/data/preview — docs salesBreakdown."""
        resp = client.get(f"/api/data/preview/{SAMSUNG}/salesBreakdown")
        if resp.status_code == 200:
            data = resp.json()
            assert data["type"] in ("table", "dict", "text", "unknown")

    @pytest.mark.skipif(not _has_samsung_finance, reason="삼성전자 finance 데이터 없음")
    def test_preview_max_rows(self, client):
        """GET /api/data/preview — max_rows 파라미터."""
        resp = client.get(f"/api/data/preview/{SAMSUNG}/annual.IS", params={"max_rows": 5})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["rows"]) <= 5


class TestExport:
    @pytest.mark.skipif(not _has_samsung_finance, reason="삼성전자 finance 데이터 없음")
    def test_export_modules(self, client):
        """GET /api/export/modules/{code}."""
        resp = client.get(f"/api/export/modules/{SAMSUNG}")
        assert resp.status_code == 200
        data = resp.json()
        assert "modules" in data
        assert isinstance(data["modules"], list)

    @pytest.mark.skipif(not _has_samsung_finance, reason="삼성전자 finance 데이터 없음")
    def test_export_sources(self, client):
        """GET /api/export/sources/{code}."""
        resp = client.get(f"/api/export/sources/{SAMSUNG}")
        assert resp.status_code == 200

    def test_export_excel_not_found(self, client):
        """GET /api/export/excel/{code} — 없는 종목."""
        resp = client.get("/api/export/excel/999999")
        assert resp.status_code == 404


class TestAsk:
    def test_ask_no_company(self, client):
        """POST /api/ask — 종목 없는 질문 (LLM 없으면 에러 허용)."""
        resp = client.post(
            "/api/ask",
            json={"question": "안녕하세요", "stream": False},
        )
        assert resp.status_code in (200, 401, 500)

    @requires_samsung_any
    def test_ask_with_company(self, client):
        """POST /api/ask — company 필드 명시."""
        resp = client.post(
            "/api/ask",
            json={"company": "삼성전자", "question": "매출 알려줘", "stream": False},
        )
        assert resp.status_code in (200, 401, 500)

    def test_ask_unknown_company(self, client):
        """POST /api/ask — 없는 종목 → not_found."""
        resp = client.post(
            "/api/ask",
            json={"company": "존재하지않는회사XYZ", "question": "분석해줘", "stream": False},
        )
        assert resp.status_code in (200, 500)
        if resp.status_code == 200:
            assert "answer" in resp.json()


# ── 유틸리티/로직 단위 테스트 ──


class TestResolveUtils:
    def test_is_meta_question(self):
        from dartlab.server.resolve import is_meta_question
        assert is_meta_question("버전 알려줘")
        assert is_meta_question("도움말")
        assert is_meta_question("뭘 할 수 있어?")
        assert not is_meta_question("삼성전자 매출 분석해줘")

    def test_has_analysis_intent(self):
        from dartlab.server.resolve import has_analysis_intent
        assert has_analysis_intent("삼성전자 매출 분석해줘")
        assert has_analysis_intent("ROE 알려줘")
        assert not has_analysis_intent("삼성전자 분석하고 싶은데")

    def test_build_not_found_msg_empty(self):
        from dartlab.server.resolve import build_not_found_msg
        msg = build_not_found_msg([])
        assert "찾을 수 없습니다" in msg

    def test_build_not_found_msg_with_suggestions(self):
        from dartlab.server.resolve import build_not_found_msg
        msg = build_not_found_msg([{"corpName": "삼성전자", "stockCode": "005930"}])
        assert "삼성전자" in msg
        assert "005930" in msg

    def test_build_ambiguous_msg(self):
        from dartlab.server.resolve import build_ambiguous_msg
        msg = build_ambiguous_msg([
            {"corpName": "현대자동차", "stockCode": "005380"},
            {"corpName": "현대차증권", "stockCode": "001500"},
        ])
        assert "현대자동차" in msg
        assert "현대차증권" in msg

    def test_needs_match_verification(self):
        from dartlab.server.resolve import needs_match_verification
        assert not needs_match_verification("삼성전자 분석해줘", "삼성전자")
        assert needs_match_verification("현대차 분석해줘", "현대차증권")
        assert not needs_match_verification("삼전 분석해줘", "삼성전자")


class TestChatUtils:
    def test_build_history_empty(self):
        from dartlab.server.chat import build_history_messages
        assert build_history_messages(None) == []

    def test_build_history_messages(self):
        from dartlab.server.chat import build_history_messages
        from dartlab.server.models import HistoryMessage
        msgs = build_history_messages([
            HistoryMessage(role="user", text="삼성전자 분석해줘"),
            HistoryMessage(role="assistant", text="분석 결과입니다."),
        ])
        assert len(msgs) == 2
        assert msgs[0]["role"] == "user"
        assert msgs[1]["role"] == "assistant"

    def test_build_history_with_meta(self):
        from dartlab.server.chat import build_history_messages
        from dartlab.server.models import HistoryMeta, HistoryMessage
        msgs = build_history_messages([
            HistoryMessage(
                role="assistant", text="분석 결과",
                meta=HistoryMeta(company="삼성전자", stockCode="005930", modules=["IS", "BS"]),
            ),
        ])
        assert len(msgs) == 1
        assert "삼성전자" in msgs[0]["content"]
        assert "005930" in msgs[0]["content"]

    def test_extract_last_stock_code(self):
        from dartlab.server.chat import extract_last_stock_code
        from dartlab.server.models import HistoryMeta, HistoryMessage
        assert extract_last_stock_code(None) is None
        assert extract_last_stock_code([]) is None
        code = extract_last_stock_code([
            HistoryMessage(role="user", text="질문"),
            HistoryMessage(
                role="assistant", text="답변",
                meta=HistoryMeta(stockCode="005930"),
            ),
        ])
        assert code == "005930"

    def test_build_dynamic_chat_prompt(self):
        from dartlab.server.chat import build_dynamic_chat_prompt
        prompt = build_dynamic_chat_prompt()
        assert "DartLab" in prompt
        assert isinstance(prompt, str)
        assert len(prompt) > 100


class TestCompanyCache:
    def test_put_and_get(self):
        from dartlab.server.cache import CompanyCache
        cache = CompanyCache()
        mock = MagicMock()
        mock.stockCode = "005930"
        cache.put("005930", mock, {"items": []})
        assert len(cache) == 1
        result = cache.get("005930")
        assert result is not None
        assert result[0] is mock
        assert result[1] == {"items": []}

    def test_clear(self):
        from dartlab.server.cache import CompanyCache
        cache = CompanyCache()
        mock = MagicMock()
        cache.put("005930", mock, None)
        cache.clear()
        assert len(cache) == 0
        assert cache.get("005930") is None

    def test_lru_eviction(self):
        from dartlab.server.cache import CompanyCache
        cache = CompanyCache()
        for i in range(25):
            code = f"{i:06d}"
            m = MagicMock()
            m.stockCode = code
            cache.put(code, m, None)
        assert len(cache) == 20
        assert cache.get("000000") is None
        assert cache.get("000024") is not None

    def test_update_snapshot(self):
        from dartlab.server.cache import CompanyCache
        cache = CompanyCache()
        mock = MagicMock()
        cache.put("005930", mock, {"old": True})
        cache.update_snapshot("005930", {"new": True})
        result = cache.get("005930")
        assert result[1] == {"new": True}
