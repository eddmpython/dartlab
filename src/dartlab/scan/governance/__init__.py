"""거버넌스 전수 스캔 — 지분율, 사외이사, pay ratio, 감사의견 → 종합 등급.

Public API:
    scan_governance()  → pl.DataFrame (전체 상장사 거버넌스 등급)
"""

from __future__ import annotations

import polars as pl

from dartlab.scan.governance.scanner import (
    scan_audit_opinion,
    scan_major_holder_pct,
    scan_outside_directors,
    scan_pay_ratio,
)
from dartlab.scan.governance.scorer import (
    grade,
    score_audit,
    score_outside_ratio,
    score_ownership,
    score_pay_ratio,
)


def scan_governance(*, verbose: bool = True) -> pl.DataFrame:
    """전체 상장사 거버넌스 스캔 → 종합 등급 DataFrame.

    컬럼: 종목코드, 지분율, 사외이사비율, pay_ratio, 감사의견,
          S_지분, S_사외, S_보수, S_감사, 총점, 등급, 유효축수
    """

    def _log(msg: str) -> None:
        if verbose:
            print(msg)

    _log("1/4 최대주주 지분율...")
    holder_map = scan_major_holder_pct()
    _log(f"  → {len(holder_map)}종목")

    _log("2/4 사외이사 비율...")
    outside_map = scan_outside_directors()
    _log(f"  → {len(outside_map)}종목")

    _log("3/4 pay ratio...")
    pay_ratio_map = scan_pay_ratio()
    _log(f"  → {len(pay_ratio_map)}종목")

    _log("4/4 감사의견...")
    audit_map = scan_audit_opinion()
    _log(f"  → {len(audit_map)}종목")

    all_codes = set(holder_map) | set(outside_map) | set(pay_ratio_map) | set(audit_map)

    results = []
    for code in all_codes:
        ownership = holder_map.get(code)
        outside = outside_map.get(code)
        pay_r = pay_ratio_map.get(code)
        audit = audit_map.get(code)

        s1 = score_ownership(ownership)
        s2 = score_outside_ratio(outside)
        s3 = score_pay_ratio(pay_r)
        s4 = score_audit(audit)
        total = s1 + s2 + s3 + s4
        g = grade(total)
        n_valid = sum(1 for v in [ownership, outside, pay_r, audit] if v is not None)

        results.append(
            {
                "종목코드": code,
                "지분율": round(ownership, 1) if ownership is not None else None,
                "사외이사비율": round(outside, 1) if outside is not None else None,
                "pay_ratio": round(pay_r, 1) if pay_r is not None else None,
                "감사의견": audit or "",
                "S_지분": s1,
                "S_사외": s2,
                "S_보수": s3,
                "S_감사": s4,
                "총점": total,
                "등급": g,
                "유효축수": n_valid,
            }
        )

    df = pl.DataFrame(results)
    _log(f"거버넌스 스캔 완료: {df.shape[0]}종목")
    return df


__all__ = ["scan_governance"]
