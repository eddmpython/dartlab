"""거버넌스 전수 스캔 — 지분율, 사외이사, pay ratio, 감사의견, 소액주주 → 종합 등급.

Public API:
    scan_governance()  → pl.DataFrame (전체 상장사 거버넌스 등급)
"""

from __future__ import annotations

import polars as pl

from dartlab.scan.governance.scanner import (
    scan_audit_opinion,
    scan_major_holder_pct,
    scan_minority_holder,
    scan_outside_directors,
    scan_pay_ratio,
)
from dartlab.scan.governance.scorer import (
    grade,
    score_audit,
    score_minority,
    score_outside_ratio,
    score_ownership,
    score_pay_ratio,
)


def scan_governance(*, verbose: bool = True) -> pl.DataFrame:
    """전체 상장사 거버넌스 스캔 → 종합 등급 DataFrame.

    컬럼: 종목코드, 지분율, 사외이사비율, 중도사임, 겸직, pay_ratio,
          감사의견, 소액주주지분, S_지분, S_사외, S_보수, S_감사, S_분산,
          총점, 등급, 유효축수
    """

    def _log(msg: str) -> None:
        if verbose:
            print(msg)

    _log("1/5 최대주주 지분율...")
    holder_map = scan_major_holder_pct()
    _log(f"  → {len(holder_map)}종목")

    _log("2/5 사외이사 비율...")
    outside_map = scan_outside_directors()
    _log(f"  → {len(outside_map)}종목")

    _log("3/5 pay ratio...")
    pay_ratio_map = scan_pay_ratio()
    _log(f"  → {len(pay_ratio_map)}종목")

    _log("4/5 감사의견...")
    audit_map = scan_audit_opinion()
    _log(f"  → {len(audit_map)}종목")

    _log("5/5 소액주주 지분율...")
    minority_map = scan_minority_holder()
    _log(f"  → {len(minority_map)}종목")

    all_codes = set(holder_map) | set(outside_map) | set(pay_ratio_map) | set(audit_map) | set(minority_map)

    results = []
    for code in all_codes:
        ownership = holder_map.get(code)
        outside_info = outside_map.get(code, {})
        outside_ratio = outside_info.get("사외이사비율") if outside_info else None
        resign = outside_info.get("중도사임", 0) if outside_info else 0
        concurrent = outside_info.get("겸직", 0) if outside_info else 0
        pay_r = pay_ratio_map.get(code)
        audit = audit_map.get(code)
        minority = minority_map.get(code)

        s1 = score_ownership(ownership)
        s2 = score_outside_ratio(outside_ratio, resign=resign, concurrent=concurrent)
        s3 = score_pay_ratio(pay_r)
        s4 = score_audit(audit)
        s5 = score_minority(minority)
        total = s1 + s2 + s3 + s4 + s5
        g = grade(total)
        n_valid = sum(1 for v in [ownership, outside_ratio, pay_r, audit, minority] if v is not None)

        results.append(
            {
                "종목코드": code,
                "지분율": round(ownership, 1) if ownership is not None else None,
                "사외이사비율": round(outside_ratio, 1) if outside_ratio is not None else None,
                "중도사임": resign,
                "겸직": concurrent,
                "pay_ratio": round(pay_r, 1) if pay_r is not None else None,
                "감사의견": audit or "",
                "소액주주지분": round(minority, 1) if minority is not None else None,
                "S_지분": s1,
                "S_사외": s2,
                "S_보수": s3,
                "S_감사": s4,
                "S_분산": s5,
                "총점": total,
                "등급": g,
                "유효축수": n_valid,
            }
        )

    df = pl.DataFrame(results)
    _log(f"거버넌스 스캔 완료: {df.shape[0]}종목, 5/5")
    return df


__all__ = ["scan_governance"]
