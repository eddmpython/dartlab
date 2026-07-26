"""tests/audit/namingConsistency.py — 매개변수 표준 사전 검사 단위 테스트."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

_REPO = Path(__file__).resolve().parent.parent.parent
_SCRIPT = _REPO / "tests" / "audit" / "namingConsistency.py"


def _loadModule():
    """tests/audit/namingConsistency.py 를 모듈로 동적 로드.

    `sys.modules` 등록 필수 — @dataclass 가 cls.__module__ lookup 시 의존.
    """
    spec = importlib.util.spec_from_file_location("namingConsistencyMod", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_buildAliasIndexInverts():
    """`{stockIdentifier: {standard: stockCode, aliases: [code, ticker]}}` →
    `{code: (stockCode, stockIdentifier), ticker: (...)}`.
    """
    nc = _loadModule()
    aliases = {
        "stockIdentifier": {"standard": "stockCode", "aliases": ["code", "ticker"]},
        "limitInt": {"standard": "limit", "aliases": ["topK", "n"]},
    }
    idx = nc._buildAliasIndex(aliases)
    assert idx["code"] == ("stockCode", "stockIdentifier", ())
    assert idx["ticker"] == ("stockCode", "stockIdentifier", ())
    assert idx["topK"] == ("limit", "limitInt", ())


def test_scanFileDetectsAliasArg(tmp_path: Path):
    """함수 매개변수가 alias 사용 시 위반 검출."""
    nc = _loadModule()
    target = tmp_path / "sample.py"
    target.write_text(
        "def fetchPrice(code: str, topK: int = 10) -> None:\n    pass\n",
        encoding="utf-8",
    )
    aliasIndex = {
        "code": ("stockCode", "stockIdentifier", ()),
        "topK": ("limit", "limitInt", ()),
    }
    violations = nc._scanFile(target, aliasIndex)
    names = sorted([v.argName for v in violations])
    assert names == ["code", "topK"]


def test_scanFilePassesStandardName(tmp_path: Path):
    """표준 이름은 통과 — 위반 0."""
    nc = _loadModule()
    target = tmp_path / "sample.py"
    target.write_text(
        "def fetchPrice(stockCode: str, limit: int = 10) -> None:\n    pass\n",
        encoding="utf-8",
    )
    aliasIndex = {
        "code": ("stockCode", "stockIdentifier", ()),
        "topK": ("limit", "limitInt", ()),
    }
    assert nc._scanFile(target, aliasIndex) == []


def test_loadAliasesReturnsPopulatedDict():
    """aliases.json (P5 1.0.0) 은 10 표준 의미 채워진 사전.

    P4.1 (2026-05-11) 에서 'code' / 'corpCode' alias 는 의미 충돌로 분리됨
    ('code' = Python source code / OAuth code · 'corpCode' = DART API 8자리).
    'codeOrName' 은 유지 — 명시적 종목코드/회사명 통합 의도.
    """
    nc = _loadModule()
    aliases = nc._loadAliases()
    assert "stockIdentifier" in aliases
    assert aliases["stockIdentifier"]["standard"] == "stockCode"
    assert "codeOrName" in aliases["stockIdentifier"]["aliases"]


def test_scopeExcludeTurnsOneRuleOffForOnePath(tmp_path: Path):
    """규칙별 경로 예외는 그 규칙만, 그 경로에서만 끈다.

    한 단어가 어떤 엔진에서는 직렬화 키로 굳어 있어 이름을 바꾸면 계약 해시가 함께
    바뀌는 경우가 있다. 그때 규칙 전체를 지우면 다른 엔진의 보호까지 사라진다.
    """

    nc = _loadModule()
    aliases = {
        "freqLabel": {
            "standard": "freq",
            "aliases": ["frequency"],
            "scopeExclude": ["src/dartlab/simulate/"],
        }
    }
    index = nc._buildAliasIndex(aliases)
    assert index["frequency"] == ("freq", "freqLabel", ("src/dartlab/simulate/",))

    body = "def build(frequency: str) -> None:\n    pass\n"
    excluded = tmp_path / "src" / "dartlab" / "simulate" / "sample.py"
    excluded.parent.mkdir(parents=True, exist_ok=True)
    excluded.write_text(body, encoding="utf-8")
    guarded = tmp_path / "src" / "dartlab" / "macro" / "sample.py"
    guarded.parent.mkdir(parents=True, exist_ok=True)
    guarded.write_text(body, encoding="utf-8")

    # 프로젝트 밖 경로는 절대경로로 떨어지므로 접두 비교가 성립하도록 상대 규칙을 맞춘다.
    relativeIndex = {"frequency": ("freq", "freqLabel", (excluded.parent.as_posix(),))}
    assert nc._scanFile(excluded, relativeIndex) == []
    assert [v.argName for v in nc._scanFile(guarded, relativeIndex)] == ["frequency"]


def test_baselineKeyIgnoresLineNumber():
    """키가 줄번호를 담으면 무관한 편집이 유령 위반을 만든다."""

    nc = _loadModule()
    first = nc.Violation(
        path="src/dartlab/x.py", line=10, funcName="build", argName="topK", standard="limit", meaning="limitInt"
    )
    moved = nc.Violation(
        path="src/dartlab/x.py", line=99, funcName="build", argName="topK", standard="limit", meaning="limitInt"
    )
    assert nc._baselineKey(first) == nc._baselineKey(moved)
