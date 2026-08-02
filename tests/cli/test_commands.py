"""CLI command smoke tests — 각 명령의 run() 최소 호출 검증.

모든 테스트는 unit 마커: 실제 데이터 로드 없음, mock/monkeypatch만 사용.
"""

from __future__ import annotations

import argparse
import types
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.unit


# ── helpers ──


def _ns(**kwargs) -> argparse.Namespace:
    """Shortcut for building argparse.Namespace."""
    return argparse.Namespace(**kwargs)


def _mock_company():
    """Company facade mock — 필요한 속성만 stub."""
    c = MagicMock()
    c.corpName = "테스트기업"
    c.stockCode = "999999"
    c.index = {"종목코드": "999999", "회사명": "테스트기업"}
    c.trace.return_value = None
    c.topics = ["BS", "IS"]
    c.panel.return_value = None  # 공개 show + docs 농장 은퇴 → panel 표면. 빈 회사 → rc 0.
    c.facts = None
    c.BS = None
    c.IS = None
    c.CF = None
    return c


def _patch_dartlab(monkeypatch, company=None):
    """configureDartlab()가 mock dartlab 모듈을 반환하도록 패치.

    Python 모듈 import 캐싱 때문에 source 모듈뿐 아니라
    각 command 모듈에 이미 바인딩된 참조도 함께 패치해야 한다.
    """
    fake_mod = types.ModuleType("dartlab")
    fake_mod.verbose = False  # type: ignore[attr-defined]
    co = company or _mock_company()
    fake_mod.Company = MagicMock(return_value=co)  # type: ignore[attr-defined]
    fake_mod.search = MagicMock(return_value=None)  # type: ignore[attr-defined]
    fake_mod.searchName = MagicMock(return_value=None)  # type: ignore[attr-defined]

    # status에서 dartlab.llm.status() 호출
    llm_mock = MagicMock()
    llm_mock.status.return_value = {"available": False, "model": "test"}
    fake_mod.llm = llm_mock  # type: ignore[attr-defined]

    factory = lambda: fake_mod  # noqa: E731

    # source 모듈 패치
    monkeypatch.setattr(
        "dartlab.cli.services.runtime.configureDartlab",
        factory,
    )

    # 이미 import된 command 모듈의 바인딩도 패치 (full suite 순서 의존성 해소)
    _CMD_MODULES = [
        "dartlab.cli.commands.ask",
        "dartlab.cli.commands.excel",
        "dartlab.cli.commands.profile",
        "dartlab.cli.commands.report",
        "dartlab.cli.commands.search",
        "dartlab.cli.commands.sections",
        "dartlab.cli.commands.show",
        "dartlab.cli.commands.statement",
    ]
    import sys

    for mod_path in _CMD_MODULES:
        if mod_path in sys.modules:
            monkeypatch.setattr(f"{mod_path}.configureDartlab", factory)

    return fake_mod


@pytest.fixture()
def mock_output(monkeypatch):
    """dartlab.cli.services.output의 getConsole/printDataframe을 mock."""
    console = MagicMock()
    monkeypatch.setattr("dartlab.cli.services.output.getConsole", lambda: console)
    monkeypatch.setattr("dartlab.cli.services.output.printDataframe", lambda *a, **kw: None)
    return console


# ── 1. search ──


def test_search_no_result(monkeypatch, mock_output):
    _patch_dartlab(monkeypatch)
    from dartlab.cli.commands.search import run

    rc = run(_ns(keyword="없는종목"))
    assert rc == 0


# ── 2. status ──


def test_status_runs(monkeypatch):
    import dartlab.cli.commands.status as status_command

    engine = MagicMock()
    engine.status.return_value = {
        "runtimes": [
            {
                "runtimeId": "codex",
                "state": "ready",
                "version": "codex-cli test",
                "mcp": {"connected": True},
            }
        ]
    }
    monkeypatch.setattr(status_command, "getRuntimeEngine", lambda: engine)

    rc = status_command.run(_ns(runtime=None, refresh=False))
    assert rc == 0
    engine.status.assert_called_once_with(refresh=False)


# ── 3. modules ──


def test_modules_list():
    from dartlab.cli.commands.modules import _run

    _run(_ns(category=None, search=None))


# ── 4. setup (help 수준) ──


def test_setup_no_provider(capsys):
    from dartlab.cli.commands.setup import run

    rc = run(_ns(target=None))
    assert rc == 0
    out = capsys.readouterr().out
    assert "데이터 수집" in out or "AI 분석" in out or "dart-key" in out


# ── 5. show (topic=None → index) ──


def test_show_index(monkeypatch, mock_output):
    _patch_dartlab(monkeypatch)
    from dartlab.cli.commands.show import run

    rc = run(_ns(company="999999", topic=None, trace=None, period=None, block=None, raw=False))
    assert rc == 0


# ── 6. show (topic 지정, None 반환) ──


def test_show_topic_none(monkeypatch, mock_output):
    _patch_dartlab(monkeypatch)
    from dartlab.cli.commands.show import run

    rc = run(_ns(company="999999", topic="BS", trace=None, period=None, block=None, raw=False))
    assert rc == 0


# ── 7. statement ──


def test_statement_bs(monkeypatch, mock_output):
    _patch_dartlab(monkeypatch)
    from dartlab.cli.commands.statement import run

    rc = run(_ns(company="999999", name="BS"))
    assert rc == 0


# ── 8. profile ──


def test_profile_basic(monkeypatch, mock_output):
    _patch_dartlab(monkeypatch)
    from dartlab.cli.commands.profile import run

    rc = run(_ns(company="999999", facts=False))
    assert rc == 0


# ── 9. sections ──


def test_sections_basic(monkeypatch, mock_output):
    _patch_dartlab(monkeypatch)
    from dartlab.cli.commands.sections import run

    rc = run(_ns(company="999999", raw=False))
    assert rc == 0


# ── 10. excel ──


def test_excel_export(monkeypatch, mock_output):
    _patch_dartlab(monkeypatch)
    monkeypatch.setattr(
        "dartlab.viz.export.excel.exportToExcel",
        lambda *a, **kw: "/tmp/test.xlsx",
    )
    from dartlab.cli.commands.excel import run

    rc = run(_ns(company="999999", output=None, modules=None))
    assert rc == 0


# ── 11. collect (stats 모드) ──


def test_collect_stats():
    from dartlab.cli.commands.collect import run

    with patch("dartlab.cli.commands.collect._runStats", return_value=0) as mock_stats:
        rc = run(_ns(stats=True, uncollected=False, auto=False, codes=None, limit=None))
    assert rc == 0
    mock_stats.assert_called_once()


# ── 12. plugin list ──


def test_plugin_list():
    from dartlab.cli.commands.plugin import run

    with patch("dartlab.cli.commands.plugin._listPlugins", return_value=0) as mock_list:
        rc = run(_ns(plugin_command="list"))
    assert rc == 0
    mock_list.assert_called_once()


# ── 13. ai (빌드 체크만) ──


def test_ai_no_build():
    from dartlab.cli.commands.ai import run

    with patch("dartlab.cli.commands.ai._checkBuiltUi", return_value=False):
        rc = run(_ns(port=8000, host="127.0.0.1", dev=False))
    assert rc == 0


def test_ai_dev_selects_platform_npm_shim():
    from dartlab.cli.commands.ai import _npmCommand

    assert _npmCommand(platform="nt") == "npm.cmd"
    assert _npmCommand(platform="posix") == "npm"


def test_ai_dev_finds_npm_workspace_root(tmp_path):
    import json

    from dartlab.cli.commands.ai import _npmWorkspaceRoot

    app = tmp_path / "ui" / "apps" / "local"
    app.mkdir(parents=True)
    (tmp_path / "package.json").write_text(json.dumps({"workspaces": ["ui/apps/*"]}), encoding="utf-8")
    (app / "package.json").write_text(json.dumps({"name": "local"}), encoding="utf-8")

    assert _npmWorkspaceRoot(app) == tmp_path


# ── 14. share (reset 모드) ──


def test_share_reset(tmp_path):
    # share.py는 channel 엔진 작업 중 deprecated/제거됨 → 미존재 시 skip
    pytest.importorskip("dartlab.cli.commands.share")
    from dartlab.cli.commands.share import run

    with patch("dartlab.cli.commands.share._load_config", return_value={}):
        with patch("dartlab.cli.commands.share._SHARE_CONFIG_PATH", tmp_path / "nonexist.json"):
            rc = run(_ns(reset=True, port=None, stop=False))
    assert rc == 0


# ── 15. mcp (import 검증) ──


def test_mcp_import():
    from dartlab.cli.commands import mcp

    assert hasattr(mcp, "_run")


# ── 16. report ──


class _ContractCompany:
    """공개 계약(`panel` · `analysis`) 만 구현한 Company 대역."""

    corpName = "테스트기업"
    stockCode = "999999"

    def panel(self, axis):
        import polars as pl

        if axis == "회사의 개요":
            return pl.DataFrame({"sectionLeaf": ["개요"], "2025Q4": ["<P>" + "테스트 본문 " * 12 + "</P>"]})
        if axis in ("BS", "IS", "CF"):
            return pl.DataFrame({"snakeId": ["total_assets"], "항목": ["자산총계"], "2025Q4": [1000.0]})
        return None

    def analysis(self, engine, axis):
        if axis == "종합평가":
            return {"scorecard": {"items": [{"area": "수익성", "grade": "A"}]}}
        return {"trend": {"history": [{"period": "2024", "roe": 5.0}, {"period": "2025", "roe": 7.0}]}}


def test_buildReport_fillsEverySection():
    """보고서 네 절이 전부 본문을 갖는다.

    예전에는 `company.BS` · `company.ratios` · `company.insights` 처럼 계약에서 빠진 이름을
    불렀고 그 실패를 넓은 except 가 삼켜서, 절 제목만 남고 본문이 통째로 비었다. 기존
    테스트가 `_buildReport` 를 통째로 patch 해 버려서 그 사실이 안 잡혔다.
    """
    from dartlab.cli.commands.report import _buildReport

    report = _buildReport(_ContractCompany(), "테스트기업", "999999", None)

    assert "데이터가 없습니다" not in report, f"빈 절이 있다:\n{report}"
    for header in ("## 기업 개요", "## 재무제표", "## 재무비율", "## 인사이트 등급"):
        assert header in report
    assert "자산총계" in report, "재무제표 본문 없음"
    assert "| 수익성 | A |" in report, "인사이트 등급 표 없음"


def test_buildReport_ratioLinesPickLatestPeriod():
    """지표 줄은 시점 최대값을 고른다 (목록 마지막이 최신이라는 보장이 없다)."""
    from dartlab.cli.commands.report import _buildReport

    report = _buildReport(_ContractCompany(), "테스트기업", "999999", {"ratios"})

    assert "(2025)" in report and "(2024)" not in report


def test_report_stdout(monkeypatch, capsys):
    _patch_dartlab(monkeypatch)
    with patch("dartlab.cli.commands.report._buildReport", return_value="# Report\n"):
        from dartlab.cli.commands.report import run

        rc = run(_ns(company="999999", sections=None, output=None))
    assert rc == 0
    assert "Report" in capsys.readouterr().out


def test_report_model_flag_emits_contract(monkeypatch, capsys):
    """--model 은 공개 계약 Company.reportModel 결과를 JSON 으로 낸다."""
    co = _mock_company()
    co.reportModel = MagicMock(return_value={"stockCode": "999999", "schemaVersion": 2, "sections": []})
    _patch_dartlab(monkeypatch, company=co)
    from dartlab.cli.commands.report import run

    rc = run(_ns(company="999999", sections=None, output=None, model=True, perspective="credit"))
    assert rc == 0
    out = capsys.readouterr().out
    assert '"schemaVersion": 2' in out and '"stockCode": "999999"' in out
    co.reportModel.assert_called_once_with("credit")


def test_report_markdown_unchanged_without_model_flag(monkeypatch, capsys):
    """--model 미지정(구 namespace 포함) 이면 기존 Markdown 경로 그대로 (추가형·회귀 0)."""
    co = _mock_company()
    co.reportModel = MagicMock()
    _patch_dartlab(monkeypatch, company=co)
    with patch("dartlab.cli.commands.report._buildReport", return_value="# MD\n"):
        from dartlab.cli.commands.report import run

        rc = run(_ns(company="999999", sections=None, output=None))
    assert rc == 0
    assert "MD" in capsys.readouterr().out
    co.reportModel.assert_not_called()


# ── 17. statement / status: 계약 호출로 실제 값을 내는가 ──


def test_statement_usesPanelContract(monkeypatch, capsys):
    """재무제표 명령이 `panel` 계약으로 표를 낸다.

    예전에는 `company.BS` 처럼 속성으로 읽었다. 그 이름들은 계약에서 빠져 존재하지
    않으므로 AttributeError 로 죽었고, 제목 두 줄만 찍히고 표가 안 나왔다.
    """
    import polars as pl

    co = _mock_company()
    frame = pl.DataFrame({"snakeId": ["sales"], "항목": ["매출액"], "2025Q4": [100.0]})
    co.panel = MagicMock(return_value=frame)
    _patch_dartlab(monkeypatch, company=co)
    from dartlab.cli.commands.statement import run

    rc = run(_ns(company="999999", name="IS", periods=6))

    assert rc == 0
    co.panel.assert_called_once_with("IS")
    assert "매출액" in capsys.readouterr().out


def test_runtimeStatus_filtersSelectedRuntime(monkeypatch, capsys):
    """status는 direct provider 대신 선택한 설치형 runtime만 표시한다."""
    import dartlab.cli.commands.status as status_command

    engine = MagicMock()
    engine.status.return_value = {
        "runtimes": [
            {"runtimeId": "codex", "state": "ready", "version": "0.1", "mcp": {"connected": True}},
            {"runtimeId": "cline", "state": "missing", "version": None, "mcp": {"connected": False}},
        ]
    }
    monkeypatch.setattr(status_command, "getRuntimeEngine", lambda: engine)

    assert status_command.run(_ns(runtime="cline", refresh=True)) == 0
    output = capsys.readouterr().out
    assert "cline" in output
    assert "codex" not in output
