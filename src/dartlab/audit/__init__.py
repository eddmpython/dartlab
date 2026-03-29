"""dartlab.audit — 분석 감사 엔진.

전 기업 순차 분석 + 품질 DB 누적.

사용법::

    import dartlab

    # 특정 기업 감사
    dartlab.runAudit(["005930", "035420"])

    # 전 기업 (getKindList 기반)
    dartlab.runAudit()

    # 이어하기 (오늘 날짜 기준 미완료분만)
    dartlab.runAudit(resume=True)

    # 결과 조회
    dartlab.queryAudit("005930")
    dartlab.queryAudit(issues=True)
    dartlab.queryAudit(coverage=True)
"""

from __future__ import annotations

from typing import Any

import polars as pl


def runAudit(
    codes: list[str] | None = None,
    *,
    resume: bool = False,
    runDate: str = "",
    onProgress: Any = None,
) -> list[dict[str, Any]]:
    """분석 감사 실행.

    Capabilities:
        - 종목코드 리스트 또는 전 기업 순차 분석
        - 15축 analysis + insights + valuation + forecast + ratios + review
        - SQLite 메타 + parquet 결과 + JSON review 자동 저장
        - resume=True로 중단된 감사 이어하기

    Requires:
        데이터: finance (자동 다운로드)

    AIContext:
        전 기업 분석 품질 측정 + 이슈 추적용.
        결과는 ~/.dartlab/data/audit/ 에 누적.

    Guide:
        - "삼성전자만 감사" -> runAudit(["005930"])
        - "전 기업 감사" -> runAudit()
        - "이어하기" -> runAudit(resume=True)

    SeeAlso:
        - queryAudit: 감사 결과 조회
        - analysis: 단일 종목 분석

    Args:
        codes: 종목코드 리스트. None이면 전 기업.
        resume: True면 오늘 날짜 기준 미완료분만.
        runDate: 감사 날짜 (기본 오늘).
        onProgress: 콜백 (stockCode, idx, total, result).

    Returns:
        list[dict] — 기업별 감사 결과 요약.

    Example::

        import dartlab
        results = dartlab.runAudit(["005930"])
        print(results[0]["coverageRate"])  # 0.85
    """
    from dartlab.audit.runner import AuditRunner
    from dartlab.audit.store import AuditStore

    store = AuditStore()
    runner = AuditRunner(store)
    try:
        return runner.auditBatch(
            codes, resume=resume, runDate=runDate, onProgress=onProgress,
        )
    finally:
        store.close()


def queryAudit(
    stockCode: str | None = None,
    *,
    axis: str | None = None,
    issues: bool = False,
    coverage: bool = False,
    runDate: str | None = None,
) -> pl.DataFrame:
    """감사 결과 조회.

    Capabilities:
        - 종목별 최신 분석 결과 (parquet)
        - 축별 크로스 기업 비교
        - 미해결 이슈 목록
        - 축별 coverage 통계

    Requires:
        감사 실행 이력 (runAudit 이후).

    AIContext:
        엔진 품질 모니터링 + 개선 우선순위 결정.

    Guide:
        - "삼성전자 감사 결과" -> queryAudit("005930")
        - "수익구조 전체 커버리지" -> queryAudit(axis="수익구조")
        - "미해결 이슈" -> queryAudit(issues=True)
        - "축별 커버리지" -> queryAudit(coverage=True)

    SeeAlso:
        - runAudit: 감사 실행

    Args:
        stockCode: 종목코드.
        axis: 분석 축 이름.
        issues: True면 미해결 이슈 반환.
        coverage: True면 축별 coverage 통계 반환.
        runDate: 날짜 필터.

    Returns:
        pl.DataFrame — 조회 결과.

    Example::

        import dartlab
        df = dartlab.queryAudit("005930")
        print(df)
    """
    from dartlab.audit.store import AuditStore

    store = AuditStore()
    try:
        if coverage:
            return store.coverageSummary(runDate)

        if issues:
            return store.queryIssues(resolved=False)

        if stockCode:
            df = store.queryParquet(stockCode, runDate)
            if df is not None and axis:
                return df.filter(pl.col("axis") == axis)
            if df is not None:
                return df
            return store.queryRuns(stockCode=stockCode)

        if axis:
            # 크로스 기업: 모든 parquet에서 해당 축 필터
            summary = store.coverageSummary(runDate)
            if not summary.is_empty():
                return summary.filter(pl.col("axis") == axis)
            return pl.DataFrame()

        # 기본: 전체 실행 기록
        return store.queryRuns(runDate=runDate)
    finally:
        store.close()


__all__ = ["runAudit", "queryAudit"]
