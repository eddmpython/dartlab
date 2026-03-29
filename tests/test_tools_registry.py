"""tools_registry 모듈 테스트 — LLM 불필요."""

import pytest

pytestmark = pytest.mark.unit

from pathlib import Path

import polars as pl

from dartlab.ai.tools.registry import (
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
        assert "execute_code" in names

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

    def test_registers_execute_code_without_company(self):
        register_defaults(None)
        schemas = get_tool_schemas()
        names = [s["function"]["name"] for s in schemas]
        assert "execute_code" in names
        assert len(names) == 1

    def test_registers_execute_code_with_company(self):
        company = MockCompany()
        register_defaults(company)
        schemas = get_tool_schemas()
        names = [s["function"]["name"] for s in schemas]
        assert "execute_code" in names
        assert len(names) == 1

    def test_execute_code_basic(self):
        register_defaults(None)
        result = execute_tool("execute_code", {"code": "print('hello')"})
        assert "hello" in result

    def test_execute_code_forbidden_module(self):
        register_defaults(None)
        result = execute_tool("execute_code", {"code": "import os\nprint(os.getcwd())"})
        assert "보안" in result or "오류" in result

    def test_execute_code_empty(self):
        register_defaults(None)
        result = execute_tool("execute_code", {"code": ""})
        assert "오류" in result
