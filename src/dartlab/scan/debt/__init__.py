"""부채 구조 전수 스캔 — 사채 만기, 부채비율, ICR, 위험등급.

Public API:
    scan_debt()  → pl.DataFrame (전체 상장사 부채 현황)
"""

from __future__ import annotations

import polars as pl

from dartlab.scan.debt.risk import classify_risk, scan_icr
from dartlab.scan.debt.scanner import scan_bonds, scan_debt_mix


def scan_debt(*, verbose: bool = True) -> pl.DataFrame:
    """전체 상장사 부채 스캔 → 종합 DataFrame.

    컬럼: 종목코드, 사채잔액, 단기잔액, 단기비중, 총부채, 부채비율, ICR, 위험등급
    """

    def _log(msg: str) -> None:
        if verbose:
            print(msg)

    _log("1/3 사채 만기...")
    bond_map = scan_bonds()
    _log(f"  → {len(bond_map)}종목")

    _log("2/3 부채비율...")
    debt_map = scan_debt_mix()
    _log(f"  → {len(debt_map)}종목")

    _log("3/3 이자보상배율...")
    icr_map = scan_icr()
    _log(f"  → {len(icr_map)}종목")

    all_codes = set(bond_map) | set(debt_map) | set(icr_map)

    results = []
    for code in all_codes:
        b = bond_map.get(code, {})
        d = debt_map.get(code, {})
        icr = icr_map.get(code)

        short_ratio = b.get("단기비중")
        risk = classify_risk(icr, short_ratio) if (b or icr is not None) else None

        results.append(
            {
                "종목코드": code,
                "사채잔액": b.get("사채잔액"),
                "단기잔액": b.get("단기잔액"),
                "단기비중": short_ratio,
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
