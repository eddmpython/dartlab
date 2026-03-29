"""Server API 엔드포인트 테스트.

데이터 독립 테스트 (status, configure, models, spec, stats, search, SPA)와
데이터 의존 테스트 (company, modules, preview, export)를 분리한다.
"""

from unittest.mock import MagicMock

import polars as pl
import pytest

starlette = pytest.importorskip("starlette", reason="starlette not installed (optional [ai] dependency)")
from starlette.testclient import TestClient  # noqa: E402

from dartlab.server import app  # noqa: E402
from tests.conftest import SAMSUNG, _has_data

_has_samsung_docs = _has_data(SAMSUNG, "docs")
_has_samsung_finance = _has_data(SAMSUNG, "finance")
_has_any_samsung = _has_samsung_docs or _has_samsung_finance

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
        assert "authenticated" in data["codex"]

    def test_status_oauth_codex_detail(self, client):
        """GET /api/status — oauth-codex 상세 정보 포함."""
        resp = client.get("/api/status")
        data = resp.json()
        assert "oauthCodex" in data
        assert "authenticated" in data["oauthCodex"]
        assert "tokenStored" in data["oauthCodex"]

    def test_status_version_not_unknown(self, client):
        """GET /api/status — 버전이 'unknown'이 아님."""
        resp = client.get("/api/status")
        data = resp.json()
        assert data["version"] != "unknown"

    def test_status_provider_probe_only_targets_selected_provider(self, client, monkeypatch):
        """GET /api/status?provider=codex — 선택 provider만 probe."""
        probed: list[str] = []
        ollama_probe_flags: list[bool] = []

        def _fake_probe(prov):
            probed.append(prov)
            return True, f"{prov}-model", True

        def _fake_ollama_detail(*, probe):
            ollama_probe_flags.append(probe)
            return {"installed": False, "running": None, "gpu": None, "checked": probe}

        monkeypatch.setattr("dartlab.server.api.ai.probe_provider_availability", _fake_probe)
        monkeypatch.setattr("dartlab.server.api.ai.build_ollama_detail", _fake_ollama_detail)

        resp = client.get("/api/status", params={"provider": "codex"})
        assert resp.status_code == 200
        assert probed == ["codex"]
        assert ollama_probe_flags == [False]

    def test_status_probe_zero_skips_provider_checks(self, client, monkeypatch):
        """GET /api/status?probe=0 — provider probe를 생략."""
        monkeypatch.setattr(
            "dartlab.server.api.ai.probe_provider_availability",
            lambda prov: (_ for _ in ()).throw(AssertionError("provider probe should not run")),
        )

        resp = client.get("/api/status", params={"probe": 0})
        assert resp.status_code == 200
        data = resp.json()
        assert data["providers"]["codex"]["checked"] is False
        assert data["providers"]["ollama"]["checked"] is False

    def test_status_without_provider_probes_only_selected_provider(self, client, monkeypatch):
        """GET /api/status — 명시하지 않으면 shared profile의 선택 provider만 probe."""
        from dartlab.ai import configure as configure_global

        configure_global(provider="openai", model="gpt-5.4")

        probed: list[str] = []
        ollama_probe_flags: list[bool] = []

        def _fake_probe(prov):
            probed.append(prov)
            return True, f"{prov}-model", True

        def _fake_ollama_detail(*, probe):
            ollama_probe_flags.append(probe)
            return {"installed": True, "running": True, "gpu": None, "checked": probe}

        monkeypatch.setattr("dartlab.server.api.ai.probe_provider_availability", _fake_probe)
        monkeypatch.setattr("dartlab.server.api.ai.build_ollama_detail", _fake_ollama_detail)

        resp = client.get("/api/status")
        assert resp.status_code == 200
        data = resp.json()
        assert probed == ["openai"]
        assert ollama_probe_flags == [False]
        assert data["providers"]["openai"]["checked"] is True
        assert data["providers"]["ollama"]["checked"] is False

    def test_should_preload_ollama_requires_selected_provider(self, monkeypatch):
        """Ollama preload는 명시적 활성화 + 선택 provider가 ollama일 때만."""
        from dartlab.ai import configure as configure_global
        from dartlab.server import _should_preload_ollama

        monkeypatch.setenv("DARTLAB_PRELOAD_OLLAMA", "1")

        configure_global(provider="openai", model="gpt-5.4")
        assert _should_preload_ollama() is False

        configure_global(provider="ollama", model="qwen3")
        assert _should_preload_ollama() is True

    def test_should_preload_ollama_when_any_role_uses_ollama(self, monkeypatch):
        """role binding 중 하나가 ollama면 preload 대상이다."""
        from dartlab.ai import configure as configure_global
        from dartlab.server import _should_preload_ollama

        monkeypatch.setenv("DARTLAB_PRELOAD_OLLAMA", "1")

        configure_global(provider="openai", model="gpt-5.4")
        configure_global(provider="ollama", model="qwen3", role="summary")
        assert _should_preload_ollama() is True

    def test_suggest_endpoint_returns_questions_and_data_ready(self, client, monkeypatch):
        """GET /api/suggest — 추천 질문과 데이터 준비 상태를 함께 반환한다."""
        company = MagicMock()
        company.stockCode = "005930"
        company.corpName = "삼성전자"

        monkeypatch.setattr("dartlab.server.services.company_api.get_company", lambda code: company)
        monkeypatch.setattr(
            "dartlab.ai.conversation.suggestions.suggestQuestions",
            lambda _: ["이 회사의 핵심 투자 포인트를 한눈에 정리해주세요"],
        )
        monkeypatch.setattr(
            "dartlab.ai.conversation.data_ready.getDataReadyStatus",
            lambda code: {
                "stockCode": code,
                "allReady": False,
                "available": ["docs"],
                "missing": ["finance", "report"],
                "categories": {},
            },
        )

        resp = client.get("/api/suggest", params={"stockCode": "005930"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["stockCode"] == "005930"
        assert data["company"] == "삼성전자"
        assert data["suggestions"] == ["이 회사의 핵심 투자 포인트를 한눈에 정리해주세요"]
        assert data["dataReady"]["missing"] == ["finance", "report"]


class TestConfigure:
    def test_validate_provider_ollama(self, client):
        """POST /api/provider/validate — provider 검증."""
        resp = client.post(
            "/api/provider/validate",
            json={"provider": "ollama"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["provider"] == "ollama"
        assert "available" in data

    def test_validate_provider_with_model(self, client):
        """POST /api/provider/validate — model 지정."""
        resp = client.post(
            "/api/provider/validate",
            json={"provider": "ollama", "model": "qwen3"},
        )
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    def test_validate_provider_does_not_mutate_global_config(self, client, monkeypatch):
        from dartlab.ai import configure as configure_global
        from dartlab.ai import get_config

        class DummyProvider:
            def __init__(self, config):
                self.resolved_model = config.model or "dummy-model"

            def check_available(self):
                return True

        monkeypatch.setattr("dartlab.ai.providers.create_provider", lambda config: DummyProvider(config))
        configure_global(provider="ollama", model="qwen3")
        before = get_config()

        resp = client.post(
            "/api/provider/validate",
            json={"provider": "openai", "model": "gpt-5.4", "api_key": "sk-test"},
        )
        assert resp.status_code == 200
        after = get_config()
        assert after.provider == before.provider
        assert after.model == before.model

    def test_configure_alias_still_works(self, client):
        """POST /api/configure — 구버전 alias 유지."""
        resp = client.post(
            "/api/configure",
            json={"provider": "ollama"},
        )
        assert resp.status_code == 200
        assert resp.json()["ok"] is True


class TestAiProfile:
    def test_get_ai_profile(self, client):
        resp = client.get("/api/ai/profile")
        assert resp.status_code == 200
        data = resp.json()
        assert "defaultProvider" in data
        assert "catalog" in data
        assert "providers" in data
        assert "roles" in data
        assert isinstance(data["catalog"], list)
        assert all(item["id"] != "claude" for item in data["catalog"])
        assert "codex" in data["providers"]

    def test_put_ai_profile_updates_shared_config(self, client):
        from dartlab.ai import get_config

        resp = client.put(
            "/api/ai/profile",
            json={"provider": "openai", "model": "gpt-5.4"},
        )
        assert resp.status_code == 200
        config = get_config()
        assert config.provider == "openai"
        assert config.model == "gpt-5.4"

    def test_post_ai_profile_secret_updates_shared_secret(self, client):
        from dartlab.ai import get_config

        resp = client.post(
            "/api/ai/profile/secrets",
            json={"provider": "openai", "api_key": "sk-test"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["providers"]["openai"]["secretConfigured"] is True
        config = get_config("openai")
        assert config.api_key == "sk-test"


class TestOpenDartKey:
    def test_status_includes_open_dart_block(self, client):
        resp = client.get("/api/status", params={"probe": 0})
        assert resp.status_code == 200
        data = resp.json()
        assert "configured" in data["openDart"]
        assert "source" in data["openDart"]
        assert "envPath" in data["openDart"]

    def test_validate_dart_key_endpoint(self, client, monkeypatch):
        monkeypatch.setattr(
            "dartlab.providers.dart.openapi.dartKey.validateDartApiKey",
            lambda key: {"ok": True, "validatedKey": key[-4:]},
        )
        monkeypatch.setattr(
            "dartlab.providers.dart.openapi.dartKey.getDartKeyStatus",
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

        resp = client.post("/api/openapi/dart-key/validate", json={"api_key": "test-dart-key"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["validatedKey"] == "-key"
        assert "openDart" in data

    def test_save_dart_key_endpoint(self, client, monkeypatch):
        monkeypatch.setattr(
            "dartlab.providers.dart.openapi.dartKey.saveDartKeyToDotenv",
            lambda key: "C:/tmp/.env",
        )
        monkeypatch.setattr(
            "dartlab.providers.dart.openapi.dartKey.getDartKeyStatus",
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
            "dartlab.providers.dart.openapi.dartKey.clearDartKeyFromDotenv",
            lambda: "C:/tmp/.env",
        )
        monkeypatch.setattr(
            "dartlab.providers.dart.openapi.dartKey.getDartKeyStatus",
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
    def test_static_providers(self, client):
        """GET /api/models/{provider} — 정적 모델 목록."""
        for prov in ("codex", "oauth-codex"):
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

    def test_removed_provider_returns_empty_models(self, client):
        """GET /api/models/claude — 제거된 provider는 빈 목록."""
        resp = client.get("/api/models/claude")
        assert resp.status_code == 200
        data = resp.json()
        assert "models" in data
        assert data["models"] == []


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


class TestCodexAuth:
    def test_codex_logout(self, client, monkeypatch):
        """POST /api/codex/logout — Codex CLI 인증 제거."""
        monkeypatch.setattr("dartlab.ai.providers.support.codex_cli.logout_codex_cli", lambda: None)
        resp = client.post("/api/codex/logout")
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

    def test_ask_passes_request_api_key(self, client, monkeypatch):
        captured = {}

        class DummyCompany:
            corpName = "삼성전자"
            stockCode = "999998"

            def ask(self, question, **kwargs):
                captured["question"] = question
                captured["kwargs"] = kwargs
                return "ok"

        monkeypatch.setattr("dartlab.server.resolve.Company", lambda identifier: DummyCompany())
        resp = client.post(
            "/api/ask",
            json={
                "company": "삼성전자",
                "question": "매출 알려줘",
                "stream": False,
                "provider": "openai",
                "model": "gpt-5.4",
                "api_key": "sk-test",
            },
        )
        assert resp.status_code == 200
        assert captured["kwargs"]["provider"] == "openai"
        assert captured["kwargs"]["model"] == "gpt-5.4"
        assert captured["kwargs"]["api_key"] == "sk-test"

    def test_plain_chat_uses_core_analysis_path(self, client, monkeypatch):
        captured = {}

        async def _fake_collect(company, question, **kwargs):
            captured["company"] = company
            captured["question"] = question
            captured["kwargs"] = kwargs
            return "core-answer"

        monkeypatch.setattr("dartlab.server.services.ai_analysis.collect_analysis_text", _fake_collect)

        resp = client.post(
            "/api/ask",
            json={"question": "안녕하세요", "stream": False, "provider": "openai", "model": "gpt-5.4"},
        )
        assert resp.status_code == 200
        assert resp.json()["answer"] == "core-answer"
        assert captured["company"] is None
        assert captured["question"] == "안녕하세요"
        assert captured["kwargs"]["provider"] == "openai"
        assert captured["kwargs"]["model"] == "gpt-5.4"
        assert captured["kwargs"]["use_tools"] is True

    def test_topic_summary_uses_core_stream_path(self, client, monkeypatch):
        class DummyCompany:
            corpName = "테스트기업"
            stockCode = "000000"

            def show(self, topic):
                if topic == "businessOverview":
                    return pl.DataFrame({"topic": ["businessOverview"]})
                return None

        async def _fake_stream(company, question, **kwargs):
            assert company.stockCode == "000000"
            assert "businessOverview" in question
            assert kwargs["view_context"]["topic"] == "businessOverview"
            yield {"event": "context", "data": '{"module":"_focus","text":"ctx"}'}
            yield {"event": "chunk", "data": '{"text":"summary"}'}

        monkeypatch.setattr("dartlab.server.api.company.get_company", lambda code: DummyCompany())
        monkeypatch.setattr("dartlab.server.services.ai_analysis.stream_analysis", _fake_stream)

        with client.stream("GET", "/api/company/000000/summary/businessOverview") as resp:
            body = b"".join(resp.iter_bytes()).decode()

        assert "event: context" in body
        assert "event: chunk" in body
        assert "summary" in body


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

        msg = build_ambiguous_msg(
            [
                {"corpName": "현대자동차", "stockCode": "005380"},
                {"corpName": "현대차증권", "stockCode": "001500"},
            ]
        )
        assert "현대자동차" in msg
        assert "현대차증권" in msg

    def test_needs_match_verification(self):
        from dartlab.server.resolve import needs_match_verification

        assert not needs_match_verification("삼성전자 분석해줘", "삼성전자")
        assert needs_match_verification("현대차 분석해줘", "현대차증권")
        assert not needs_match_verification("삼전 분석해줘", "삼성전자")

    def test_try_resolve_company_uses_view_context(self, monkeypatch):
        from dartlab.server.models import AskRequest
        from dartlab.server.resolve import try_resolve_company

        class DummyCompany:
            def __init__(self, identifier):
                self.stockCode = "005930" if identifier == "005930" else identifier
                self.corpName = "삼성전자"

        monkeypatch.setattr("dartlab.server.resolve.Company", DummyCompany)
        result = try_resolve_company(
            AskRequest(
                question="이 부분 왜 이래?",
                viewContext={
                    "type": "viewer",
                    "company": {"corpName": "삼성전자", "stockCode": "005930", "market": "dart"},
                    "topic": "dividend",
                    "topicLabel": "배당",
                },
            )
        )
        assert result.company is not None
        assert result.company.stockCode == "005930"

    def test_try_resolve_from_history_skips_invalid_company(self, monkeypatch):
        from dartlab.server.models import HistoryMessage, HistoryMeta
        from dartlab.server.resolve import try_resolve_from_history

        class DummyCompany:
            def __init__(self, identifier):
                if identifier == "111111":
                    raise ValueError("invalid")
                self.stockCode = identifier

        monkeypatch.setattr("dartlab.server.resolve.Company", DummyCompany)
        company = try_resolve_from_history(
            [
                HistoryMessage(role="assistant", text="이전 답변", meta=HistoryMeta(stockCode="111111")),
                HistoryMessage(role="assistant", text="최근 답변", meta=HistoryMeta(stockCode="005930")),
            ]
        )
        assert company is not None
        assert company.stockCode == "005930"


class TestChatUtils:
    def test_build_history_empty(self):
        from dartlab.server.chat import build_history_messages

        assert build_history_messages(None) == []

    def test_build_history_messages(self):
        from dartlab.server.chat import build_history_messages
        from dartlab.server.models import HistoryMessage

        msgs = build_history_messages(
            [
                HistoryMessage(role="user", text="삼성전자 분석해줘"),
                HistoryMessage(role="assistant", text="분석 결과입니다."),
            ]
        )
        assert len(msgs) == 2
        assert msgs[0]["role"] == "user"
        assert msgs[1]["role"] == "assistant"

    def test_build_history_with_meta(self):
        from dartlab.server.chat import build_history_messages
        from dartlab.server.models import HistoryMessage, HistoryMeta

        msgs = build_history_messages(
            [
                HistoryMessage(
                    role="assistant",
                    text="분석 결과",
                    meta=HistoryMeta(
                        company="삼성전자",
                        stockCode="005930",
                        modules=["IS", "BS"],
                        market="dart",
                        topic="dividend",
                        topicLabel="배당",
                        dialogueMode="company_analysis",
                        userGoal="현재 회사의 구체적 분석",
                    ),
                ),
            ]
        )
        assert len(msgs) == 1
        assert "삼성전자" in msgs[0]["content"]
        assert "005930" in msgs[0]["content"]
        assert "배당" in msgs[0]["content"]
        assert "company_analysis" in msgs[0]["content"]

    def test_extract_last_stock_code(self):
        from dartlab.server.chat import extract_last_stock_code
        from dartlab.server.models import HistoryMessage, HistoryMeta

        assert extract_last_stock_code(None) is None
        assert extract_last_stock_code([]) is None
        code = extract_last_stock_code(
            [
                HistoryMessage(role="user", text="질문"),
                HistoryMessage(
                    role="assistant",
                    text="답변",
                    meta=HistoryMeta(stockCode="005930"),
                ),
            ]
        )
        assert code == "005930"

    def test_build_dynamic_chat_prompt(self):
        from dartlab.server.chat import build_dynamic_chat_prompt
        from dartlab.server.dialogue import build_conversation_state
        from dartlab.server.models import ViewContext

        prompt = build_dynamic_chat_prompt()
        assert "DartLab" in prompt
        assert isinstance(prompt, str)
        assert len(prompt) > 100

        state = build_conversation_state(
            "이 부분 왜 이래?",
            view_context=ViewContext(
                type="viewer",
                company={"corpName": "삼성전자", "stockCode": "005930", "market": "dart"},
                topic="dividend",
                topicLabel="배당",
            ),
        )
        prompt_with_state = build_dynamic_chat_prompt(state)
        assert "현재 대화 상태" in prompt_with_state
        assert "배당" in prompt_with_state
        assert "응답 템플릿" in prompt_with_state

    def test_build_history_messages_compresses_long_text(self):
        from dartlab.server.chat import build_history_messages
        from dartlab.server.models import HistoryMessage

        long_text = "가" * 4000
        msgs = build_history_messages([HistoryMessage(role="assistant", text=long_text)])
        assert len(msgs) == 1
        assert len(msgs[0]["content"]) < 2500
        assert "..." in msgs[0]["content"]

    def test_build_focus_context(self):
        from dartlab.server.chat import build_focus_context
        from dartlab.server.dialogue import build_conversation_state
        from dartlab.server.models import ViewContext

        class DummyCompany:
            corpName = "삼성전자"
            stockCode = "005930"

            def show(self, topic, block=None):
                if block is None:
                    return pl.DataFrame(
                        {
                            "block": [0, 1],
                            "type": ["text", "table"],
                            "source": ["docs", "report"],
                            "preview": ["개요", "배당표"],
                        }
                    )
                return pl.DataFrame({"year": [2024, 2023], "dps": [1500, 1444]})

            def trace(self, topic):
                return {"primarySource": "report", "topic": topic}

        state = build_conversation_state(
            "왜 줄었지?",
            company=DummyCompany(),
            view_context=ViewContext(
                type="viewer",
                company={"corpName": "삼성전자", "stockCode": "005930", "market": "dart"},
                topic="dividend",
                topicLabel="배당",
            ),
        )
        text = build_focus_context(DummyCompany(), state)
        assert text is not None
        assert "현재 사용자가 보고 있는 섹션" in text
        assert "dividend" in text
        assert "primarySource" in text

    def test_build_snapshot_relaxes_financial_thresholds(self):
        from dartlab.core.sector.types import IndustryGroup, Sector, SectorInfo
        from dartlab.server.chat import build_snapshot

        class DummyRatios:
            revenueTTM = None
            operatingIncomeTTM = None
            netIncomeTTM = None
            operatingMargin = None
            roe = 8.3
            roa = 0.6
            debtRatio = None
            currentRatio = None
            fcf = None
            revenueGrowth3Y = None
            roic = None
            interestCoverage = None
            piotroskiFScore = None
            altmanZScore = None
            warnings = []

        class DummyCompany:
            ratios = DummyRatios()
            sector = SectorInfo(Sector.FINANCIALS, IndustryGroup.BANK, 1.0, "test")
            annual = None

        snapshot = build_snapshot(DummyCompany())
        assert snapshot is not None
        items = {item["label"]: item for item in snapshot["items"]}
        assert items["ROE"]["status"] == "good"
        assert items["ROA"]["status"] == "good"


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
        cache.update_snapshot("005930", {"new": True})
        result = cache.get("005930")
        assert result[1] == {"new": True}


# ── Phase 1-5: 추가 Company API 엔드포인트 ──


class TestCompanyAPIExtended:
    """sections, toc, insights, network, scan 등 추가 엔드포인트."""

    @requires_samsung_any
    def test_company_sections(self, client):
        """GET /api/company/{code}/sections — sections 수평화 테이블."""
        resp = client.get(f"/api/company/{SAMSUNG}/sections")
        assert resp.status_code == 200
        data = resp.json()
        assert data["stockCode"] == SAMSUNG
        assert "payload" in data

    def test_company_sections_not_found(self, client):
        resp = client.get("/api/company/999999/sections")
        assert resp.status_code == 404

    @requires_samsung_any
    def test_company_toc(self, client):
        """GET /api/company/{code}/toc — 목차."""
        resp = client.get(f"/api/company/{SAMSUNG}/toc")
        assert resp.status_code == 200
        data = resp.json()
        assert "chapters" in data

    def test_company_toc_not_found(self, client):
        resp = client.get("/api/company/999999/toc")
        assert resp.status_code == 404

    @requires_samsung_any
    def test_company_init(self, client):
        """GET /api/company/{code}/init — 초기화 번들."""
        resp = client.get(f"/api/company/{SAMSUNG}/init")
        assert resp.status_code == 200
        data = resp.json()
        assert data["stockCode"] == SAMSUNG
        assert "toc" in data
        assert "firstTopic" in data

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
    def test_company_viewer_topic(self, client):
        """GET /api/company/{code}/viewer/{topic} — 뷰어 데이터."""
        resp = client.get(f"/api/company/{SAMSUNG}/viewer/companyOverview")
        assert resp.status_code in (200, 404)
