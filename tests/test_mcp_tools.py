"""MCP 도구 정의 + 실행 로직 단위 테스트.

기존 test_mcp.py와 겹치지 않는 영역 — _executeTool mock, 캐싱, installMcpConfig, _fmtDict.
데이터 로드 없음, mock 전용.
"""

from __future__ import annotations

import json
import time
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.unit


# ── _TOOLS 구조 검증 ──


def test_all_tools_have_required_params_subset():
    """required 목록의 모든 항목이 params에 존재해야 한다."""
    from dartlab.mcp import _TOOLS

    for tool in _TOOLS:
        for req in tool["required"]:
            assert req in tool["params"], f"Tool '{tool['name']}': required param '{req}' not in params"


def test_all_tool_names_unique():
    from dartlab.mcp import _TOOLS

    names = [t["name"] for t in _TOOLS]
    assert len(names) == len(set(names))


def test_tool_feature_map_covers_all_tools():
    """_TOOL_FEATURE_MAP이 모든 도구를 커버한다."""
    from dartlab.mcp import _TOOL_FEATURE_MAP, _TOOLS

    tool_names = {t["name"] for t in _TOOLS}
    mapped_names = set(_TOOL_FEATURE_MAP.keys())
    assert tool_names == mapped_names, f"Missing in feature map: {tool_names - mapped_names}"


def test_tool_descriptions_nonempty():
    from dartlab.mcp import _TOOLS

    for tool in _TOOLS:
        assert len(tool["description"]) > 10, f"Tool '{tool['name']}' has too short description"


def test_stock_param_type():
    """stockCode 파라미터는 항상 type=string이다."""
    from dartlab.mcp import _TOOLS

    for tool in _TOOLS:
        if "stockCode" in tool["params"]:
            assert tool["params"]["stockCode"]["type"] == "string"


# ── _fmtDict ──


def test_fmt_dict_nested():
    from dartlab.mcp import _fmtDict

    result = _fmtDict({"level1": {"level2": "value"}})
    assert "level1" in result
    assert "level2" in result
    assert "value" in result


def test_fmt_dict_skips_none():
    from dartlab.mcp import _fmtDict

    result = _fmtDict({"visible": "yes", "hidden": None})
    assert "visible" in result
    assert "hidden" not in result


def test_fmt_dict_list_of_strings():
    from dartlab.mcp import _fmtDict

    result = _fmtDict({"items": ["a", "b", "c"]})
    assert "- a" in result
    assert "- b" in result


def test_fmt_dict_list_of_dicts():
    from dartlab.mcp import _fmtDict

    result = _fmtDict({"items": [{"key": "val"}]})
    assert "key" in result


def test_fmt_dict_numeric():
    from dartlab.mcp import _fmtDict

    result = _fmtDict({"ratio": 0.123, "count": 42})
    assert "0.123" in result
    assert "42" in result


# ── _fmt truncation ──


def test_fmt_truncates_long_string():
    from dartlab.mcp import _MCP_MAX_RESULT_CHARS, _fmt

    long_text = "x" * (_MCP_MAX_RESULT_CHARS + 1000)
    result = _fmt(long_text)
    assert len(result) < len(long_text)
    assert "결과 잘림" in result


def test_fmt_does_not_truncate_short_string():
    from dartlab.mcp import _fmt

    short = "hello"
    assert _fmt(short) == short


# ── _getCompany caching ──


def test_get_company_caches():
    """동일 종목코드에 대해 캐시된 인스턴스를 반환한다."""
    from dartlab.mcp import _cache, _getCompany

    _cache.clear()
    mock_company = MagicMock()

    with patch("dartlab.Company", return_value=mock_company) as mock_ctor:
        result1 = _getCompany("TEST01")
        result2 = _getCompany("TEST01")

    assert result1 is result2
    mock_ctor.assert_called_once()
    _cache.clear()


def test_get_company_evicts_oldest():
    """캐시가 _CACHE_MAX에 도달하면 가장 오래된 항목을 제거한다."""
    from dartlab.mcp import _CACHE_MAX, _cache, _getCompany

    _cache.clear()

    with patch("dartlab.Company", side_effect=lambda code: MagicMock(name=code)):
        for i in range(_CACHE_MAX + 1):
            _getCompany(f"CODE{i:02d}")

    assert len(_cache) == _CACHE_MAX
    _cache.clear()


def test_get_company_expires_cache():
    """TTL 만료 시 새 인스턴스를 생성한다."""
    from dartlab.mcp import _CACHE_TTL, _cache, _getCompany

    _cache.clear()
    mock1 = MagicMock(name="old")
    mock2 = MagicMock(name="new")

    # Insert expired entry
    _cache["EXPTEST"] = (mock1, time.monotonic() - _CACHE_TTL - 10)

    with patch("dartlab.Company", return_value=mock2):
        result = _getCompany("EXPTEST")

    assert result is mock2
    _cache.clear()


# ── _executeTool with mock ──


def test_execute_tool_unknown():
    from dartlab.mcp import _executeTool

    result = _executeTool("nonExistentTool", {})
    assert "Unknown tool" in result


def test_execute_tool_search_company():
    from dartlab.mcp import _executeTool

    mock_result = MagicMock()
    mock_result.__str__ = lambda self: "삼성전자 005930"

    with patch("dartlab.searchName", return_value=mock_result):
        result = _executeTool("searchCompany", {"query": "삼성"})

    assert "삼성" in result or result is not None


def test_execute_tool_company_insights():
    from dartlab.mcp import _cache, _executeTool

    _cache.clear()
    mock_company = MagicMock()
    mock_company.insights.__str__ = lambda self: "등급: A"

    with patch("dartlab.Company", return_value=mock_company):
        result = _executeTool("companyInsights", {"stockCode": "005930"})

    assert isinstance(result, str)
    _cache.clear()


def test_execute_tool_company_financials():
    from dartlab.mcp import _cache, _executeTool

    _cache.clear()
    mock_company = MagicMock()
    mock_company.IS = "IS data"

    with patch("dartlab.Company", return_value=mock_company):
        result = _executeTool("companyFinancials", {"stockCode": "005930", "statement": "IS"})

    assert isinstance(result, str)
    _cache.clear()


def test_execute_tool_market_scan():
    from dartlab.mcp import _executeTool

    mock_scan_result = "governance results"
    with patch("dartlab.scan", return_value=mock_scan_result):
        result = _executeTool("marketScan", {"axis": "governance"})

    assert "governance" in result


def test_execute_tool_error_handling():
    """도구 실행 중 에러가 발생하면 에러 메시지를 반환한다."""
    from dartlab.mcp import _cache, _executeTool

    _cache.clear()

    with patch("dartlab.Company", side_effect=ValueError("데이터 없음")):
        result = _executeTool("companyInsights", {"stockCode": "BAD"})

    assert "Error" in result
    _cache.clear()


def test_execute_tool_company_analysis_with_axis():
    from dartlab.mcp import _cache, _executeTool

    _cache.clear()
    mock_company = MagicMock()
    mock_company.analysis.return_value = {"key": "value"}

    with patch("dartlab.Company", return_value=mock_company):
        result = _executeTool("companyAnalysis", {"stockCode": "005930", "axis": "financial", "sub": "수익성"})

    mock_company.analysis.assert_called_once_with("financial", "수익성")
    _cache.clear()


def test_execute_tool_company_analysis_axis_only():
    from dartlab.mcp import _cache, _executeTool

    _cache.clear()
    mock_company = MagicMock()
    mock_company.analysis.return_value = "guide"

    with patch("dartlab.Company", return_value=mock_company):
        result = _executeTool("companyAnalysis", {"stockCode": "005930", "axis": "financial"})

    mock_company.analysis.assert_called_once_with("financial")
    _cache.clear()


def test_execute_tool_company_analysis_no_axis():
    from dartlab.mcp import _cache, _executeTool

    _cache.clear()
    mock_company = MagicMock()
    mock_company.analysis.return_value = "全体 가이드"

    with patch("dartlab.Company", return_value=mock_company):
        result = _executeTool("companyAnalysis", {"stockCode": "005930"})

    mock_company.analysis.assert_called_once_with()
    _cache.clear()


def test_execute_tool_company_show():
    from dartlab.mcp import _cache, _executeTool

    _cache.clear()
    mock_company = MagicMock()
    mock_company.show.return_value = "사업개요 내용"

    with patch("dartlab.Company", return_value=mock_company):
        result = _executeTool("companyShow", {"stockCode": "005930", "topic": "businessOverview"})

    mock_company.show.assert_called_once_with("businessOverview")
    _cache.clear()


def test_execute_tool_company_diff_with_topic():
    from dartlab.mcp import _cache, _executeTool

    _cache.clear()
    mock_company = MagicMock()
    mock_company.diff.return_value = "변경사항"

    with patch("dartlab.Company", return_value=mock_company):
        result = _executeTool("companyDiff", {"stockCode": "005930", "topic": "revenue"})

    mock_company.diff.assert_called_once_with("revenue")
    _cache.clear()


def test_execute_tool_company_diff_no_topic():
    from dartlab.mcp import _cache, _executeTool

    _cache.clear()
    mock_company = MagicMock()
    mock_company.diff.return_value = "전체 변경"

    with patch("dartlab.Company", return_value=mock_company):
        result = _executeTool("companyDiff", {"stockCode": "005930"})

    mock_company.diff.assert_called_once()
    _cache.clear()


# ── installMcpConfig ──


def test_install_mcp_config_creates_file(tmp_path):
    from dartlab.mcp import installMcpConfig

    result = installMcpConfig(str(tmp_path))
    assert "생성 완료" in result

    mcp_file = tmp_path / ".mcp.json"
    assert mcp_file.exists()
    config = json.loads(mcp_file.read_text(encoding="utf-8"))
    assert "dartlab" in config["mcpServers"]
    assert config["mcpServers"]["dartlab"]["command"] == "uv"


def test_install_mcp_config_skips_if_exists(tmp_path):
    mcp_file = tmp_path / ".mcp.json"
    existing = {"mcpServers": {"dartlab": {"command": "existing"}}}
    mcp_file.write_text(json.dumps(existing), encoding="utf-8")

    from dartlab.mcp import installMcpConfig

    result = installMcpConfig(str(tmp_path))
    assert "이미 등록됨" in result

    # 기존 설정이 유지됨
    config = json.loads(mcp_file.read_text(encoding="utf-8"))
    assert config["mcpServers"]["dartlab"]["command"] == "existing"


def test_install_mcp_config_merges_with_existing(tmp_path):
    """기존 .mcp.json에 다른 서버가 있으면 dartlab만 추가한다."""
    mcp_file = tmp_path / ".mcp.json"
    existing = {"mcpServers": {"other": {"command": "other_cmd"}}}
    mcp_file.write_text(json.dumps(existing), encoding="utf-8")

    from dartlab.mcp import installMcpConfig

    result = installMcpConfig(str(tmp_path))
    assert "생성 완료" in result

    config = json.loads(mcp_file.read_text(encoding="utf-8"))
    assert "other" in config["mcpServers"]
    assert "dartlab" in config["mcpServers"]


# ── _MCP_INSTRUCTIONS ──


def test_mcp_instructions_contains_key_info():
    from dartlab.mcp import _MCP_INSTRUCTIONS

    assert "DART" in _MCP_INSTRUCTIONS
    assert "EDGAR" in _MCP_INSTRUCTIONS
    assert "companyInsights" in _MCP_INSTRUCTIONS
    assert "companyReview" in _MCP_INSTRUCTIONS


# ── companyReview tool execution ──


def test_execute_tool_company_review_full():
    from dartlab.mcp import _cache, _executeTool

    _cache.clear()
    mock_company = MagicMock()
    mock_review = MagicMock()
    mock_review.toMarkdown.return_value = "# 보고서"
    mock_company.review.return_value = mock_review

    with patch("dartlab.Company", return_value=mock_company):
        result = _executeTool("companyReview", {"stockCode": "005930"})

    assert result == "# 보고서"
    mock_company.review.assert_called_once_with()
    _cache.clear()


def test_execute_tool_company_review_section():
    from dartlab.mcp import _cache, _executeTool

    _cache.clear()
    mock_company = MagicMock()
    mock_review = MagicMock()
    mock_review.toMarkdown.return_value = "# 수익구조 보고서"
    mock_company.review.return_value = mock_review

    with patch("dartlab.Company", return_value=mock_company):
        result = _executeTool("companyReview", {"stockCode": "005930", "section": "수익구조"})

    mock_company.review.assert_called_once_with("수익구조")
    _cache.clear()
