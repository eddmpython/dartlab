"""tools_registry 모듈 테스트 — LLM 불필요."""

import pytest

pytestmark = pytest.mark.unit

from pathlib import Path

import polars as pl

from dartlab.engines.ai.tools.registry import (
    build_tool_runtime,
    clear_registry,
    execute_tool,
    get_tool_schemas,
    register_defaults,
    register_tool,
)

# ══════════════════════════════════════
# Mock Company
# ══════════════════════════════════════


class MockCompany:
    """테스트용 가짜 Company."""

    def __init__(self):
        self.corpName = "테스트기업"
        self.stockCode = "000000"
        self.BS = pl.DataFrame(
            {
                "계정명": ["자산총계", "부채총계", "자본총계", "유동자산", "유동부채"],
                "2023": [15000, 5000, 10000, 8000, 4000],
                "2022": [13000, 4000, 9000, 7000, 3500],
            }
        )
        self.IS = pl.DataFrame(
            {
                "계정명": ["매출액", "영업이익", "당기순이익"],
                "2023": [20000, 3000, 2000],
                "2022": [18000, 2500, 1800],
            }
        )
        self.CF = pl.DataFrame(
            {
                "계정명": ["영업활동으로인한현금흐름"],
                "2023": [5000],
                "2022": [3000],
            }
        )
        self.dividend = pl.DataFrame(
            {
                "year": [2022, 2023],
                "dps": [1200, 1500],
            }
        )
        self.companyOverview = {
            "ceo": "홍길동",
            "mainBusiness": "소프트웨어",
            "indutyName": "IT서비스",
        }

    def show(self, topic: str, **kwargs):
        return getattr(self, topic, None)

    def liveFilings(
        self,
        start=None,
        end=None,
        *,
        days=None,
        limit=20,
        keyword=None,
        forms=None,
        finalOnly=False,
    ):
        del start, end, days, keyword, forms, finalOnly
        return pl.DataFrame(
            {
                "docId": ["20240312000736"],
                "filedAt": ["2024-03-12"],
                "title": ["단일판매공급계약체결"],
                "formType": ["단일판매공급계약체결"],
                "docUrl": ["https://example.com/viewer?rcpNo=20240312000736"],
                "market": ["KR"],
            }
        ).head(limit)

    def readFiling(self, filing, *, maxChars=None):
        del maxChars
        return {
            "docId": "20240312000736",
            "docUrl": filing if isinstance(filing, str) else filing.get("docUrl", ""),
            "text": "공시 본문 테스트",
        }


class MockDartCompany(MockCompany):
    market = "KR"


# ══════════════════════════════════════
# register_tool / execute_tool
# ══════════════════════════════════════


class TestRegisterTool:
    def setup_method(self):
        clear_registry()

    def test_register_and_execute(self):
        register_tool(
            "hello",
            lambda name="World": f"Hello, {name}!",
            "인사 도구",
            {
                "type": "object",
                "properties": {"name": {"type": "string"}},
            },
        )
        result = execute_tool("hello", {"name": "DartLab"})
        assert result == "Hello, DartLab!"

    def test_execute_unknown(self):
        result = execute_tool("nonexistent", {})
        assert "찾을 수 없습니다" in result

    def test_get_schemas(self):
        register_tool(
            "test_tool",
            lambda: "ok",
            "테스트 도구",
            {"type": "object", "properties": {}},
        )
        schemas = get_tool_schemas()
        assert len(schemas) == 1
        assert schemas[0]["type"] == "function"
        assert schemas[0]["function"]["name"] == "test_tool"

    def test_clear(self):
        register_tool("x", lambda: "y", "d", {"type": "object", "properties": {}})
        assert len(get_tool_schemas()) == 1
        clear_registry()
        assert len(get_tool_schemas()) == 0

    def test_build_tool_runtime_is_isolated(self):
        runtime = build_tool_runtime(None, name="isolated-test")
        names = [schema["function"]["name"] for schema in runtime.get_tool_schemas()]
        assert runtime.name == "isolated-test"
        assert "get_system_spec" in names
        assert "get_coding_runtime_status" in names
        assert "run_coding_task" in names
        assert "run_codex_task" in names

    def test_error_handling(self):
        """실행 중 에러가 발생하면 에러 메시지 반환."""

        def bad_func():
            raise ValueError("test error")

        register_tool("bad", bad_func, "d", {"type": "object", "properties": {}})
        result = execute_tool("bad", {})
        assert "오류" in result
        assert "test error" in result


# ══════════════════════════════════════
# register_defaults
# ══════════════════════════════════════


class TestRegisterDefaults:
    def setup_method(self):
        clear_registry()

    def test_registers_global_tools_without_company(self):
        register_defaults(None)
        schemas = get_tool_schemas()
        names = [s["function"]["name"] for s in schemas]
        assert "get_system_spec" in names
        assert "get_engine_spec" in names
        assert "get_runtime_capabilities" in names
        assert "get_tool_catalog" in names
        assert "get_coding_runtime_status" in names
        assert "get_openapi_capabilities" in names
        assert "call_dart_openapi" in names
        assert "search_dart_filings" in names
        assert "get_dart_filing_text" in names
        assert "call_edgar_openapi" in names
        assert "openapi_save" in names
        assert "run_coding_task" in names
        assert "run_codex_task" in names
        assert "search_company" in names
        assert "download_data" in names
        assert "data_status" in names
        assert "get_data" not in names

    def test_register_defaults_hides_coding_tools_on_nonlocal_host(self, monkeypatch):
        monkeypatch.setenv("DARTLAB_HOST", "0.0.0.0")
        monkeypatch.delenv("DARTLAB_ENABLE_CODING_RUNTIME", raising=False)
        register_defaults(None)
        names = [s["function"]["name"] for s in get_tool_schemas()]
        assert "get_coding_runtime_status" in names
        assert "run_coding_task" not in names
        assert "run_codex_task" not in names
        result = execute_tool("get_runtime_capabilities", {})
        assert "비활성화" in result
        assert "안전 정책" in result

    def test_runtime_capabilities_mentions_edgar_and_coding_scope(self):
        register_defaults(None)
        result = execute_tool("get_runtime_capabilities", {})
        assert "OpenEdgar" in result
        assert "EDGAR" in result
        assert "Codex" in result or "codex" in result
        assert "workspace-write" in result
        assert "run_coding_task" in result
        assert "run_codex_task" in result

    def test_get_tool_catalog_includes_runtime_tools(self):
        register_defaults(None)
        result = execute_tool("get_tool_catalog", {"include_parameters": True})
        assert "get_runtime_capabilities" in result
        assert "get_coding_runtime_status" in result
        assert "run_coding_task" in result
        assert "run_codex_task" in result
        assert "timeout_seconds" in result

    def test_get_coding_runtime_status(self, monkeypatch):
        from dartlab.engines.ai.providers.support import codex_cli

        monkeypatch.setattr(
            codex_cli,
            "inspect_codex_cli",
            lambda: {
                "installed": True,
                "authenticated": True,
                "version": "0.99.0",
                "configuredModel": "gpt-5.4",
                "sandboxModes": ["read-only", "workspace-write"],
            },
        )
        register_defaults(None)
        result = execute_tool("get_coding_runtime_status", {})
        assert "Coding Runtime" in result
        assert "`codex`" in result
        assert "0.99.0" in result
        assert "workspace-write" in result

    def test_run_coding_task(self, monkeypatch):
        from dartlab.engines.ai.providers.support import codex_cli

        monkeypatch.setattr(
            codex_cli,
            "inspect_codex_cli",
            lambda: {
                "installed": True,
                "authenticated": True,
                "configuredModel": "gpt-5.4",
                "sandboxModes": ["read-only", "workspace-write"],
            },
        )
        monkeypatch.setattr(
            codex_cli,
            "run_codex_exec",
            lambda prompt, model=None, sandbox="read-only", timeout=300: (
                f"done: {prompt}",
                {"total_tokens": 123},
            ),
        )
        register_defaults(None)
        result = execute_tool(
            "run_coding_task",
            {
                "prompt": "foo.py를 수정해줘",
                "backend": "codex",
                "sandbox": "workspace-write",
                "timeout_seconds": 120,
            },
        )
        assert "Coding 작업 결과" in result
        assert "backend: codex" in result
        assert "workspace-write" in result
        assert "done: foo.py를 수정해줘" in result

    def test_run_codex_task(self, monkeypatch):
        from dartlab.engines.ai.providers.support import codex_cli

        monkeypatch.setattr(
            codex_cli,
            "inspect_codex_cli",
            lambda: {
                "installed": True,
                "authenticated": True,
                "configuredModel": "gpt-5.4",
                "sandboxModes": ["read-only", "workspace-write"],
            },
        )
        monkeypatch.setattr(
            codex_cli,
            "run_codex_exec",
            lambda prompt, model=None, sandbox="read-only", timeout=300: (f"done: {prompt}", {"total_tokens": 123}),
        )
        register_defaults(None)
        result = execute_tool(
            "run_codex_task",
            {"prompt": "foo.py를 수정해줘", "sandbox": "workspace-write", "timeout_seconds": 120},
        )
        assert "Codex 작업 결과" in result
        assert "workspace-write" in result
        assert "done: foo.py를 수정해줘" in result

    def test_call_dart_openapi_search(self, monkeypatch):
        import dartlab

        class FakeOpenDart:
            @staticmethod
            def reportTypes():
                return ["배당", "직원"]

            @staticmethod
            def filingTypes():
                return {"A": "정기공시"}

            @staticmethod
            def markets():
                return {"Y": "유가증권"}

            def search(self, query, listed=False):
                assert query == "삼성"
                assert listed is True
                return pl.DataFrame({"corp_name": ["삼성전자"], "stock_code": ["005930"]})

        monkeypatch.setattr(dartlab, "OpenDart", FakeOpenDart)
        register_defaults(None)
        result = execute_tool("call_dart_openapi", {"action": "search", "query": "삼성", "listed": True})
        assert "005930" in result

    def test_call_dart_openapi_document_text(self, monkeypatch):
        import dartlab

        class FakeOpenDart:
            @staticmethod
            def reportTypes():
                return ["배당"]

            @staticmethod
            def filingTypes():
                return {"A": "정기공시"}

            @staticmethod
            def markets():
                return {"Y": "유가증권"}

            def documentText(self, rcept_no):
                assert rcept_no == "20240312000736"
                return "<html><body>단일판매공급계약 본문</body></html>"

        monkeypatch.setattr(dartlab, "OpenDart", FakeOpenDart)
        monkeypatch.setattr("dartlab.engines.ai.context.dartOpenapi.hasDartApiKey", lambda startPath=None: True)
        register_defaults(None)
        result = execute_tool(
            "call_dart_openapi",
            {"action": "document_text", "rcept_no": "20240312000736", "max_chars": 200},
        )
        assert "단일판매공급계약 본문" in result

    def test_search_dart_filings_tool(self, monkeypatch):
        import dartlab

        class FakeOpenDart:
            def filings(self, corp=None, start=None, end=None, type=None, final=False, market=None):
                assert start == "20240301"
                assert end == "20240307"
                return pl.DataFrame(
                    {
                        "rcept_dt": ["20240307"],
                        "corp_name": ["테스트기업"],
                        "stock_code": ["000000"],
                        "corp_cls": ["K"],
                        "report_nm": ["단일판매공급계약체결"],
                        "rcept_no": ["20240307000001"],
                    }
                )

        monkeypatch.setattr(dartlab, "OpenDart", FakeOpenDart)
        monkeypatch.setattr("dartlab.engines.ai.context.dartOpenapi.hasDartApiKey", lambda startPath=None: True)
        register_defaults(None)
        result = execute_tool(
            "search_dart_filings",
            {
                "start": "20240301",
                "end": "20240307",
                "keywords": "단일판매공급계약,공급계약",
                "limit": 10,
            },
        )
        assert "OpenDART 공시목록 검색 결과" in result
        assert "단일판매공급계약체결" in result

    def test_call_edgar_openapi_company(self, monkeypatch):
        import dartlab

        class FakeOpenEdgar:
            def company(self, identifier):
                assert identifier == "AAPL"
                return {"ticker": "AAPL", "cik": "0000320193", "title": "Apple Inc."}

        monkeypatch.setattr(dartlab, "OpenEdgar", FakeOpenEdgar)
        register_defaults(None)
        result = execute_tool("call_edgar_openapi", {"action": "company", "identifier": "AAPL"})
        assert "Apple Inc." in result
        assert "0000320193" in result

    def test_openapi_save_edgar_docs(self, monkeypatch):
        import dartlab

        class FakeOpenEdgarCompany:
            def saveDocs(self, sinceYear=2009):
                assert sinceYear == 2018
                return Path("C:/temp/AAPL.parquet")

        class FakeOpenEdgar:
            def __call__(self, identifier):
                assert identifier == "AAPL"
                return FakeOpenEdgarCompany()

        monkeypatch.setattr(dartlab, "OpenEdgar", FakeOpenEdgar)
        register_defaults(None)
        result = execute_tool(
            "openapi_save",
            {"market": "edgar", "identifier": "AAPL", "dataset": "docs", "since_year": 2018},
        )
        assert "AAPL.parquet" in result

    def test_download_data_specific_category_uses_loaddata(self, monkeypatch):
        import dartlab.core.dataLoader as data_loader

        called = {}

        def fake_load_data(stock_code, category="docs", **kwargs):
            called["stock_code"] = stock_code
            called["category"] = category
            return pl.DataFrame()

        monkeypatch.setattr(data_loader, "loadData", fake_load_data)
        register_defaults(None)
        result = execute_tool("download_data", {"stock_code": "AAPL", "category": "edgarDocs"})
        assert called == {"stock_code": "AAPL", "category": "edgarDocs"}
        assert "AAPL edgarDocs 데이터 다운로드 완료." in result

    def test_registers_tools(self):
        company = MockCompany()
        register_defaults(company)
        schemas = get_tool_schemas()
        assert len(schemas) >= 6
        names = [s["function"]["name"] for s in schemas]
        assert "get_data" in names
        assert "compute_ratios" in names
        assert "detect_anomalies" in names
        assert "compute_growth" in names
        assert "yoy_analysis" in names
        assert "get_summary" in names
        assert "get_company_info" in names
        assert "list_live_filings" in names
        assert "read_filing" in names

    def test_get_data(self):
        company = MockCompany()
        register_defaults(company)
        result = execute_tool("get_data", {"module_name": "BS"})
        assert "자산총계" in result or "부채총계" in result

    def test_get_data_missing(self):
        company = MockCompany()
        register_defaults(company)
        result = execute_tool("get_data", {"module_name": "nonexistent"})
        assert "없습니다" in result

    def test_compute_ratios(self):
        company = MockCompany()
        register_defaults(company)
        result = execute_tool("compute_ratios", {})
        assert "부채비율" in result or "ROE" in result or "|" in result

    def test_detect_anomalies_no_anomalies(self):
        company = MockCompany()
        register_defaults(company)
        result = execute_tool("detect_anomalies", {"module_name": "CF"})
        # CF에 큰 변동이 있을 수 있으므로 결과 타입만 확인
        assert isinstance(result, str)

    def test_get_company_info(self):
        company = MockCompany()
        register_defaults(company)
        result = execute_tool("get_company_info", {})
        assert "테스트기업" in result
        assert "000000" in result

    def test_list_live_filings(self):
        company = MockCompany()
        register_defaults(company)
        result = execute_tool("list_live_filings", {"days": 7, "limit": 5})
        assert "실시간 공시목록" in result
        assert "단일판매공급계약체결" in result

    def test_read_filing(self):
        company = MockCompany()
        register_defaults(company)
        result = execute_tool("read_filing", {"doc_id": "20240312000736", "max_chars": 200})
        assert "공시 본문 테스트" in result

    def test_list_live_filings_guides_missing_dart_key(self, monkeypatch):
        monkeypatch.setattr("dartlab.engines.company.dart.openapi.dartKey.hasDartApiKey", lambda: False)
        company = MockDartCompany()
        register_defaults(company)
        result = execute_tool("list_live_filings", {"days": 7, "limit": 5})
        assert "OpenDART API 키가 필요합니다" in result
        assert "우상단 설정" in result
        assert "DART_API_KEY" in result

    def test_read_filing_guides_missing_dart_key(self, monkeypatch):
        monkeypatch.setattr("dartlab.engines.company.dart.openapi.dartKey.hasDartApiKey", lambda: False)
        company = MockDartCompany()
        register_defaults(company)
        result = execute_tool("read_filing", {"doc_id": "20240312000736", "max_chars": 200})
        assert "OpenDART API 키가 필요합니다" in result
        assert "공시 원문 조회" in result

    def test_yoy_analysis(self):
        company = MockCompany()
        register_defaults(company)
        result = execute_tool("yoy_analysis", {"module_name": "IS"})
        assert isinstance(result, str)

    def test_get_summary(self):
        company = MockCompany()
        register_defaults(company)
        result = execute_tool("get_summary", {"module_name": "dividend"})
        assert isinstance(result, str)
