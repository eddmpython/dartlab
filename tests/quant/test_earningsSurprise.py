from __future__ import annotations

import polars as pl


def _dartFinance() -> pl.LazyFrame:
    rows = []
    for index in range(60):
        code = f"{index:06d}"
        previous = 100.0 + index
        current = previous * (1.0 + index / 100.0)
        for year, value in (("2024", previous), ("2025", current)):
            rows.append(
                {
                    "stockCode": code,
                    "bsns_year": year,
                    "fs_div": "CFS",
                    "reprt_code": "11011",
                    "sj_div": "CIS",
                    "account_nm": "당기순이익",
                    "thstrm_amount": str(value),
                }
            )
            rows.append(
                {
                    "stockCode": code,
                    "bsns_year": year,
                    "fs_div": "CFS",
                    "reprt_code": "11011",
                    "sj_div": "BS",
                    "account_nm": "자산총계",
                    "thstrm_amount": "999999999",
                }
            )

    for index in range(2):
        rows.append(
            {
                "stockCode": f"9{index:05d}",
                "bsns_year": "2026",
                "fs_div": "CFS",
                "reprt_code": "11011",
                "sj_div": "CIS",
                "account_nm": "당기순이익",
                "thstrm_amount": "200",
            }
        )
    return pl.DataFrame(rows).lazy()


def test_earnings_surprise_filters_before_collect_and_skips_thin_latest_year(monkeypatch):
    from dartlab.quant.alphas import earningsSurprise

    monkeypatch.setattr(earningsSurprise, "loadScanParquet", lambda *_args, **_kwargs: _dartFinance())

    result = earningsSurprise.calcEarningsSurprise(market="KR", stockCode="000059")

    assert result is not None
    assert result["year"] == "2025"
    assert result["prevYear"] == "2024"
    assert result["universe"] == 60
    assert result["score"] > 0
