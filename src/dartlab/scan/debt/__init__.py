"""부채 구조 전수 스캔 — 사채 만기, 부채비율, ICR, 위험등급.

Public API:
    scan_debt()  → pl.DataFrame (전체 상장사 부채 현황)
"""

from __future__ import annotations

import polars as pl

from dartlab.scan.debt.risk import classify_risk, scan_icr
from dartlab.scan.debt.scanner import scan_bonds, scan_debt_mix, scan_short_debt


def scan_debt(*, verbose: bool = True) -> pl.DataFrame:
    """전체 상장사 부채 스캔 → 종합 DataFrame.

    컬럼: 종목코드, 사채잔액, 단기잔액, 단기비중, 단기사채잔액, CP잔액,
          단기채무합계, 총부채, 부채비율, ICR, 위험등급
    """

    def _log(msg: str) -> None:
        if verbose:
            print(msg)

    _log("1/4 사채 만기...")
    bond_map = scan_bonds()
    _log(f"  -> {len(bond_map)}종목")

    _log("2/4 단기사채/CP...")
    short_map = scan_short_debt()
    _log(f"  -> {len(short_map)}종목")

    _log("3/4 부채비율...")
    debt_map = scan_debt_mix()
    _log(f"  -> {len(debt_map)}종목")

    _log("4/4 이자보상배율...")
    icr_map = scan_icr()
    _log(f"  -> {len(icr_map)}종목")

    all_codes = set(bond_map) | set(debt_map) | set(icr_map) | set(short_map)

    results = []
    for code in all_codes:
        b = bond_map.get(code, {})
        s = short_map.get(code, {})
        d = debt_map.get(code, {})
        icr = icr_map.get(code)

        short_ratio = b.get("단기비중")
        shortDebtTotal = s.get("단기채무합계")
        risk = classify_risk(icr, short_ratio, shortDebtTotal) if (b or s or icr is not None) else None

        results.append(
            {
                "종목코드": code,
                "사채잔액": b.get("사채잔액"),
                "단기잔액": b.get("단기잔액"),
                "단기비중": short_ratio,
                "단기사채잔액": s.get("단기사채잔액"),
                "CP잔액": s.get("CP잔액"),
                "단기채무합계": shortDebtTotal,
                "총부채": d.get("총부채"),
                "부채비율": d.get("부채비율"),
                "ICR": icr,
                "위험등급": risk,
            }
        )

    df = pl.DataFrame(results)
    _log(f"부채 스캔 완료: {df.shape[0]}종목")
    return df


__all__ = ["scan_debt"]
