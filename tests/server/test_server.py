"""Server API 엔드포인트 테스트.

데이터 독립 테스트 (status, configure, models, spec, stats, search, SPA)와
데이터 의존 테스트 (company, modules, preview, export)를 분리한다.
"""

import asyncio
from unittest.mock import MagicMock

import polars as pl
import pytest

starlette = pytest.importorskip("starlette", reason="starlette not installed (optional [ai] dependency)")
from starlette.testclient import TestClient  # noqa: E402

from dartlab.server import app  # noqa: E402
from tests.conftest import SAMSUNG, _has_data

_has_samsung_panel = _has_data(SAMSUNG, "panel")
_has_samsung_finance = _has_data(SAMSUNG, "finance")
_has_any_samsung = _has_samsung_panel or _has_samsung_finance

requires_samsung_any = pytest.mark.skipif(not _has_any_samsung, reason="삼성전자 데이터 없음")

pytestmark = pytest.mark.integration


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
        assert "openDart" in data
        assert isinstance(data["providers"], dict)
        assert "claude" not in data["providers"]
        assert "claude-code" not in data["providers"]
        assert "chatgpt" not in data["providers"]
        for prov_info in data["providers"].values():
            assert "available" in prov_info
            assert "credentialSource" in prov_info

    def test_status_runtimes_detail(self, client):
        """GET /api/status: 설치형 runtime 목록과 readiness를 반환한다.

        direct provider 시절의 최상위 ollama/codex/oauthCodex 블록은 제거됐고
        (agent-runtime 전환), 상태는 runtimes 배열이 소유한다.
        """
        resp = client.get("/api/status", params={"probe": 0})
        assert resp.status_code == 200
        data = resp.json()
        assert "ollama" not in data
        assert "oauthCodex" not in data
        runtimes = {item["runtimeId"]: item for item in data["runtimes"]}
        assert {"claude", "codex"} <= set(runtimes)
        for item in runtimes.values():
            assert "state" in item
            assert "readiness" in item
        assert "defaultRuntimeId" in data

    def test_status_version_not_unknown(self, client):
        """GET /api/status — 버전이 'unknown'이 아님."""
        resp = client.get("/api/status")
        data = resp.json()
        assert data["version"] != "unknown"

    def test_status_runtime_filter_returns_only_selected_runtime(self, client):
        """GET /api/status?runtimeId=codex: 선택 runtime만 남긴다."""
        resp = client.get("/api/status", params={"probe": 0, "runtimeId": "codex"})
        assert resp.status_code == 200
        data = resp.json()
        assert [item["runtimeId"] for item in data["runtimes"]] == ["codex"]

    def test_status_probe_zero_skips_cli_probe(self, client, monkeypatch):
        """GET /api/status?probe=0: CLI refresh probe를 실행하지 않는다."""
        refreshFlags: list[bool] = []

        from dartlab.ai.runtime import getRuntimeEngine

        engine = getRuntimeEngine()
        realStatus = engine.status

        def _recordingStatus(*, refresh):
            refreshFlags.append(refresh)
            return realStatus(refresh=False)

        monkeypatch.setattr(engine, "status", _recordingStatus)

        resp = client.get("/api/status", params={"probe": 0})
        assert resp.status_code == 200
        assert refreshFlags == [False]
        # direct provider probe 표면은 제거됐고 providers 블록은 빈 호환 dict다.
        assert resp.json()["providers"] == {}

    def test_suggest_endpoint_returns_questions_and_data_ready(self, client, monkeypatch):
        """GET /api/suggest — 추천 질문과 데이터 준비 상태를 함께 반환한다."""
        company = MagicMock()
        company.stockCode = "005930"
        company.corpName = "삼성전자"

        monkeypatch.setattr("dartlab.server.services.companyApi.get_company", lambda code: company)

        resp = client.get("/api/suggest", params={"stockCode": "005930"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["stockCode"] == "005930"
        assert data["company"] == "삼성전자"
        assert data["suggestions"] == []
        assert data["dataReady"] == {}


class TestConfigure:
    """direct provider 설정 표면은 agent-runtime 전환으로 제거됐다(410 Gone).

    DartLab은 모델 키를 저장하지 않고, 모델·인증은 설치형 agent CLI가 소유한다.
    """

    def test_validate_provider_is_gone(self, client):
        """POST /api/provider/validate: 410 + Runtime Center 안내."""
        resp = client.post(
            "/api/provider/validate",
            json={"provider": "ollama", "model": "qwen3"},
        )
        assert resp.status_code == 410
        assert "/api/agent/runtimes" in resp.json()["detail"]

    def test_configure_alias_is_gone(self, client):
        """POST /api/configure: 구 alias도 같은 410 계약이다."""
        resp = client.post(
            "/api/configure",
            json={"provider": "ollama"},
        )
        assert resp.status_code == 410
        assert "모델 키를 저장하지 않습니다" in resp.json()["detail"]


class TestAiProfile:
    """profile 표면은 조회 호환만 남기고 갱신·secret 저장은 제거됐다(410 Gone)."""

    def test_get_ai_profile_reports_runtime_migration(self, client):
        resp = client.get("/api/ai/profile")
        assert resp.status_code == 200
        data = resp.json()
        assert data["mode"] == "agent-runtime"
        assert data["deprecated"] is True
        assert "runtimes" in data
        assert "defaultProvider" not in data

    def test_put_ai_profile_is_gone(self, client):
        resp = client.put(
            "/api/ai/profile",
            json={"provider": "openai", "model": "gpt-5.4"},
        )
        assert resp.status_code == 410
        assert "agent CLI" in resp.json()["detail"]

    def test_post_ai_profile_secret_is_gone(self, client):
        """DartLab은 모델 API 키와 OAuth 토큰을 저장하지 않는다."""
        resp = client.post(
            "/api/ai/profile/secrets",
            json={"provider": "openai", "api_key": "sk-test"},
        )
        assert resp.status_code == 410
        assert "저장하지 않습니다" in resp.json()["detail"]


class TestOpenDartKey:
    def test_status_includes_open_dart_block(self, client):
        resp = client.get("/api/status", params={"probe": 0})
        assert resp.status_code == 200
        data = resp.json()
        assert "configured" in data["openDart"]
        assert "source" in data["openDart"]
        assert "envPath" in data["openDart"]

    def test_validate_dart_key_endpoint(self, client, monkeypatch):
        # 엔드포인트는 validateDartApiKey 결과 객체의 toDict()를 그대로 반환한다.
        monkeypatch.setattr(
            "dartlab.gather.dart.keys.validateDartApiKey",
            lambda key: type(
                "Validation",
                (),
                {"toDict": lambda self: {"ok": True, "validatedKey": key[-4:]}},
            )(),
        )

        resp = client.post("/api/openapi/dart-key/validate", json={"api_key": "test-dart-key"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["validatedKey"] == "-key"

    def test_save_dart_key_endpoint(self, client, monkeypatch):
        monkeypatch.setattr(
            "dartlab.gather.dart.keys.saveDartKeyToDotenv",
            lambda key: "C:/tmp/.env",
        )
        monkeypatch.setattr(
            "dartlab.gather.dart.keys.getDartKeyStatus",
            lambda startPath=None: type(
                "Status",
                (),
                {
                    "toDict": lambda self: {
                        "configured": True,
                        "source": "dotenv",
                        "keyCount": 1,
                        "envPath": ".env",
                        "writable": True,
                    }
                },
            )(),
        )

        resp = client.put("/api/openapi/dart-key", json={"api_key": "test-dart-key"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["envPath"] == "C:/tmp/.env"
        assert data["openDart"]["configured"] is True

    def test_delete_dart_key_endpoint(self, client, monkeypatch):
        monkeypatch.setattr(
            "dartlab.gather.dart.keys.clearDartKeyFromDotenv",
            lambda: "C:/tmp/.env",
        )
        monkeypatch.setattr(
            "dartlab.gather.dart.keys.getDartKeyStatus",
            lambda startPath=None: type(
                "Status",
                (),
                {
                    "toDict": lambda self: {
                        "configured": False,
                        "source": "none",
                        "keyCount": 0,
                        "envPath": ".env",
                        "writable": True,
                    }
                },
            )(),
        )

        resp = client.delete("/api/openapi/dart-key")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["envPath"] == "C:/tmp/.env"
        assert data["openDart"]["configured"] is False


class TestModels:
    """모델 catalog 소유권은 열린 세션의 CLI로 이관됐다.

    /api/models/{runtimeId}는 어떤 ID든 빈 목록과 새 endpoint 안내만 반환한다.
    """

    def test_models_endpoint_delegates_to_session_cli(self, client):
        for runtimeId in ("codex", "claude", "ollama", "nonexistent"):
            resp = client.get(f"/api/models/{runtimeId}")
            assert resp.status_code == 200
            data = resp.json()
            assert data["models"] == []
            assert data["runtimeId"] == runtimeId
            assert "/api/agent/sessions" in data["detail"]


class TestDataStats:
    def test_data_stats(self, client):
        """GET /api/data/stats — 데이터 현황."""
        resp = client.get("/api/data/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "version" in data
        assert "panel" in data
        assert "finance" in data
        assert isinstance(data["panel"]["count"], int)
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
        """GET /api/oauth/status: agent CLI 소유를 알리는 호환 응답."""
        resp = client.get("/api/oauth/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["done"] is True
        assert data["managedBy"] == "agent-cli"

    def test_oauth_logout_is_gone(self, client):
        """POST /api/oauth/logout: OAuth 토큰 저장소 제거로 410."""
        resp = client.post("/api/oauth/logout")
        assert resp.status_code == 410


class TestCodexAuth:
    def test_codex_logout_is_gone(self, client):
        """POST /api/codex/logout: CLI 인증은 각 agent CLI 공식 명령 소유라 410."""
        resp = client.post("/api/codex/logout")
        assert resp.status_code == 410
        assert "공식 명령" in resp.json()["detail"]


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
        assert "surface" in data
        assert data["profile"]["status"] == "roadmap"

    def test_company_not_found(self, client):
        """GET /api/company/{code} — 없는 종목 → 404."""
        resp = client.get("/api/company/999999")
        assert resp.status_code == 404

    @requires_samsung_any
    def test_company_index(self, client):
        resp = client.get(f"/api/company/{SAMSUNG}/index")
        assert resp.status_code == 200
        data = resp.json()
        assert data["payload"]["type"] == "table"
        assert "chapter" in data["payload"]["columns"]

    @requires_samsung_any
    def test_company_show(self, client):
        resp = client.get(f"/api/company/{SAMSUNG}/show/BS")
        assert resp.status_code == 200
        data = resp.json()
        assert data["payload"]["type"] == "table"
        assert "rows" in data["payload"]

    @requires_samsung_any
    def test_company_trace(self, client):
        resp = client.get(f"/api/company/{SAMSUNG}/trace/dividend")
        assert resp.status_code == 200
        data = resp.json()
        assert data["payload"]["type"] == "dict"
        assert data["payload"]["data"]["primarySource"] == "report"


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

    @pytest.mark.skipif(not _has_samsung_panel, reason="삼성전자 panel 데이터 없음")
    def test_preview_panel_module(self, client):
        """GET /api/data/preview — panel keywordTrend."""
        resp = client.get(f"/api/data/preview/{SAMSUNG}/keywordTrend")
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

    def test_plain_chat_uses_agent_runtime_path(self, client, monkeypatch):
        """비스트리밍 /api/ask는 설치형 agent runtime(kernel.ask)으로 답을 수집한다.

        runtimeId는 반드시 그대로 넘어가야 한다. 예전 direct provider 시절 여기서
        선택을 떨어뜨려 스트리밍 경로와 다른 모델로 답한 회귀(c81e64232)의
        agent-runtime 버전 가드다.
        """
        captured = {}

        def _fake_ask(question, **kwargs):
            captured["question"] = question
            captured["kwargs"] = kwargs
            return "core-answer"

        monkeypatch.setattr("dartlab.ai.kernel.ask", _fake_ask)

        resp = client.post(
            "/api/ask",
            json={"question": "안녕하세요", "stream": False, "runtimeId": "claude", "sessionId": "s-1"},
        )
        assert resp.status_code == 200
        assert resp.json()["answer"] == "core-answer"
        assert resp.json()["sessionId"] == "s-1"
        assert captured["question"] == "안녕하세요"
        assert captured["kwargs"]["runtimeId"] == "claude"
        assert captured["kwargs"]["sessionId"] == "s-1"
        assert captured["kwargs"]["stream"] is False

    def test_plain_chat_passes_company_as_stock_code_hint(self, client, monkeypatch):
        captured = {}

        def _fake_ask(question, **kwargs):
            captured["question"] = question
            captured["kwargs"] = kwargs
            return "core-answer"

        monkeypatch.setattr("dartlab.ai.kernel.ask", _fake_ask)

        resp = client.post(
            "/api/ask",
            json={"company": "005930", "question": "수익성 분석", "stream": False},
        )
        assert resp.status_code == 200
        assert captured["kwargs"]["stockCode"] == "005930"

    def test_ask_artifact_download(self, client, tmp_path, monkeypatch):
        from dartlab import config

        monkeypatch.setattr(config, "dataDir", str(tmp_path))
        day = "2026-04-28"
        artifact_dir = tmp_path / "ai-artifacts" / day
        artifact_dir.mkdir(parents=True)
        path = artifact_dir / "scan_result_test.csv"
        path.write_text("a,b\n1,2\n", encoding="utf-8")

        resp = client.get(f"/api/ask/artifacts/{day}/{path.name}")

        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        assert resp.text.startswith("a,b")

    def test_ask_artifact_download_rejects_path_traversal(self, client):
        resp = client.get("/api/ask/artifacts/2026-04-28/..%5Csecret.csv")

        assert resp.status_code == 404

    def test_topic_summary_uses_core_stream_path(self, monkeypatch):
        class DummyCompany:
            corpName = "테스트기업"
            stockCode = "000000"

            def panel(self, topic):
                """공개 계약은 ``panel`` 이다. ``show`` 폴백은 걷어냈으므로 대역도 따른다."""
                if topic == "businessOverview":
                    return pl.DataFrame({"topic": ["businessOverview"]})
                return None

        async def _fake_topic_summary(company, topic, **kwargs):
            assert company.stockCode == "000000"
            assert topic == "businessOverview"
            yield {"event": "context", "data": '{"module":"_focus","text":"ctx"}'}
            yield {"event": "chunk", "data": '{"text":"summary"}'}

        monkeypatch.setattr("dartlab.server.api.company.get_company", lambda code: DummyCompany())
        monkeypatch.setattr("dartlab.server.api.company.stream_topic_summary", _fake_topic_summary)

        from dartlab.server.api.company import apiCompanyTopicSummary

        async def collect_events() -> list:
            response = await apiCompanyTopicSummary("000000", "businessOverview")
            events = []
            async for chunk in response.body_iterator:
                events.append(chunk)
            return events

        events = asyncio.run(collect_events())
        assert any(event.get("event") == "context" for event in events)
        assert any(event.get("event") == "chunk" for event in events)
        assert any("summary" in event.get("data", "") for event in events)


# ── 유틸리티/로직 단위 테스트 ──


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
        from unittest.mock import patch

        from dartlab.server.cache import CompanyCache

        cache = CompanyCache()
        # 메모리 압박으로 _max_size가 줄어드는 것을 방지
        with patch.object(cache, "_check_memory_pressure"):
            for i in range(10):
                code = f"{i:06d}"
                m = MagicMock()
                m.stockCode = code
                cache.put(code, m, None)
        assert len(cache) == 5
        assert cache.get("000000") is None
        assert cache.get("000009") is not None

    def test_update_snapshot(self):
        from dartlab.server.cache import CompanyCache

        cache = CompanyCache()
        mock = MagicMock()
        cache.put("005930", mock, {"old": True})
        cache.updateSnapshot("005930", {"new": True})
        result = cache.get("005930")
        assert result[1] == {"new": True}


# ── Phase 1-5: 추가 Company API 엔드포인트 ──


class TestCompanyAPIExtended:
    """panel, toc, insights, network, scan 등 추가 엔드포인트."""

    @requires_samsung_any
    def test_company_toc(self, client):
        """GET /api/company/{code}/panel/toc — panel 목차 (chapter > sectionLeaf)."""
        resp = client.get(f"/api/company/{SAMSUNG}/panel/toc")
        assert resp.status_code == 200
        data = resp.json()
        assert "chapters" in data
        assert "periods" in data

    def test_company_toc_not_found(self, client):
        resp = client.get("/api/company/999999/panel/toc")
        assert resp.status_code == 404

    @requires_samsung_any
    def test_company_init(self, client):
        """GET /api/company/{code}/panel/init — 초기화 번들 (toc + 첫 절 grid)."""
        resp = client.get(f"/api/company/{SAMSUNG}/panel/init")
        assert resp.status_code == 200
        data = resp.json()
        assert data["stockCode"] == SAMSUNG
        assert "toc" in data
        assert "firstSectionKey" in data

    @pytest.mark.skipif(not _has_samsung_finance, reason="삼성전자 finance 데이터 없음")
    def test_company_insights(self, client):
        """GET /api/company/{code}/insights — 인사이트 등급."""
        resp = client.get(f"/api/company/{SAMSUNG}/insights")
        if resp.status_code == 200:
            data = resp.json()
            assert "grades" in data or "insights" in data or "profile" in data

    def test_company_insights_not_found(self, client):
        resp = client.get("/api/company/999999/insights")
        assert resp.status_code == 404

    @requires_samsung_any
    def test_company_network(self, client):
        """GET /api/company/{code}/network — 관계 네트워크."""
        resp = client.get(f"/api/company/{SAMSUNG}/network")
        # 네트워크 데이터가 없을 수 있으므로 200 또는 404 허용
        assert resp.status_code in (200, 404)

    @requires_samsung_any
    def test_company_scan(self, client):
        """GET /api/company/{code}/scan/{axis} — 축별 스캔."""
        resp = client.get(f"/api/company/{SAMSUNG}/scan/profitability")
        # 스캔 데이터가 없을 수 있으므로 200 또는 404 허용
        assert resp.status_code in (200, 404, 422)

    @requires_samsung_any
    def test_company_show_all(self, client):
        """GET /api/company/{code}/show-all/{topic} — 전체 블록."""
        resp = client.get(f"/api/company/{SAMSUNG}/show-all/companyOverview")
        assert resp.status_code in (200, 404)

    @requires_samsung_any
    def test_company_panel(self, client):
        """GET /api/company/{code}/panel — panel grid (전체 격자)."""
        resp = client.get(f"/api/company/{SAMSUNG}/panel")
        assert resp.status_code in (200, 404)
        if resp.status_code == 200:
            data = resp.json()
            assert "rows" in data
            assert "periods" in data
