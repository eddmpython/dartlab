"""buildEdgarAllFilingsRecent._accumulate 계약. HF baseline merge 누적·dedup.

US 수시공시는 submissions recent 블록만 재빌드하면 활성기업 옛 공시가 밀려 사라진다(슬라이딩).
_accumulate 가 기존 HF baseline 과 merge·dedup 해 전 이력을 보존(trim 없음)하는지 검증. KR 동형.
스크립트라 importlib 경유. 합성 프레임, 네트워크/HF 무관.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import polars as pl
import pytest

pytestmark = pytest.mark.unit

_SCRIPT = Path(__file__).resolve().parents[3] / ".github" / "scripts" / "sync" / "buildEdgarAllFilingsRecent.py"


def _load():
    """buildEdgarAllFilingsRecent 모듈 로드(스크립트라 importlib 경유)."""
    spec = importlib.util.spec_from_file_location("buildEdgarAllFilingsRecentForTest", _SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _frame(rows: list[dict]) -> pl.DataFrame:
    cols = ["stockCode", "entityName", "filingDate", "form", "accessionNo", "docDescription", "url"]
    return pl.DataFrame([{c: r.get(c, "") for c in cols} for r in rows], schema={c: pl.Utf8 for c in cols})


def test_accumulate_preserves_baseline_history():
    """baseline 의 과거 공시가 신규분과 merge 되어 보존(슬라이딩 방지) + accessionNo dedup."""
    mod = _load()
    fresh = _frame(
        [
            {"stockCode": "AAPL", "filingDate": "20260626", "accessionNo": "A-2026"},
            {"stockCode": "AAPL", "filingDate": "20250101", "accessionNo": "A-2025"},  # baseline 과 중복
        ]
    )
    base = _frame(
        [
            {"stockCode": "AAPL", "filingDate": "20250101", "accessionNo": "A-2025"},  # 중복은 1개로 dedup
            {"stockCode": "AAPL", "filingDate": "20230103", "accessionNo": "A-2023"},  # 과거 dot, 신규엔 없음
        ]
    )
    out = mod._accumulate(fresh, base)
    accs = set(out["accessionNo"].to_list())
    assert accs == {"A-2026", "A-2025", "A-2023"}  # 과거(A-2023) 보존 + dedup
    assert out.height == 3  # 중복 A-2025 는 1개


def test_accumulate_none_base_is_fresh_only():
    """baseline 부재(최초 빌드)면 신규분만."""
    mod = _load()
    fresh = _frame([{"stockCode": "MSFT", "filingDate": "20260101", "accessionNo": "M-1"}])
    out = mod._accumulate(fresh, None)
    assert out["accessionNo"].to_list() == ["M-1"]
