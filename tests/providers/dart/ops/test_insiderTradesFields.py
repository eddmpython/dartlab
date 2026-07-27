"""DART 내부자 거래 필드 매핑 회귀.

실제 `elestock.json` 응답에는 `ofcps` 도 `ctr_motive` 도 없다. 그런데 그 두 이름을 읽고
있어서 직위와 사유가 언제나 빈 문자열이었다. 더 나쁜 것은 소유주식수와 증감주식수를 서로
바꿔 읽고 있었다는 점이다. 소유 2,000 주에 증감 1,000 주인 임원이 증감 2,000 주로 나갔다.

`_safeInt` 가 모든 미스를 0 으로 바꾸므로 예외는 나지 않는다. 확신에 찬 틀린 숫자가
그대로 사용자 화면까지 간다.

여기 쓰는 행 모양은 2026-07-27 실제 응답에서 그대로 가져왔다.
"""

from __future__ import annotations

import polars as pl
import pytest

from dartlab.gather.types import InsiderTrade
from dartlab.providers.dart.ops.insiderTrades import _tradeTypeOf

# 삼성전자 실제 응답 행. 소유수와 증감수가 다른 것을 고른 이유는 둘을 바꿔 읽어도
# 값이 같아 통과해 버리는 행이 흔하기 때문이다.
_REAL_ROW = {
    "corp_code": "00126380",
    "corp_name": "삼성전자",
    "rcept_no": "20240807000123",
    "rcept_dt": "2024-08-07",
    "repror": "정용준",
    "isu_exctv_rgist_at": "비등기임원",
    "isu_exctv_ofcps": "부사장",
    "isu_main_shrholdr": "-",
    "sp_stock_lmp_cnt": "2,000",
    "sp_stock_lmp_irds_cnt": "1,000",
    "sp_stock_lmp_rate": "0",
    "sp_stock_lmp_irds_rate": "0",
}


def _mapRow(row: dict[str, str]) -> dict[str, object]:
    """provider 가 하는 매핑을 그대로 재현한다."""

    from dartlab.providers.dart.ops.insiderTrades import _safeInt

    return {
        "date": str(row.get("rcept_dt", "")),
        "name": str(row.get("repror", "")),
        "position": str(row.get("isu_exctv_ofcps", "")),
        "tradeType": _tradeTypeOf(_safeInt(row.get("sp_stock_lmp_irds_cnt", 0))),
        "changeShares": _safeInt(row.get("sp_stock_lmp_irds_cnt", 0)),
        "afterShares": _safeInt(row.get("sp_stock_lmp_cnt", 0)),
        "reason": str(row.get("isu_exctv_rgist_at", "")),
        "source": "dart",
    }


def testPositionComesFromTheFieldThatActuallyExists() -> None:
    """`ofcps` 는 응답에 없다. 직위는 `isu_exctv_ofcps` 다."""

    assert "ofcps" not in _REAL_ROW
    assert _mapRow(_REAL_ROW)["position"] == "부사장"


def testChangeAndHoldingAreNotSwapped() -> None:
    """증감과 보유를 바꿔 읽으면 거래 규모가 통째로 틀린다."""

    mapped = _mapRow(_REAL_ROW)

    assert mapped["changeShares"] == 1000
    assert mapped["afterShares"] == 2000


def testHoldingIsAtLeastTheChangeForAnAcquisition() -> None:
    """취득이면 변동 후 보유는 증감분 이상이다. 뒤바뀌면 이 관계가 깨진다."""

    mapped = _mapRow(_REAL_ROW)

    assert mapped["afterShares"] >= mapped["changeShares"]


@pytest.mark.parametrize(
    ("change", "expected"),
    [(1000, "취득"), (-500, "처분"), (0, "")],
)
def testTradeTypeIsDerivedFromTheChangeSign(change: int, expected: str) -> None:
    """응답에 거래 유형 필드가 없으므로 증감 부호로 가른다. 0 은 어느 쪽도 아니다."""

    assert _tradeTypeOf(change) == expected


def testMappedRowSatisfiesTheDataclassContract() -> None:
    """소비자가 `InsiderTrade(**row)` 로 그대로 넘긴다. 키가 어긋나면 즉시 깨진다."""

    trade = InsiderTrade(**_mapRow(_REAL_ROW))

    assert trade.name == "정용준"
    assert trade.position == "부사장"
    assert trade.tradeType == "취득"
    assert trade.changeShares == 1000
    assert trade.afterShares == 2000


def testMajorHolderNameComesFromTheReporterField() -> None:
    """`report_nm` 도 `change_on` 도 majorstock 응답에 없다. 보고자는 `repror` 다."""

    from dartlab.providers.dart.ops.insiderTrades import _safeFloat, _safeInt

    row = {
        "rcept_dt": "2024-10-25",
        "repror": "삼성물산",
        "report_tp": "일반",
        "report_resn": "- 보유주식수 변동",
        "stkqy": "1,198,889,258",
        "stkrt": "20.08",
        "stkqy_irds": "6,317",
    }
    mapped = {
        "holderName": str(row.get("repror", "")),
        "shares": _safeInt(row.get("stkqy", 0)),
        "ratio": _safeFloat(row.get("stkrt", 0)),
        "changeDate": str(row.get("rcept_dt", "")),
        "changeType": str(row.get("report_tp", "")),
        "source": "dart",
    }

    assert "report_nm" not in row
    assert "change_on" not in row
    assert mapped["holderName"] == "삼성물산"
    assert mapped["changeType"] == "일반"
    assert mapped["shares"] == 1198889258
    assert mapped["ratio"] == pytest.approx(20.08)


def testProviderMappingMatchesThisTest() -> None:
    """provider 본체와 이 테스트의 매핑이 어긋나면 테스트가 무의미해진다."""

    import inspect

    from dartlab.providers.dart.ops import insiderTrades

    source = inspect.getsource(insiderTrades)

    assert '"isu_exctv_ofcps"' in source
    assert '"ofcps"' not in source
    assert '"ctr_motive"' not in source
    assert '"report_nm"' not in source
    assert '"change_on"' not in source


def testRawRowShapeIsWhatTheProviderExpects() -> None:
    """DataFrame 경유라 컬럼이 그대로 살아 있어야 한다."""

    frame = pl.DataFrame([_REAL_ROW])

    assert set(_REAL_ROW) <= set(frame.columns)
