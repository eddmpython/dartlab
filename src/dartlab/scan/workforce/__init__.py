"""인력/급여 전수 스캔 — 직원 현황, 급여 성장, 고액 보수.

Public API:
    scan_workforce()  → pl.DataFrame (전체 상장사 인력 현황)
"""

from __future__ import annotations

import polars as pl

from dartlab.scan.workforce.growth import (
    compute_salary_vs_revenue,
    scan_revenue_growth,
    scan_salary_growth,
)
from dartlab.scan.workforce.scanner import (
    scan_employee,
    scan_revenue_per_employee,
    scan_top_pay,
)


def scan_workforce(*, verbose: bool = True) -> pl.DataFrame:
    """전체 상장사 인력 스캔 → 종합 DataFrame.

    컬럼: 종목코드, 직원수, 평균급여_만원, 남녀격차, 근속_년,
          직원당매출_억, 급여성장률, 매출성장률, 인건비부담,
          최고보수_억, 공개인원
    """

    def _log(msg: str) -> None:
        if verbose:
            print(msg)

    _log("1/4 직원 현황...")
    emp_map = scan_employee()
    _log(f"  → {len(emp_map)}종목")

    _log("2/4 직원당 매출...")
    rpe_map = scan_revenue_per_employee()
    _log(f"  → {len(rpe_map)}종목")

    _log("3/4 급여 vs 매출 성장률...")
    sal_map = scan_salary_growth()
    rev_map = scan_revenue_growth()
    growth_df = compute_salary_vs_revenue(sal_map, rev_map)
    growth_dict: dict[str, dict] = {}
    for row in growth_df.iter_rows(named=True):
        growth_dict[row["종목코드"]] = row
    _log(f"  → {len(growth_dict)}종목")

    _log("4/4 고액 보수...")
    top_map = scan_top_pay()
    _log(f"  → {len(top_map)}종목")

    # 합집합
    all_codes = set(emp_map) | set(rpe_map) | set(growth_dict) | set(top_map)

    results = []
    for code in all_codes:
        emp = emp_map.get(code, {})
        rpe = rpe_map.get(code)
        g = growth_dict.get(code, {})
        tp = top_map.get(code, {})

        results.append(
            {
                "종목코드": code,
                "직원수": emp.get("직원수"),
                "평균급여_만원": emp.get("평균급여_만원"),
                "남녀격차": emp.get("남녀격차"),
                "근속_년": emp.get("근속_년"),
                "직원당매출_억": rpe,
                "급여성장률": g.get("급여성장률"),
                "매출성장률": g.get("매출성장률"),
                "인건비부담": g.get("인건비부담"),
                "최고보수_억": tp.get("최고보수_억"),
                "공개인원": tp.get("공개인원"),
            }
        )

    df = pl.DataFrame(results)
    _log(f"인력 스캔 완료: {df.shape[0]}종목")
    return df


__all__ = ["scan_workforce"]
