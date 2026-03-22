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
    c.show.return_value = None
    c.trace.return_value = None
    c.topics = ["BS", "IS"]
    c.docs.sections = None
    c.profile.facts = None
    c.BS = None
    c.IS = None
    c.CF = None
    return c


def _patch_dartlab(monkeypatch, company=None):
    """configure_dartlab()가 mock dartlab 모듈을 반환하도록 패치.

    Python 모듈 import 캐싱 때문에 source 모듈뿐 아니라
    각 command 모듈에 이미 바인딩된 참조도 함께 패치해야 한다.
    """
    fake_mod = types.ModuleType("dartlab")
    fake_mod.verbose = False  # type: ignore[attr-defined]
    co = company or _mock_company()
    fake_mod.Company = MagicMock(return_value=co)  # type: ignore[attr-defined]
    fake_mod.search = MagicMock(return_value=None)  # type: ignore[attr-defined]

    # status에서 dartlab.llm.status() 호출
    llm_mock = MagicMock()
    llm_mock.status.return_value = {"available": False, "model": "test"}
    fake_mod.llm = llm_mock  # type: ignore[attr-defined]

    factory = lambda: fake_mod  # noqa: E731

    # source 모듈 패치
    monkeypatch.setattr(
        "dartlab.cli.services.runtime.configure_dartlab",
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
        "dartlab.cli.commands.status",
    ]
    import sys

    for mod_path in _CMD_MODULES:
        if mod_path in sys.modules:
            monkeypatch.setattr(f"{mod_path}.configure_dartlab", factory)

    return fake_mod


@pytest.fixture()
def mock_output(monkeypatch):
    """dartlab.cli.services.output의 get_console/print_dataframe을 mock."""
    console = MagicMock()
    monkeypatch.setattr("dartlab.cli.services.output.get_console", lambda: console)
    monkeypatch.setattr("dartlab.cli.services.output.print_dataframe", lambda *a, **kw: None)
    return console


# ── 1. search ──


def test_search_no_result(monkeypatch, mock_output):
    _patch_dartlab(monkeypatch)
    from dartlab.cli.commands.search import run

    rc = run(_ns(keyword="없는종목"))
    assert rc == 0


# ── 2. status ──


def test_status_runs(monkeypatch):
    _patch_dartlab(monkeypatch)
    from dartlab.cli.commands.status import run

    rc = run(_ns(provider="openai", cost=False))
    assert rc == 0


# ── 3. modules ──


def test_modules_list():
    from dartlab.cli.commands.modules import _run

    _run(_ns(category=None, search=None))


# ── 4. setup (help 수준) ──


def test_setup_no_provider(capsys):
    from dartlab.cli.commands.setup import run

    rc = run(_ns(provider=None))
    assert rc == 0
    out = capsys.readouterr().out
    assert "provider" in out.lower() or "Provider" in out or "사용 가능" in out


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

    rc = run(_ns(company="999999"))
    assert rc == 0


# ── 10. excel ──


def test_excel_export(monkeypatch, mock_output):
    _patch_dartlab(monkeypatch)
    monkeypatch.setattr(
        "dartlab.export.excel.exportToExcel",
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

    with patch("dartlab.cli.commands.plugin._list_plugins", return_value=0) as mock_list:
        rc = run(_ns(plugin_command="list"))
    assert rc == 0
    mock_list.assert_called_once()


# ── 13. ai (빌드 체크만) ──


def test_ai_no_build():
    from dartlab.cli.commands.ai import run

    with patch("dartlab.cli.commands.ai._check_built_ui", return_value=False):
        rc = run(_ns(port=8000, host="127.0.0.1", dev=False))
    assert rc == 0


# ── 14. share (reset 모드) ──


def test_share_reset(tmp_path):
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


def test_report_stdout(monkeypatch, capsys):
    _patch_dartlab(monkeypatch)
    with patch("dartlab.cli.commands.report._build_report", return_value="# Report\n"):
        from dartlab.cli.commands.report import run

        rc = run(_ns(company="999999", sections=None, output=None))
    assert rc == 0
    assert "Report" in capsys.readouterr().out
