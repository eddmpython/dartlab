"""pivot._pivotToSeries 의 ledger 옵트인 회귀 차단.

핵심 보증:
1. ENV OFF (기본) — ledger.append 호출 0, pivot 결과 정상.
2. ENV ON  — ledger.append 호출 발생, pivot 결과는 ENV OFF 와 동일.
3. mapper 가 None 반환 (nonstd fallback 진입) 시 ledgerKeys 가 누적된다.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import polars as pl
import pytest

from dartlab.providers.dart.finance import pivot as pivotMod
from dartlab.providers.dart.finance import pivotArrow as pivotArrowMod

pytestmark = pytest.mark.unit


def _fixtureFrame() -> pl.DataFrame:
    """미매핑 1 종 + 매핑 1 종이 섞인 작은 fixture."""
    return pl.DataFrame(
        {
            "sj_div": ["BS", "BS"],
            "account_id": ["-표준계정코드 미사용-", "ifrs-full_Assets"],
            "account_nm": ["기타의금융자산", "자산총계"],
            "_normalized_amount": [100.0, 5000.0],
            "bsns_year": ["2024", "2024"],
            "reprt_nm": ["1분기", "1분기"],
        }
    )


class _StubMapper:
    """`기타의금융자산` 만 매핑 실패, 그 외는 단순 정규화."""

    def map(self, accountId: str, accountNm: str) -> str | None:
        if accountNm == "기타의금융자산":
            return None
        return "total_assets"


@pytest.fixture(autouse=True)
def _clearLedgerEnv(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DARTLAB_MAPPING_LEDGER", raising=False)
    monkeypatch.delenv("DARTLAB_MAPPING_LEDGER_PATH", raising=False)


def test_env_off_no_ledger_call(monkeypatch: pytest.MonkeyPatch) -> None:
    df = _fixtureFrame()
    with (
        patch.object(pivotMod.AccountMapper, "get", return_value=_StubMapper()),
        patch.object(pivotMod.mappingLedger, "append") as appendMock,
    ):
        result = pivotMod._pivotToSeries(df, ["2024-Q1"], stockCode="005930")

    appendMock.assert_not_called()
    assert "nonstd_기타의금융자산" in result["BS"]
    assert result["BS"]["total_assets"][0] == 5000.0


def test_env_on_appends_ledger_with_stockcode(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    target = tmp_path / "raw.ndjson"
    monkeypatch.setenv("DARTLAB_MAPPING_LEDGER", "1")
    monkeypatch.setenv("DARTLAB_MAPPING_LEDGER_PATH", str(target))

    df = _fixtureFrame()
    with patch.object(pivotMod.AccountMapper, "get", return_value=_StubMapper()):
        pivotMod._pivotToSeries(df, ["2024-Q1"], stockCode="005930")

    assert target.exists()
    contents = target.read_text(encoding="utf-8").strip().splitlines()
    assert len(contents) == 1
    import json

    rec = json.loads(contents[0])
    assert rec["accountNm"] == "기타의금융자산"
    assert rec["stockCode"] == "005930"
    assert rec["sjDiv"] == "BS"
    assert rec["occurrenceCount"] == 1


def test_pivot_result_identical_with_and_without_ledger(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """ENV ON/OFF 결과 dict 동일성 — 회귀 차단 핵심."""
    df = _fixtureFrame()

    with patch.object(pivotMod.AccountMapper, "get", return_value=_StubMapper()):
        offResult = pivotMod._pivotToSeries(df, ["2024-Q1"], stockCode="005930")

    monkeypatch.setenv("DARTLAB_MAPPING_LEDGER", "1")
    monkeypatch.setenv("DARTLAB_MAPPING_LEDGER_PATH", str(tmp_path / "raw.ndjson"))
    with patch.object(pivotMod.AccountMapper, "get", return_value=_StubMapper()):
        onResult = pivotMod._pivotToSeries(df, ["2024-Q1"], stockCode="005930")

    assert offResult == onResult


def test_env_on_propagates_ledger_write_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """명시적으로 켠 관측 저장 실패를 데이터 성공으로 위장하지 않는다."""
    monkeypatch.setenv("DARTLAB_MAPPING_LEDGER", "1")
    frame = _fixtureFrame()

    with (
        patch.object(pivotMod.AccountMapper, "get", return_value=_StubMapper()),
        patch.object(pivotMod.mappingLedger, "append", side_effect=OSError("disk full")),
        pytest.raises(OSError, match="disk full"),
    ):
        pivotMod._pivotToSeries(frame, ["2024-Q1"], stockCode="005930")


def test_arrow_env_on_propagates_ledger_write_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Arrow 경로도 명시적으로 켠 관측 실패를 삼키지 않는다."""
    monkeypatch.setenv("DARTLAB_MAPPING_LEDGER", "1")
    attached = (pl.DataFrame(), {}, 0, [("", "미매핑계정", "BS", 1)])

    with (
        patch.object(pivotArrowMod, "_attachMappingColumns", return_value=attached),
        patch.object(pivotArrowMod, "_buildPeriodKeyColumn", return_value=pl.DataFrame()),
        patch.object(pivotArrowMod, "_runDuckdbPivot", return_value=pl.DataFrame()),
        patch.object(pivotArrowMod.mappingLedger, "append", side_effect=OSError("disk full")),
        pytest.raises(OSError, match="disk full"),
    ):
        pivotArrowMod.pivotToSeriesArrow(
            pl.DataFrame(),
            [],
            accountIdPriority=lambda _: 3,
            fallbackSnakeId=lambda _: None,
            ifrsTopLevelIds=frozenset(),
            stockCode="005930",
        )
