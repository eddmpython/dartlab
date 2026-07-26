from __future__ import annotations

import polars as pl


def testCalcEarningsAcceptsConsolidatedCisRows(monkeypatch) -> None:
    from dartlab.quant.signal import earningsMomentum

    frame = pl.DataFrame(
        {
            "stockCode": ["005930", "005930", "005930"],
            "bsns_year": ["2022", "2023", "2024"],
            "sj_div": ["CIS", "CIS", "CIS"],
            "account_nm": ["영업이익", "영업이익", "영업이익"],
            "thstrm_amount": ["100", "120", "180"],
        }
    )
    monkeypatch.setattr(earningsMomentum, "loadScanParquet", lambda name, market: frame.lazy())
    monkeypatch.setattr(earningsMomentum, "extractAnnualConsolidated", lambda value: value)
    monkeypatch.setattr(earningsMomentum, "isEdgarSchema", lambda value: False)

    result = earningsMomentum.calcEarnings("005930", market="KR")

    assert result["years"] == ["2022", "2023", "2024"]
    assert result["latestOpIncome"] == 180.0
    assert "error" not in result
