"""거버넌스 전수 스캔 — 지분율, 사외이사, pay ratio, 감사의견, 소액주주 → 종합 등급.

Public API:
    scanGovernance()  → pl.DataFrame (전체 상장사 거버넌스 등급)
"""

from __future__ import annotations

import polars as pl

from dartlab.core.logger import getLogger

_log = getLogger(__name__)


from dartlab.scan.governance.scanner import (
    scanAuditOpinion,
    scanMajorHolderChanges,
    scanMajorHolderPct,
    scanMinorityHolder,
    scanOutsideDirectors,
    scanPayRatio,
)
from dartlab.scan.governance.scorer import (
    grade,
    scoreAudit,
    scoreMinority,
    scoreOutsideRatio,
    scoreOwnership,
    scorePayRatio,
)


def scanGovernance(*, verbose: bool = True) -> pl.DataFrame:
    """전체 상장사 거버넌스 스캔 → 종합 등급 DataFrame.

    Parameters
    ----------
    verbose : bool, default True
        진행 라인을 ``logger.info`` 로 출력.

    Returns
    -------
    pl.DataFrame
        stockCode : str — 종목코드
        지분율 : float | None — 최대주주 지분율 (%)
        사외이사비율 : float | None — 사외이사 비율 (%)
        중도사임 : int — 중도사임 인원 (명)
        겸직 : int — 겸직 인원 (명)
        pay_ratio : float | None — 임원/직원 보수 배율 (배)
        감사의견 : str | None
        소액주주지분 : float | None — 소액주주 지분율 (%)
        S_지분 / S_사외 / S_보수 / S_감사 / S_분산 : float — 5 축별 점수 (점)
        총점 : float — 100 점 만점 종합 점수
        등급 : str — A/B/C/D/E
        유효축수 : int — 점수가 산출된 축 수 (0~5)

    Raises
    ------
    polars.PolarsError
        majorHolder · outsideDirector · executivePayAllTotal · auditOpinion ·
        minorityHolder report parquet 손상 시.

    Examples
    --------
    >>> import dartlab
    >>> df = dartlab.scan("governance")
    >>> df.filter(pl.col("등급") == "A").select(["종목코드", "총점"]).head()

    Capabilities:
        - 5 sub-scanner (지분율/사외이사/pay ratio/감사의견/소액주주지분) 결과 union → 종목별 5
          축 점수 + 100 점 만점 총점 + 5 단계 등급 (A/B/C/D/E).
        - 유효축수 컬럼으로 데이터 신뢰도 표시 (5/5 vs 부분).

    AIContext:
        Agent 가 ``dartlab.scan("governance")`` 호출 시 본 함수 dispatch. governance 종합 등급
        스크리닝, "A 등급" 종목 watchlist, 1 사 지배구조 5 축 비교 source.

    Guide:
        - 100 점 만점 = 5 축 × 20 점. scorer 모듈이 각 점수 산식 SSOT.
        - 사외이사 비율은 중도사임 / 겸직 인원도 결합해 점수 차감.

    When:
        대시보드 governance 카드 빌드 시. cross-company 등급 스크리닝 시.

    How:
        5 sub-scanner 순차 호출 → all_codes union → 종목별 dict merge → score* 5 함수 호출 →
        총점 + grade + 유효축수 → wide row 적재.

    Requires:
        - 로컬 ``data/dart/scan/report/{majorHolder,outsideDirector,executivePayAllTotal,auditOpinion,minorityHolder}.parquet``
          (``buildReport`` 산출)

    SeeAlso:
        - :mod:`dartlab.scan.governance.scanner` · :mod:`dartlab.scan.governance.scorer`
        - :func:`dartlab.scan.builders.kr.payload.governanceToInsight` — 등급 → InsightResult 변환
        - :func:`dartlab.scan.audit.scanAudit` — 감사 단독 axis (본 함수의 보완)
    """

    def _say(msg: str) -> None:
        if verbose:
            _log.info(msg)

    _say("1/5 최대주주 지분율...")
    holder_map = scanMajorHolderPct()
    _say(f"  → {len(holder_map)}종목")

    _say("2/5 사외이사 비율...")
    outside_map = scanOutsideDirectors()
    _say(f"  → {len(outside_map)}종목")

    _say("3/5 pay ratio...")
    pay_ratio_map = scanPayRatio()
    _say(f"  → {len(pay_ratio_map)}종목")

    _say("4/5 감사의견...")
    audit_map = scanAuditOpinion()
    _say(f"  → {len(audit_map)}종목")

    _say("5/6 소액주주 지분율...")
    minority_map = scanMinorityHolder()
    _say(f"  → {len(minority_map)}종목")

    _say("6/6 최대주주 변동...")
    change_map = scanMajorHolderChanges()
    _say(f"  → {len(change_map)}종목")

    all_codes = (
        set(holder_map) | set(outside_map) | set(pay_ratio_map) | set(audit_map) | set(minority_map) | set(change_map)
    )

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
        change = change_map.get(code, {})

        s1 = scoreOwnership(ownership)
        s2 = scoreOutsideRatio(outside_ratio, resign=resign, concurrent=concurrent)
        s3 = scorePayRatio(pay_r)
        s4 = scoreAudit(audit)
        s5 = scoreMinority(minority)
        total = s1 + s2 + s3 + s4 + s5
        g = grade(total)
        n_valid = sum(1 for v in [ownership, outside_ratio, pay_r, audit, minority] if v is not None)

        results.append(
            {
                "stockCode": code,
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
                "최대주주변동건수": change.get("최대주주변동건수"),
                "최대주주지분율": round(change["최대주주지분율"], 1)
                if change.get("최대주주지분율") is not None
                else None,
            }
        )

    df = pl.DataFrame(results)
    _say(f"거버넌스 스캔 완료: {df.shape[0]}종목, 5/5")
    return df


__all__ = ["scanGovernance"]
