"""governance.py 깊이 분석 — 5 종 분리.

calcGovernanceFlags + calcOwnerConcentration + calcCEOTurnover +
calcRelatedPartyIntensity + calcLegalEventRisk 본체.
"""

from __future__ import annotations

from dartlab.core.memory import memoizedCalc
from dartlab.core.polarsUtil import isEmptyDf
from dartlab.core.utils.helpers import MAX_RATIO_YEARS, annualColsFromPeriods, toDictBySnakeId
from dartlab.providers._common.auditOpinion import normalizeAuditOpinion

CEO_TURNOVER_WINDOW_YEARS = 5
RELATED_PARTY_PARSER_UNIT = 1_000_000
LEGAL_EVENT_WINDOW_YEARS = 3


def _safePivotExecutivePay(*args, **kwargs):
    from dartlab.analysis.financial.governance import _safePivotExecutivePay as _f

    return _f(*args, **kwargs)


def _safePivotMajorHolder(*args, **kwargs):
    from dartlab.analysis.financial.governance import _safePivotMajorHolder as _f

    return _f(*args, **kwargs)


def _safePivotExecutive(*args, **kwargs):
    from dartlab.analysis.financial.governance import _safePivotExecutive as _f

    return _f(*args, **kwargs)


def _safePivotAudit(*args, **kwargs):
    from dartlab.analysis.financial.governance import _safePivotAudit as _f

    return _f(*args, **kwargs)


def _getDartStockCode(*args, **kwargs):
    from dartlab.analysis.financial.governance import _getDartStockCode as _f

    return _f(*args, **kwargs)


def _loadSanction(*args, **kwargs):
    from dartlab.analysis.financial.governance import _loadSanction as _f

    return _f(*args, **kwargs)


def _loadContingentLiability(*args, **kwargs):
    from dartlab.analysis.financial.governance import _loadContingentLiability as _f

    return _f(*args, **kwargs)


def _fetchLatestEquity(*args, **kwargs):
    from dartlab.analysis.financial.governance import _fetchLatestEquity as _f

    return _f(*args, **kwargs)


def _loadExecutiveDocs(*args, **kwargs):
    from dartlab.analysis.financial.governance import _loadExecutiveDocs as _f

    return _f(*args, **kwargs)


def _loadRelatedPartyTx(*args, **kwargs):
    from dartlab.analysis.financial.governance import _loadRelatedPartyTx as _f

    return _f(*args, **kwargs)


def calcOwnershipTrend(*args, **kwargs):
    """최대주주 지분 시계열 — governance.py 본체로 위임 (cycle 회피용 lazy proxy).

    Requires:
        governance.py 본체 import.

    Raises:
        없음.

    Example:
        >>> calcOwnershipTrend(company)["latest"]
        0.62
    """
    from dartlab.analysis.financial.governance import calcOwnershipTrend as _f

    return _f(*args, **kwargs)


def calcBoardComposition(*args, **kwargs):
    """이사회 구성 분석 — governance.py 본체로 위임 (cycle 회피용 lazy proxy).

    Requires:
        governance.py 본체 import.

    Raises:
        없음.

    Example:
        >>> calcBoardComposition(company)["outsideRatio"]
        0.6
    """
    from dartlab.analysis.financial.governance import calcBoardComposition as _f

    return _f(*args, **kwargs)


def calcAuditOpinionTrend(*args, **kwargs):
    """감사 의견 시계열 — governance.py 본체로 위임 (cycle 회피용 lazy proxy).

    Requires:
        governance.py 본체 import.

    Raises:
        없음.

    Example:
        >>> calcAuditOpinionTrend(company)["latest"]
        '적정'
    """
    from dartlab.analysis.financial.governance import calcAuditOpinionTrend as _f

    return _f(*args, **kwargs)


def calcExecutivePayDivergence(*args, **kwargs):
    """임원 보수 괴리 — governance.py 본체로 위임 (cycle 회피용 lazy proxy).

    Requires:
        governance.py 본체 import.

    Raises:
        없음.

    Example:
        >>> calcExecutivePayDivergence(company)["divergence"]
        2.5
    """
    from dartlab.analysis.financial.governance import calcExecutivePayDivergence as _f

    return _f(*args, **kwargs)


def calcIndependentDirectorQuality(*args, **kwargs):
    """사외이사 품질 — governance.py 본체로 위임 (cycle 회피용 lazy proxy).

    Requires:
        governance.py 본체 import.

    Raises:
        없음.

    Example:
        >>> calcIndependentDirectorQuality(company)["score"]
        70
    """
    from dartlab.analysis.financial.governance import calcIndependentDirectorQuality as _f

    return _f(*args, **kwargs)


@memoizedCalc
def calcGovernanceFlags(company, *, basePeriod: str | None = None) -> list[tuple[str, str]]:
    """지배구조 경고/기회 플래그.

    Returns
    -------
    list[tuple[str, str]]
        (message, severity) 쌍 목록. severity: "warning" | "opportunity"

    Capabilities:
        - 5 governance sub-calc 결과 → warning/opportunity 플래그 자동 누적
        - 최대주주/이사회/감사/보수/사외이사 결과 종합

    Guide:
        story governance 플래그 박스. flag ≥ 2 = governance 위험 다중 신호.

    When:
        Story governance flag + AI 거버넌스 위험 답변.

    How:
        5 sub-calc 호출 → 임계 비교 → 플래그 누적.

    Requires:
        governance sub-calc 가용.

    Raises:
        없음.

    Example:
        >>> calcGovernanceFlags(company)
        [('최대주주 지분 70%+', 'warning')]

    See Also:
        - calcOwnerConcentration : 종합 owner score
        - governance.* : sub-calc

    AIContext:
        "거버넌스 위험" 답변 시 flag 인용.
    """
    flags: list[tuple[str, str]] = []

    # 최대주주 지분
    ownership = calcOwnershipTrend(company)
    if ownership and ownership["history"]:
        latest = ownership["history"][-1]
        r = latest.get("ratio")
        if r is not None:
            if r > 50:
                flags.append((f"최대주주 지분율 {r:.1f}% -- 과반 지배", "warning"))
            elif r < 20:
                flags.append((f"최대주주 지분율 {r:.1f}% -- 경영권 방어 취약", "warning"))

        # 지분 변동 추이
        history = ownership["history"]
        if len(history) >= 3:
            changes = [h["change"] for h in history[-3:] if h.get("change") is not None]
            if len(changes) >= 2 and all(c < -1.0 for c in changes):
                flags.append(("최대주주 지분 2기 연속 감소 -- 지분 희석 주의", "warning"))

    # 이사회 구성
    board = calcBoardComposition(company)
    if board:
        outsideRatio = board.get("outsideRatio")
        if outsideRatio is not None:
            if outsideRatio < 25:
                flags.append((f"사외이사비율 {outsideRatio:.0f}% -- 이사회 독립성 취약", "warning"))
            elif outsideRatio >= 50:
                flags.append((f"사외이사비율 {outsideRatio:.0f}% -- 이사회 독립성 양호", "opportunity"))

    # 감사의견
    audit = calcAuditOpinionTrend(company)
    if audit and audit["history"]:
        latest = audit["history"][-1]
        opinion = latest.get("opinion")
        normalized = normalizeAuditOpinion(opinion)
        if normalized and normalized != "적정의견":
            flags.append((f"최근 감사의견: {normalized}", "warning"))

        # 감사인 변경
        changes = [h for h in audit["history"] if h.get("auditorChanged")]
        if len(changes) >= 2:
            flags.append(("감사인 잦은 변경 -- 감사 독립성 점검 필요", "warning"))

    # 대표이사 교체 — 데이터 없으면 플래그 없음 (None safe check, 가짜 0 회피)
    ceo = calcCEOTurnover(company)
    if ceo:
        cnt = ceo.get("turnoverCount")
        n = ceo.get("windowYears", CEO_TURNOVER_WINDOW_YEARS)
        if cnt is not None and cnt >= 2:
            flags.append((f"최근 {n}년 대표이사 교체 {cnt}회 -- 경영진 불안정", "warning"))
        avgT = ceo.get("avgTenureYears")
        if avgT is not None and avgT < 3:
            flags.append((f"대표이사 평균 재임 {avgT:.1f}년 -- 단기 재임 구간 (crash risk)", "warning"))

    # 오너 집중도 (본인/특수관계 분리) — None 보고 누락 vs 0 진짜 무지분 구분
    owner = calcOwnerConcentration(company)
    if owner and owner.get("latest"):
        lt = owner["latest"]
        top1 = lt.get("top1Share")
        totalR = lt.get("topHolderRatio")
        # 소유-지배 괴리 패턴: 본인 지분 적은데 특수관계 포함 총합이 큰 경우
        if top1 is not None and totalR is not None and top1 < 10 and totalR >= 40:
            flags.append(
                (
                    f"본인 지분 {top1:.1f}% vs 특수관계 포함 {totalR:.1f}% -- 소유-지배 괴리 큼",
                    "warning",
                )
            )
        # 과소 지배 — 20% 미만 + 특수관계도 낮음
        if totalR is not None and 0 < totalR < 20:
            flags.append((f"본인+특수관계 {totalR:.1f}% -- 경영권 방어 취약", "warning"))
        # 본인 지분 5년 급격 희석
        ch = owner.get("top1Change5y")
        if ch is not None and ch <= -5:
            flags.append((f"본인 지분 5년간 {ch:+.1f}%p 희석 -- 승계/상속 이벤트 가능", "warning"))

    # 법적 이벤트 리스크 (제재·소송·채무보증) — None 보고 누락 vs 0 무이벤트 구분
    legal = calcLegalEventRisk(company)
    if legal:
        n = legal.get("windowYears", LEGAL_EVENT_WINDOW_YEARS)
        sanctionCount = legal.get("sanctionCount")
        if sanctionCount is not None and sanctionCount >= 1:
            amt = legal.get("sanctionAmount")
            # 1억 이상만 금액 표시 — 파서 단위 혼재로 1억 미만은 불확실
            amtText = f" (누적 {amt / 1e8:.1f}억원)" if amt is not None and amt >= 1_0000_0000 else ""
            flags.append((f"최근 {n}년 제재 {sanctionCount}건{amtText} -- 규제 리스크", "warning"))
        lawsuitCount = legal.get("lawsuitCount")
        lawsuitAmount = legal.get("lawsuitAmount")
        if (lawsuitCount is not None and lawsuitCount >= 1) or (
            lawsuitAmount is not None and lawsuitAmount >= 100_0000_0000
        ):
            amtText = (
                f" (청구금액 {lawsuitAmount / 1e8:.0f}억원)"
                if lawsuitAmount is not None and lawsuitAmount >= 1_0000_0000
                else ""
            )
            flags.append(
                (
                    f"최근 {n}년 소송 {lawsuitCount if lawsuitCount is not None else 0}건{amtText} -- 법적 분쟁 진행",
                    "warning",
                )
            )
        gRatio = legal.get("guaranteeToEquity")
        if gRatio is not None and gRatio >= 50:
            flags.append((f"채무보증/자기자본 {gRatio:.0f}% -- 우발채무 부담 큼", "warning"))

    # 특수관계자 거래 집중도
    rpt = calcRelatedPartyIntensity(company)
    if rpt and rpt.get("latest"):
        lt = rpt["latest"]
        rev = lt.get("relatedRevenueRatio")
        if rev is not None and rev >= 30:
            trend = rpt.get("trend", "unknown")
            trendText = {"increasing": ", 증가 추세", "decreasing": ", 감소 추세", "stable": ""}.get(trend, "")
            flags.append(
                (
                    f"특수관계 매출 {rev:.0f}%{trendText} -- 내부거래 의존 높음",
                    "warning",
                )
            )
        gRatio = lt.get("relatedGuaranteeRatio")
        if gRatio is not None and gRatio >= 20:
            flags.append(
                (
                    f"특수관계 보증/자기자본 {gRatio:.0f}% -- 계열 지원 부담",
                    "warning",
                )
            )

    return flags


@memoizedCalc
def calcOwnerConcentration(company, *, basePeriod: str | None = None) -> dict | None:
    """오너 집중도 — 본인/특수관계 분리 지분 시계열.

    Capabilities:
        - 본인 vs 특수관계인 지분을 분리하여 연도별 합산 + 5 년 변동폭 추출
        - 한국 chaebol 소유-지배 괴리 식별

    report.majorHolder df에서 연도별 본인("본인") 지분과 특수관계인 합산
    지분을 분리한다. 한국 시장 특유의 "소유-지배 괴리(control-ownership
    disparity)"는 특수관계인을 통한 간접 지배가 크게 벌어질수록 커지므로,
    기존 합산 지분율(calcOwnershipTrend)만으로는 포착되지 않는 축이다.
    ECGI "Korea chaebol cash-flow rights" 연구와 MSCI Ownership & Control
    Key Issue 의 평가 방식에 대응한다.

    Parameters
    ----------
    company : Company
        분석 대상 기업 (DART).
    basePeriod : str, optional
        기준 기간. 현재 구현에서는 참고만 — 시계열 전부 반환.

    Returns
    -------
    dict | None
        None : majorHolder 데이터 없음.
        latest : dict — 최근 연도 스냅샷
            year : int — 연도
            topHolderRatio : float — 본인+특수관계 합산 지분 (%)
            top1Share : float — 본인 지분 (%)
            specialRelatedSum : float — 특수관계인 지분 합계 (%)
            specialRelatedCount : int — 특수관계인 수 (명)
        history : list[dict] — 연도별 추이 (최근 5년)
            year : int — 연도
            top1 : float — 본인 지분 (%)
            specialRelated : float — 특수관계 합계 (%)
            total : float — 본인+특수관계 합산 (%)
        top1Change5y : float | None — 5년간 본인 지분 변동폭 (%p)

    Raises
    ------
    없음 — 데이터 없음은 None 반환.

    Examples
    --------
    >>> c = dartlab.Company("005930")
    >>> c.analysis("지배구조")["ownerConcentration"]

    Notes
    -----
    - 보통주 기준. 우선주는 집계에서 제외.
    - 합계행("계")는 제외하고 본인·특수관계인 개별 행만 집계.
    - `top1Change5y`는 5년 이상 데이터가 있을 때만 계산. 짧으면 None.

    Guide
    -----
    `top1Share < 10%`이면서 `topHolderRatio > 40%`이면 소유-지배 괴리가
    큰 패턴(특수관계인을 통한 간접 지배). `top1Change5y < -5%p`이면
    본인 지분 희석 국면으로 상속·승계 이벤트 신호일 수 있다.

    When:
        한국 chaebol 특화 governance 평가 + AI 소유 구조 답변.

    How:
        report.majorHolder pivot → 본인/특수관계 분리 → 연도별 합산.

    Requires:
        report.majorHolder df.

    AIContext:
        chaebol 소유-지배 괴리 답변 시 top1Share + topHolderRatio 인용.

    See Also
    --------
    calcOwnershipTrend : 합산 지분율 시계열 (본/특수 미분리).
    calcGovernanceFlags : 본 calc 결과를 warning/opportunity로 소비.
    """
    import polars as pl

    result = _safePivotMajorHolder(company)
    if result is None or result.df is None or result.df.is_empty():
        return None

    df = result.df.filter(pl.col("nm") != "계")
    if "nm" in df.columns:
        df = df.filter(pl.col("nm").is_not_null())
    if df.is_empty():
        return None

    history: list[dict] = []
    for year in sorted(df["year"].unique().to_list())[-MAX_RATIO_YEARS:]:
        yearDf = df.filter(pl.col("year") == year)
        if yearDf.is_empty():
            continue
        latestQ = yearDf["quarterNum"].max()
        snap = yearDf.filter(pl.col("quarterNum") == latestQ)

        top1 = 0.0
        specialRelated = 0.0
        for row in snap.iter_rows(named=True):
            r = row.get("trmend_posesn_stock_qota_rt") or 0.0
            relate = (row.get("relate") or "").strip()
            if not relate or relate == "-":
                continue
            # "본인" 포함이면 본인 ("최대주주 본인", "본인" 등). 단 "특수관계인"의 "인"과
            # 겹치므로 "특수관계"가 포함된 경우는 제외.
            if "본인" in relate and "특수관계" not in relate:
                top1 = max(top1, float(r))
            else:
                specialRelated += float(r)

        history.append(
            {
                "year": int(year),
                "top1": round(top1, 2),
                "specialRelated": round(specialRelated, 2),
                "total": round(top1 + specialRelated, 2),
            }
        )

    if not history:
        return None

    latestYear = history[-1]["year"]
    latestDf = df.filter(pl.col("year") == latestYear)
    latestQ = latestDf["quarterNum"].max()
    latestSnap = latestDf.filter(pl.col("quarterNum") == latestQ)
    specialRelatedCount = 0
    for row in latestSnap.iter_rows(named=True):
        relate = (row.get("relate") or "").strip()
        if not relate or relate == "-":
            continue
        if "본인" in relate and "특수관계" not in relate:
            continue
        specialRelatedCount += 1

    latest = {
        "year": latestYear,
        "topHolderRatio": history[-1]["total"],
        "top1Share": history[-1]["top1"],
        "specialRelatedSum": history[-1]["specialRelated"],
        "specialRelatedCount": specialRelatedCount,
    }

    top1Change5y: float | None = None
    if len(history) >= 5:
        top1Change5y = round(history[-1]["top1"] - history[-5]["top1"], 2)
    elif len(history) >= 2:
        top1Change5y = round(history[-1]["top1"] - history[0]["top1"], 2)

    return {
        "latest": latest,
        "history": history,
        "top1Change5y": top1Change5y,
    }


# ── calcCEOTurnover + calcRelatedPartyIntensity + calcLegalEventRisk → _governanceDeepRest.py 분리 ──

from dartlab.analysis.financial._governanceDeepRest import (  # noqa: E402, F401
    calcCEOTurnover,
    calcLegalEventRisk,
    calcRelatedPartyIntensity,
)
