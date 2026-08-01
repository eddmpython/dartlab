"""거버넌스 5 신호 블록 (analyzeGovernance 의 신호별 seam).

최대주주·감사의견·감사인·내부통제·감사위원회·배당은 모두 "report 하위 namespace 를 읽어
details/risks/opps 에 문장을 더하고 score/maxScore 를 올린다" 는 같은 모양이다.
블록마다 함수 하나로 떼어내고, 누적 리스트는 인자로 받아 제자리 변경한다.
반환은 (score 증분, maxScore 증분) 이다.
"""

from __future__ import annotations

from dartlab.analysis.financial._seriesMath import _latestNotNone
from dartlab.analysis.financial.insight.types import Flag
from dartlab.providers._common.auditOpinion import normalizeAuditOpinion

_BIG4_KEYWORDS = ["삼일", "PwC", "삼정", "KPMG", "한영", "EY", "안진", "Deloitte"]


def _majorHolderSignal(
    major,
    details: list[str],
    risks: list[Flag],
    opps: list[Flag],
) -> tuple[int, int]:
    """최대주주 지분율 신호.

    Parameters
    ----------
    major : Any
        rpt.majorHolder namespace.
    details, risks, opps : list
        누적 리스트. 제자리 변경.

    Returns
    -------
    tuple[int, int]
        (score 증분, maxScore 증분).
    """
    if not (major is not None and major.totalShareRatio):
        return 0, 0
    latest = _latestNotNone(major.totalShareRatio)
    if latest is None:
        return 0, 3
    if latest > 50:
        details.append(f"최대주주 지분 {latest:.1f}%. 지배력 안정")
        opps.append(Flag("positive", "governance", f"최대주주 {latest:.1f}%"))
        return 3, 3
    if latest > 30:
        details.append(f"최대주주 지분 {latest:.1f}%. 적정 수준")
        return 2, 3
    if latest > 20:
        details.append(f"최대주주 지분 {latest:.1f}%")
        return 1, 3
    details.append(f"최대주주 지분 {latest:.1f}%. 경영권 분산")
    risks.append(Flag("warning", "governance", f"최대주주 {latest:.1f}%"))
    return 0, 3


def _auditOpinionSignal(audit, details: list[str], risks: list[Flag]) -> tuple[int, int]:
    """감사의견 신호. 비적정은 감점 + danger 플래그.

    Parameters
    ----------
    audit : Any
        rpt.audit namespace.
    details, risks : list
        누적 리스트. 제자리 변경.

    Returns
    -------
    tuple[int, int]
        (score 증분, maxScore 증분).
    """
    if not (audit is not None and audit.opinions):
        return 0, 0
    latest = _latestNotNone(audit.opinions)
    normalized = normalizeAuditOpinion(latest)
    if normalized is None:
        return 0, 0
    if normalized == "적정의견":
        details.append("감사의견: 적정의견 명시 관측")
        return 2, 2
    details.append(f"감사의견: {normalized}")
    risks.append(Flag("danger", "audit", f"감사의견 비적정: {normalized}"))
    return -2, 2


def _auditorStabilitySignal(audit, details: list[str], risks: list[Flag]) -> tuple[int, int]:
    """감사인 안정성 (PCAOB AS 3101). Big4 여부 + 장기 유지.

    Parameters
    ----------
    audit : Any
        rpt.audit namespace.
    details, risks : list
        누적 리스트. 제자리 변경.

    Returns
    -------
    tuple[int, int]
        (score 증분, maxScore 증분).
    """
    if not (audit is not None and audit.auditors):
        return 0, 0
    uniqueAuditors = [a for a in audit.auditors if a is not None]
    latestAuditor = uniqueAuditors[-1] if uniqueAuditors else None
    if not latestAuditor:
        return 0, 2

    changeCount = sum(1 for i in range(1, len(uniqueAuditors)) if uniqueAuditors[i] != uniqueAuditors[i - 1])
    if any(kw in latestAuditor for kw in _BIG4_KEYWORDS):
        if changeCount == 0 and len(uniqueAuditors) >= 3:
            details.append(f"감사인: {latestAuditor} (Big4, 3년+ 유지)")
            return 2, 2
        if changeCount == 0:
            details.append(f"감사인: {latestAuditor} (Big4)")
            return 1, 2
        details.append(f"감사인: {latestAuditor} (Big4, {changeCount}회 교체)")
        return 1, 2

    details.append(f"감사인: {latestAuditor} (비Big4)")
    # 빈번 교체 시 감점
    if changeCount >= 2:
        risks.append(Flag("warning", "audit", f"감사인 빈번 교체 ({changeCount}회)"))
        return -1, 2
    return 0, 2


def _internalControlSignal(rpt, details: list[str], risks: list[Flag]) -> tuple[int, int]:
    """내부통제 (SOX 302/404) 신호.

    Parameters
    ----------
    rpt : Any
        company.report namespace.
    details, risks : list
        누적 리스트. 제자리 변경.

    Returns
    -------
    tuple[int, int]
        (score 증분, maxScore 증분). 속성/인덱스 접근 실패 시 (0, 0).
    """
    score = 0
    maxDelta = 0
    try:
        ic = getattr(rpt, "internalControl", None)
        if ic is not None:
            controlDf = getattr(ic, "controlDf", None)
            if controlDf is not None and len(controlDf) > 0:
                maxDelta = 2
                latestRow = controlDf.row(-1, named=True)
                hasWeakness = latestRow.get("hasWeakness", False)
                opinion = latestRow.get("opinion", "")
                if hasWeakness:
                    score = -2
                    details.append(f"내부통제: 취약점 보고 ({opinion})")
                    risks.append(Flag("danger", "governance", "내부통제 취약점"))
                else:
                    score = 2
                    details.append(f"내부통제: {opinion or '적정'}")
    except (AttributeError, IndexError):
        # 원본과 같은 자리에서 삼킨다. maxDelta 는 이미 오른 값을 그대로 유지한다.
        pass
    return score, maxDelta


def _auditCommitteeSignal(rpt, details: list[str]) -> tuple[int, int]:
    """감사위원회 활동 신호.

    Parameters
    ----------
    rpt : Any
        company.report namespace.
    details : list
        누적 리스트. 제자리 변경.

    Returns
    -------
    tuple[int, int]
        (score 증분, maxScore 증분). 속성 접근 실패 시 (0, 0).
    """
    score = 0
    maxDelta = 0
    try:
        auditSys = getattr(rpt, "auditSystem", None)
        if auditSys is not None:
            activity = getattr(auditSys, "activity", None) or []
            if activity:
                maxDelta = 1
                score = 1
                details.append(f"감사위원회: {len(activity)}건 활동")
            elif getattr(auditSys, "committee", None):
                maxDelta = 1
                details.append("감사위원회: 설치됨 (활동 미확인)")
    except AttributeError:
        # 원본과 같은 자리에서 삼킨다. 이미 오른 증분은 그대로 유지한다.
        pass
    return score, maxDelta


def _dividendSignal(div, details: list[str], risks: list[Flag], opps: list[Flag]) -> tuple[int, int]:
    """배당 지속성 신호.

    Parameters
    ----------
    div : Any
        rpt.dividend namespace.
    details, risks, opps : list
        누적 리스트. 제자리 변경.

    Returns
    -------
    tuple[int, int]
        (score 증분, maxScore 증분).
    """
    if not (div is not None and div.dps):
        return 0, 0
    recentDps = [d for d in div.dps[-3:] if d is not None]
    if recentDps and all(d > 0 for d in recentDps):
        if len(recentDps) >= 3:
            details.append(f"3년 연속 배당 (DPS: {recentDps[-1]:,.0f}원)")
            opps.append(Flag("positive", "shareholder", "안정적 배당"))
            return 3, 3
        details.append(f"배당 실시 (DPS: {recentDps[-1]:,.0f}원)")
        return 2, 3
    if recentDps and recentDps[-1] > 0:
        details.append(f"배당 재개 (DPS: {recentDps[-1]:,.0f}원)")
        return 1, 3
    details.append("무배당")
    risks.append(Flag("warning", "shareholder", "무배당"))
    return 0, 3


def _governanceSummary(grade: str) -> str:
    """등급 -> 한 줄 요약.

    Parameters
    ----------
    grade : str
        'A'~'F' 등급.

    Returns
    -------
    str
        '지배구조 우수' 등 요약 문장.
    """
    label = {"A": "우수", "B": "안정", "C": "보통", "D": "주의"}.get(grade, "위험")
    return "지배구조 " + label


__all__ = [
    "_auditCommitteeSignal",
    "_auditOpinionSignal",
    "_auditorStabilitySignal",
    "_dividendSignal",
    "_governanceSummary",
    "_internalControlSignal",
    "_majorHolderSignal",
]
