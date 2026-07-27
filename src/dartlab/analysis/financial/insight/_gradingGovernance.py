"""analysis/financial/insight/grading 거버넌스 그룹 분리.

grading.py 가 1323 줄 god module 이라 거버넌스 분석 2 함수 분리.
identity 보존을 위해 grading.py 가 본 모듈에서 re-export 한다.

함수:
- _analyzeGovernanceFromSections — report 없을 때 sections 기반 (EDGAR)
- analyzeGovernance — 종합 거버넌스 분석 (감사/배당/지배구조)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

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

    docs = getattr(company, "docs", None)
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

    major = rpt.majorHolder
    if major is not None and major.totalShareRatio:
        maxScore += 3
        latest = None
        for v in reversed(major.totalShareRatio):
            if v is not None:
                latest = v
                break
        if latest is not None:
            if latest > 50:
                details.append(f"최대주주 지분 {latest:.1f}% — 지배력 안정")
                opps.append(Flag("positive", "governance", f"최대주주 {latest:.1f}%"))
                score += 3
            elif latest > 30:
                details.append(f"최대주주 지분 {latest:.1f}% — 적정 수준")
                score += 2
            elif latest > 20:
                details.append(f"최대주주 지분 {latest:.1f}%")
                score += 1
            else:
                details.append(f"최대주주 지분 {latest:.1f}% — 경영권 분산")
                risks.append(Flag("warning", "governance", f"최대주주 {latest:.1f}%"))

    audit = rpt.audit
    if audit is not None and audit.opinions:
        maxScore += 2
        latest = None
        for v in reversed(audit.opinions):
            if v is not None:
                latest = v
                break
        if latest is not None:
            if "적정" in str(latest):
                details.append("감사의견: 적정")
                score += 2
            else:
                details.append(f"감사의견: {latest}")
                risks.append(Flag("danger", "audit", f"감사의견 비적정: {latest}"))
                score -= 2

    # 감사인 안정성 (PCAOB AS 3101) — Big4 + 장기 유지
    _big4_kw = ["삼일", "PwC", "삼정", "KPMG", "한영", "EY", "안진", "Deloitte"]
    if audit is not None and audit.auditors:
        maxScore += 2
        uniqueAuditors = [a for a in audit.auditors if a is not None]
        latestAuditor = uniqueAuditors[-1] if uniqueAuditors else None

        if latestAuditor and any(kw in latestAuditor for kw in _big4_kw):
            # Big4 판정
            changeCount = sum(1 for i in range(1, len(uniqueAuditors)) if uniqueAuditors[i] != uniqueAuditors[i - 1])
            if changeCount == 0 and len(uniqueAuditors) >= 3:
                details.append(f"감사인: {latestAuditor} (Big4, 3년+ 유지)")
                score += 2
            elif changeCount == 0:
                details.append(f"감사인: {latestAuditor} (Big4)")
                score += 1
            else:
                details.append(f"감사인: {latestAuditor} (Big4, {changeCount}회 교체)")
                score += 1
        elif latestAuditor:
            details.append(f"감사인: {latestAuditor} (비Big4)")
            # 빈번 교체 시 감점
            changeCount = sum(1 for i in range(1, len(uniqueAuditors)) if uniqueAuditors[i] != uniqueAuditors[i - 1])
            if changeCount >= 2:
                score -= 1
                risks.append(Flag("warning", "audit", f"감사인 빈번 교체 ({changeCount}회)"))

    # 내부통제 (SOX 302/404)
    try:
        ic = getattr(rpt, "internalControl", None)
        if ic is not None:
            controlDf = getattr(ic, "controlDf", None)
            if controlDf is not None and len(controlDf) > 0:
                maxScore += 2
                latestRow = controlDf.row(-1, named=True)
                hasWeakness = latestRow.get("hasWeakness", False)
                opinion = latestRow.get("opinion", "")
                if hasWeakness:
                    score -= 2
                    details.append(f"내부통제: 취약점 보고 ({opinion})")
                    risks.append(Flag("danger", "governance", "내부통제 취약점"))
                else:
                    score += 2
                    details.append(f"내부통제: {opinion or '적정'}")
    except (AttributeError, IndexError):
        pass

    # 감사위원회 활동
    try:
        auditSys = getattr(rpt, "auditSystem", None)
        if auditSys is not None:
            activity = getattr(auditSys, "activity", None) or []
            if activity:
                maxScore += 1
                score += 1
                details.append(f"감사위원회: {len(activity)}건 활동")
            elif getattr(auditSys, "committee", None):
                maxScore += 1
                details.append("감사위원회: 설치됨 (활동 미확인)")
    except AttributeError:
        pass

    div = rpt.dividend
    if div is not None and div.dps:
        maxScore += 3
        recentDps = [d for d in div.dps[-3:] if d is not None]
        if recentDps and all(d > 0 for d in recentDps):
            if len(recentDps) >= 3:
                details.append(f"3년 연속 배당 (DPS: {recentDps[-1]:,.0f}원)")
                opps.append(Flag("positive", "shareholder", "안정적 배당"))
                score += 3
            else:
                details.append(f"배당 실시 (DPS: {recentDps[-1]:,.0f}원)")
                score += 2
        elif recentDps and recentDps[-1] > 0:
            details.append(f"배당 재개 (DPS: {recentDps[-1]:,.0f}원)")
            score += 1
        else:
            details.append("무배당")
            risks.append(Flag("warning", "shareholder", "무배당"))

    if maxScore == 0:
        return InsightResult("N", "지배구조 데이터 없음")

    grade = _scoreToGrade(score, maxScore)
    summary = "지배구조 " + (
        "우수"
        if grade == "A"
        else "안정"
        if grade == "B"
        else "보통"
        if grade == "C"
        else "주의"
        if grade == "D"
        else "위험"
    )
    return InsightResult(grade, summary, details, risks, opps)


__all__ = ["_analyzeGovernanceFromSections", "analyzeGovernance"]
