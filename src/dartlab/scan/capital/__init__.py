"""주주환원 전수 스캔 — 배당, 자사주, 증자/감자 → 순환원 분류.

Public API:
    scan_capital()  → pl.DataFrame (전체 상장사 주주환원 현황)
"""

from __future__ import annotations

import polars as pl

from dartlab.scan.capital.classifier import classify_return
from dartlab.scan.capital.scanner import (
    scan_capital_change,
    scan_dividend,
    scan_treasury_stock,
)


def scan_capital(*, verbose: bool = True) -> pl.DataFrame:
    """전체 상장사 주주환원 스캔 → 순환원 분류 DataFrame.

    컬럼: 종목코드, 배당여부, DPS, 배당수익률, 자사주보유, 자사주취득,
          자사주처분, 자사주소각, 취득수량, 처분수량, 소각수량,
          최근증자, 환원점수, 분류, 모순형
    """

    def _log(msg: str) -> None:
        if verbose:
            print(msg)

    _log("1/3 배당 스캔...")
    div_map = scan_dividend()
    _log(f"  → {len(div_map)}종목")

    _log("2/3 자사주 스캔...")
    treasury_map = scan_treasury_stock()
    _log(f"  → {len(treasury_map)}종목")

    _log("3/3 증자/감자 스캔...")
    cap_map = scan_capital_change()
    _log(f"  → {len(cap_map)}종목")

    all_codes = set(div_map) | set(treasury_map) | set(cap_map)

    results = []
    for code in all_codes:
        d = div_map.get(code, {})
        t = treasury_map.get(code, {})
        c = cap_map.get(code, {})

        has_dividend = d.get("배당여부", False)
        has_buyback = t.get("당기취득", False)
        has_treasury = t.get("자사주보유", False)
        has_disposal = t.get("당기처분", False)
        has_cancel = t.get("당기소각", False)
        recent_increase = c.get("최근증자", False)

        category, contradiction = classify_return(has_dividend, has_buyback, recent_increase)

        # 환원 점수 (참고용) — 소각은 가장 강한 환원 신호
        return_score = 0
        if has_dividend:
            return_score += 1
        if has_buyback:
            return_score += 1
        if has_cancel:
            return_score += 1
        if recent_increase:
            return_score -= 1

        results.append(
            {
                "stockCode": code,
                "배당여부": has_dividend,
                "DPS": d.get("DPS", 0.0),
                "배당수익률": d.get("배당수익률", 0.0),
                "자사주보유": has_treasury,
                "자사주취득": has_buyback,
                "자사주처분": has_disposal,
                "자사주소각": has_cancel,
                "취득수량": t.get("취득수량", 0),
                "처분수량": t.get("처분수량", 0),
                "소각수량": t.get("소각수량", 0),
                "최근증자": recent_increase,
                "환원점수": return_score,
                "분류": category,
                "모순형": contradiction,
            }
        )

    df = pl.DataFrame(results)
    _log(f"주주환원 스캔 완료: {df.shape[0]}종목")
    return df


__all__ = ["scan_capital"]
