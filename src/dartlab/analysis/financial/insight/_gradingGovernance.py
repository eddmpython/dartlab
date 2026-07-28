"""analysis/financial/insight/grading 거버넌스 그룹 분리.

grading.py 가 1323 줄 god module 이라 거버넌스 분석 2 함수 분리.
identity 보존을 위해 grading.py 가 본 모듈에서 re-export 한다.

함수:
- _analyzeGovernanceFromSections — report 없을 때 sections 기반 (EDGAR)
- analyzeGovernance — 종합 거버넌스 분석 (감사/배당/지배구조)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dartlab.analysis.financial.insight._gradingGovernanceSignals import (
    _auditCommitteeSignal,
    _auditOpinionSignal,
    _auditorStabilitySignal,
    _dividendSignal,
    _governanceSummary,
    _internalControlSignal,
    _majorHolderSignal,
)
from dartlab.analysis.financial.insight._gradingScales import _scoreToGrade
from dartlab.analysis.financial.insight.types import Flag, InsightResult

if TYPE_CHECKING:
    from dartlab.company import Company


def _analyzeGovernanceFromSections(company: Company) -> InsightResult:
    """report가 없을 때 sections 기반 governance 분석 (EDGAR 등).

    Parameters
    ----------
    company : Company
        기업 객체. DART는 report/panel, EDGAR는 EDGAR sections view 사용.

    Returns
    -------
    InsightResult
        grade : str — 'A'~'N' 등급
        summary : str — 지배구조 요약
        details : list[str] — topic/블록 수, 기간 일관성 등
    """
    import polars as pl

    # 예전 이름은 company.docs 였다. 공개 namespace 정리 때 _docs 로 바뀌었는데 여기가
    # 안 따라와서 EDGAR 지배구조 분석이 어느 회사에서나 "데이터 없음" 을 돌려주었다.
    docs = getattr(company, "_docs", None)
    if docs is None:
        return InsightResult("N", "지배구조 데이터 없음")
    sec = getattr(docs, "sections", None)
    if sec is None or not isinstance(sec, pl.DataFrame) or sec.is_empty():
        return InsightResult("N", "지배구조 데이터 없음")

    # governance 관련 topic 검색 (EDGAR: director, compensation, ownership)
    gov_pattern = "(?i)governance|director|compensation|ownership|security.?owner|executive.?comp"
    gov_topics = sec.filter(pl.col("topic").cast(pl.Utf8).str.contains(gov_pattern))

    if gov_topics.is_empty():
        return InsightResult("N", "지배구조 데이터 없음")

    # 데이터 존재량으로 점수 부여
    n_topics = gov_topics.select("topic").unique().height
    n_blocks = gov_topics.height
    # 메타 컬럼 제외한 기간 컬럼 수
    meta_cols = {"topic", "blockType", "blockOrder", "textNodeType", "textLevel", "textPath", "source", "chapter"}
    period_cols = [c for c in gov_topics.columns if c not in meta_cols]
    n_periods = 0
    for col in period_cols:
        if gov_topics[col].drop_nulls().len() > 0:
            n_periods += 1

    details: list[str] = []
    score = 0
    max_score = 3

    if n_topics >= 3:
        score += 2
        details.append(f"지배구조 관련 {n_topics}개 topic, {n_blocks}개 블록 공시")
    elif n_topics >= 1:
        score += 1
        details.append(f"지배구조 관련 {n_topics}개 topic 공시")

    if n_periods >= 3:
        score += 1
        details.append(f"{n_periods}개 기간 연속 공시 (일관성 양호)")

    grade = _scoreToGrade(score, max_score)
    summary = "지배구조 " + ("양호" if grade in ("A", "B") else "보통" if grade == "C" else "제한적 정보")
    return InsightResult(grade, summary, details)


def analyzeGovernance(company: Company | None) -> InsightResult:
    """지배구조 분석.

    Capabilities:
        - 최대주주 지분 + 감사의견 + 감사인 (Big4 지속) + 내부통제 + 배당 5 신호 통합.

    Parameters
    ----------
    company : Company | None
        기업 객체. None이면 'N' 등급 반환.

    Returns
    -------
    InsightResult
        grade : str — 'A'~'N' 등급
        summary : str — 지배구조 요약
        details : list[str] — 최대주주, 감사의견, 감사인, 내부통제, 배당 등
        risks : list[Flag] — 지배구조 리스크
        opportunities : list[Flag] — 지배구조 강점

    Guide:
        report 네임스페이스 없으면 sections fallback (EDGAR). KR/US 동일 진입점.

    When:
        analyzeFinancial 의 'governance' 키 산출.

    How:
        rpt.majorHolder/audit/internalControl 추출 → 룰 분기 → score/maxScore 누적 → grade.

    Requires:
        company.report (DART KR) 또는 EDGAR sections view 보유.

    Raises:
        없음 — 데이터 부재 시 'N' 등급.

    Example:
        >>> analyzeGovernance(Company("005930"))
        InsightResult(grade='A', summary='지배구조 양호', ...)

    See Also:
        - _analyzeGovernanceFromSections: EDGAR fallback
        - analyzeAudit: 감사 단독 분석

    AIContext:
        ‘지배구조 양호/주의’ 답변 시 details 항목 인용. 감사의견 비적정은 우선 노출.
    """
    details: list[str] = []
    risks: list[Flag] = []
    opps: list[Flag] = []
    score = 0
    maxScore = 0

    if company is None:
        return InsightResult("N", "기업 데이터 없음")

    # report namespace가 없으면 sections 기반 fallback (EDGAR 등)
    if not hasattr(company, "report") or company.report is None:
        return _analyzeGovernanceFromSections(company)

    rpt = company.report
    audit = rpt.audit

    signals = [
        _majorHolderSignal(rpt.majorHolder, details, risks, opps),
        _auditOpinionSignal(audit, details, risks),
        _auditorStabilitySignal(audit, details, risks),
        _internalControlSignal(rpt, details, risks),
        _auditCommitteeSignal(rpt, details),
        _dividendSignal(rpt.dividend, details, risks, opps),
    ]
    for scoreDelta, maxDelta in signals:
        score += scoreDelta
        maxScore += maxDelta

    if maxScore == 0:
        return InsightResult("N", "지배구조 데이터 없음")

    grade = _scoreToGrade(score, maxScore)
    return InsightResult(grade, _governanceSummary(grade), details, risks, opps)


__all__ = ["_analyzeGovernanceFromSections", "analyzeGovernance"]
