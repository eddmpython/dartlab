"""5-1 지배구조 분석 -- 이 회사의 주인은 누구이며, 감시는 작동하는가.

report 데이터(최대주주, 임원, 감사의견, 임원보수)에서 지배구조 핵심 지표를
추출하며, 사업보고서 텍스트 섹션 파서(sanction, contingentLiability)로
제재·소송·채무보증 등 법적 이벤트 리스크를 집계한다.

DART 전용 섹션 기반 calc는 EDGAR Company에서 None을 반환한다 (SEC 공시 구조
한계 — 동등 소스 없음).
"""

from __future__ import annotations

import re
from types import SimpleNamespace

from dartlab.core.market import isKrStockCode
from dartlab.core.memory import memoizedCalc
from dartlab.core.polarsUtil import isEmptyDf
from dartlab.core.utils.helpers import MAX_RATIO_YEARS, annualColsFromPeriods, toDictBySnakeId

# ── docs 농장 은퇴 → providers.dart.panel.text 기반 정성 표 재건 (드롭 아님, SSOT) ──

_KRW_UNIT = {"백만원": 1_000_000, "백만": 1_000_000, "억원": 100_000_000, "억": 100_000_000, "천원": 1_000}


def _parseKrwAmount(cell: str | None) -> int | None:
    """제재/보증 금액 셀 → 원 단위 int. 외화(USD/UZS 등)·'-'·비숫자는 None."""
    if not cell:
        return None
    s = cell.strip()
    if s in ("-", ""):
        return None
    if re.search(r"[A-Za-z]", s):  # 외화 표기(USD/UZS/JPY ...) — FX 없이 환산 불가.
        return None
    for unit, mult in _KRW_UNIT.items():
        if unit in s:
            m = re.search(r"[\d,.]+", s)
            if m:
                try:
                    return int(float(m.group().replace(",", "")) * mult)
                except ValueError:
                    return None
    m = re.search(r"[\d,]+", s)  # 단위 표기 없으면 원 그대로.
    if m:
        try:
            return int(m.group().replace(",", ""))
        except ValueError:
            return None
    return None


# ── 최대주주 지분 시계열 ──


@memoizedCalc
def calcOwnershipTrend(company, *, basePeriod: str | None = None) -> dict | None:
    """최대주주 지분율 시계열 + 최근 주주 구성.

    Capabilities:
        - DART majorHolder 섹션의 연도별 합산 지분율 추이 + 최신 상위 10 주주.

    Args:
        company: 분석 대상 기업.
        basePeriod: 기준 기간 (현재 미사용).

    Returns:
        dict | None: history (연도별 ratio/change %p) + latestHolders (상위
        10) 객체. majorHolder 미가용 시 None.

    Guide:
        DART 전용 — EDGAR Company 는 None 반환 (SEC 동등 소스 없음).

    When:
        지배구조 보고에서 최대주주 안정성·지분 변동 추적할 때.

    How:
        ``_safePivotMajorHolder`` 결과를 MAX_RATIO_YEARS 로 절단 후 history.

    Requires:
        DART report.majorHolder 수신.

    Raises:
        없음.

    Example:
        >>> calcOwnershipTrend(Company("005930"))
        {"history": [...], "latestHolders": [...]}

    SeeAlso:
        - ``calcBoardComposition``: 이사회 구성

    AIContext:
        AI 답변에서 최대주주 변동·집중도 인용 시.
    """
    result = _safePivotMajorHolder(company)
    if result is None:
        return None

    years = result.years[-MAX_RATIO_YEARS:]
    ratios = result.totalShareRatio[-MAX_RATIO_YEARS:]

    history = []
    for i, y in enumerate(years):
        r = ratios[i] if i < len(ratios) else None
        prevR = ratios[i - 1] if i > 0 and (i - 1) < len(ratios) else None
        change = round(r - prevR, 2) if r is not None and prevR is not None else None
        history.append({"year": y, "ratio": r, "change": change})

    holders = result.latestHolders[:10] if result.latestHolders else []

    return (
        {
            "history": history,
            "latestHolders": holders,
        }
        if history
        else None
    )


# ── 이사회 구성 ──


@memoizedCalc
def calcBoardComposition(company, *, basePeriod: str | None = None) -> dict | None:
    """이사회 구성 -- 사외이사비율, 전체 임원 수.

    Capabilities:
        - 최신 분기 임원 수 / 등기 / 사외 / 사외이사비율 (%).

    Args:
        company: 분석 대상 기업.
        basePeriod: 기준 기간 (현재 미사용).

    Returns:
        dict | None: totalCount/registeredCount/outsideCount/outsideRatio.
        executive 미가용 시 None.

    Guide:
        DART report.executive 기반. EDGAR Company 는 None.

    When:
        지배구조 분석 헤더에서 이사회 한 줄 요약 표시.

    How:
        ``_safePivotExecutive`` 결과 카운트 사용 후 비율 계산.

    Requires:
        DART report.executive 수신.

    Raises:
        없음.

    Example:
        >>> calcBoardComposition(Company("005930"))
        {"totalCount": 10, "outsideRatio": 60.0, ...}

    SeeAlso:
        - ``calcIndependentDirectorQuality``: 독립성 평가

    AIContext:
        AI 답변에서 이사회 구성 한 줄 인용 시.
    """
    result = _safePivotExecutive(company)
    if result is None:
        return None

    total = result.totalCount
    registered = result.registeredCount
    outside = result.outsideCount
    if total == 0:
        return None

    outsideRatio = round(outside / total * 100, 1) if total > 0 else None

    return {
        "totalCount": total,
        "registeredCount": registered,
        "outsideCount": outside,
        "outsideRatio": outsideRatio,
    }


# ── 감사의견 시계열 ──


@memoizedCalc
def calcAuditOpinionTrend(company, *, basePeriod: str | None = None) -> dict | None:
    """감사의견 + 감사인 시계열.

    Capabilities:
        - 연도별 감사의견 + 감사법인 + 변경 플래그.

    Args:
        company: 분석 대상 기업.
        basePeriod: 기준 기간 (현재 미사용).

    Returns:
        dict | None: history 키에 year/opinion/auditor/auditorChanged 행
        리스트. audit 미가용 시 None.

    Guide:
        DART report.audit 기반. 감사인 변경 ≥ 1 회 감지.

    When:
        감사 안정성·의견 변경 (한정·부적정) 추적, 감사인 교체 빈도 점검.

    How:
        ``_safePivotAudit`` 의 years/opinions/auditors 매핑 후 직전과 비교.

    Requires:
        DART report.audit 수신.

    Raises:
        없음.

    Example:
        >>> calcAuditOpinionTrend(Company("005930"))
        {"history": [{"year": "...", "opinion": "적정", ...}]}

    SeeAlso:
        - ``calcOwnershipTrend``: 지배구조 시계열

    AIContext:
        AI 답변의 감사 안정성 인용 시.
    """
    result = _safePivotAudit(company)
    if result is None:
        return None

    years = result.years[-MAX_RATIO_YEARS:]
    opinions = result.opinions[-MAX_RATIO_YEARS:]
    auditors = result.auditors[-MAX_RATIO_YEARS:]

    history = []
    for i, y in enumerate(years):
        opinion = opinions[i] if i < len(opinions) else None
        auditor = auditors[i] if i < len(auditors) else None
        prevAuditor = auditors[i - 1] if i > 0 and (i - 1) < len(auditors) else None
        auditorChanged = auditor is not None and prevAuditor is not None and auditor != prevAuditor
        history.append(
            {
                "year": y,
                "opinion": opinion,
                "auditor": auditor,
                "auditorChanged": auditorChanged,
            }
        )

    return {"history": history} if history else None


# ── 플래그 ──


# ── 임원보수 괴리 ──


@memoizedCalc
def calcExecutivePayDivergence(company, *, basePeriod: str | None = None) -> dict | None:
    """임원 총보수 5Y 증가율 vs 매출/순이익 증가율 괴리.

    Capabilities:
        - 5 년 임원 총보수 CAGR 과 매출/순이익 CAGR 비교 + 괴리 (%p) 산출.

    Args:
        company: 분석 대상 기업.
        basePeriod: 기준 기간.

    Returns:
        dict | None: history (연도별 pay/매출/NI) + cagr 3 종 + divergence
        (execPay - revenue %p). 데이터 부족 시 None.

    Guide:
        divergence > 0 이면 실적 대비 임원보수가 빠르게 증가 — 거버넌스
        경고 신호.

    When:
        지배구조 보고서에서 경영진 인센티브 정렬 점검할 때.

    How:
        ``_safePivotExecutivePay`` 의 payByTypeDf 를 연도별 합산 후 IS 매출/
        순이익 매핑 → CAGR 계산.

    Requires:
        DART report.executive (보수 섹션) + IS sales/net_profit.

    Raises:
        없음.

    Example:
        >>> calcExecutivePayDivergence(Company("005930"))
        {"history": [...], "cagr": {...}, "divergence": 4.5}

    SeeAlso:
        - ``calcBoardComposition``: 이사회 구성

    AIContext:
        AI 답변에서 경영진 인센티브 정렬 인용 시.
    """
    pay = _safePivotExecutivePay(company)
    if pay is None or pay.payByTypeDf is None:
        return None

    import polars as pl

    df = pay.payByTypeDf
    if isEmptyDf(df):
        return None

    # category 합산 → year별 전체 임원보수
    try:
        yearly = df.group_by("year").agg(pl.col("totalPay").sum().alias("total")).sort("year")
        payByYear: dict[str, float] = {str(r["year"]): float(r["total"] or 0) for r in yearly.to_dicts()}
    except (KeyError, TypeError, ValueError, pl.exceptions.PolarsError):
        return None

    if not payByYear:
        return None

    # 매출/순이익 매핑
    from dartlab.core.utils.helpers import annualColsFromPeriods, toDictBySnakeId

    parsed = toDictBySnakeId(company.select("IS", ["sales", "net_profit"]))
    if parsed is None:
        return None
    isData, periods = parsed
    yCols = annualColsFromPeriods(periods, basePeriod=basePeriod, maxYears=5)

    # 분기 컬럼 → 연도 매핑 (annual cols: "2024" 혹은 "2024Q4")
    def _yearOf(col: str) -> str:
        """기간 컬럼에서 연도 4자리 추출."""
        return col[:4]

    salesRow = isData.get("sales", {})
    niRow = isData.get("net_profit", {})

    history = []
    years = sorted(payByYear.keys())[-5:]  # 최근 5년 pay 데이터 기준
    for y in years:
        col = next((c for c in yCols if _yearOf(c) == y), None)
        rev = salesRow.get(col) if col else None
        ni = niRow.get(col) if col else None
        history.append(
            {
                "year": y,
                "execPayTotal": payByYear.get(y),
                "revenue": rev,
                "netIncome": ni,
            }
        )

    if len(history) < 2:
        return None

    def _cagr(vals: list[float | None]) -> float | None:
        """양수 값 리스트에서 CAGR 산출 (%)."""
        vv = [v for v in vals if v is not None and v > 0]
        if len(vv) < 2:
            return None
        first, last = vv[0], vv[-1]
        n = len(vv) - 1
        return round(((last / first) ** (1 / n) - 1) * 100, 2) if n > 0 else None

    cagr = {
        "execPay": _cagr([h["execPayTotal"] for h in history]),
        "revenue": _cagr([h["revenue"] for h in history]),
        "netIncome": _cagr([h["netIncome"] for h in history]),
    }

    divergence = None
    if cagr["execPay"] is not None and cagr["revenue"] is not None:
        divergence = round(cagr["execPay"] - cagr["revenue"], 2)

    return {"history": history, "cagr": cagr, "divergence": divergence}


# ── 외부이사 독립성 ──


@memoizedCalc
def calcIndependentDirectorQuality(company, *, basePeriod: str | None = None) -> dict | None:
    """외부이사 독립성 — 비율 시계열 + 독립성 플래그.

    Capabilities:
        - 사외이사 비율 + 독립성 우려 한국어 flags 산출.

    Args:
        company: 분석 대상 기업.
        basePeriod: 기준 기간 (현재 미사용).

    Returns:
        dict | None: history (단일 latest 행 list) + latest (구성) + flags
        (한국어 경고 리스트). executive 미가용 시 None.

    Guide:
        flags 기준 — 25% 미만 취약 / 33% 미만 1/3 기준 미달 / 사외 ≤ 2 명
        + 전체 ≥ 6 명 절대수 부족.

    When:
        이사회 독립성 정성 평가가 필요할 때.

    How:
        ``_safePivotExecutive`` 결과 카운트 → 비율 계산 → 임계 비교.

    Requires:
        DART report.executive 수신.

    Raises:
        없음.

    Example:
        >>> calcIndependentDirectorQuality(Company("005930"))
        {"latest": {...}, "flags": [...]}

    SeeAlso:
        - ``calcBoardComposition``: 단순 비율 산출

    AIContext:
        AI 답변에서 독립성 우려 한 줄 인용 시.
    """
    from dartlab.core.utils.helpers import parseNumStr  # noqa: F401 (consistency)

    exec_ = _safePivotExecutive(company)
    if exec_ is None:
        return None

    # executivePayAllTotal / boardOfDirectors 등에서 연도별 구성이 제공될 수 있다
    # 간략히 현재 구성만 활용 — 시계열은 report.executive에 있는 경우만
    # totalCount/outsideCount 가 None 또는 0 이면 임원 구성 데이터 없음 → 분석 불가
    total = getattr(exec_, "totalCount", None)
    outside = getattr(exec_, "outsideCount", None)
    if not total:
        return None
    if outside is None:
        outside = 0  # 사외이사 정보 누락 — 0 가정 후 비율 0% (보수적 신호)

    ratio = round(outside / total * 100, 1)

    flags: list[str] = []
    if ratio < 25:
        flags.append(f"사외이사비율 {ratio:.0f}% — 이사회 독립성 취약 (25% 기준)")
    elif ratio < 33:
        flags.append(f"사외이사비율 {ratio:.0f}% — 독립성 기준(1/3) 미달")
    if outside <= 2 and total >= 6:
        flags.append(f"사외이사 {outside}명 — 절대수 부족")

    latest = {"total": total, "outside": outside, "ratio": ratio}
    return {
        "history": [{"year": "latest", "total": total, "outside": outside, "ratio": ratio}],
        "latest": latest,
        "flags": flags,
    }


def _safePivotExecutivePay(company):
    """report.executivePay를 안전하게 가져온다."""
    try:
        result = company._report.executivePay
        return result
    except (AttributeError, ValueError, KeyError, TypeError):
        return None


# ── 내부 헬퍼 ──


def _safePivotMajorHolder(company):
    """report.majorHolder를 안전하게 가져온다."""
    try:
        result = company._report.majorHolder
        if result is None:
            return None
        return result
    except (AttributeError, ValueError, KeyError, TypeError):
        return None


def _safePivotExecutive(company):
    """report.executive를 안전하게 가져온다."""
    try:
        result = company._report.executive
        if result is None:
            return None
        return result
    except (AttributeError, ValueError, KeyError, TypeError):
        return None


def _safePivotAudit(company):
    """report.audit를 안전하게 가져온다."""
    try:
        result = company._report.audit
        if result is None:
            return None
        return result
    except (AttributeError, ValueError, KeyError, TypeError):
        return None


# ── DART 전용 섹션 파이프라인 접근 ──


def _getDartStockCode(company) -> str | None:
    """DART Company에서 종목코드를 추출. EDGAR/다른 provider면 None.

    DART 전용 섹션 파이프라인(sanction, contingentLiability, relatedPartyTx)은
    사업보고서 parquet를 가정하므로 KRW 통화의 6자리 종목코드만 지원한다.
    """
    currency = getattr(company, "currency", None)
    if currency != "KRW":
        return None
    code = getattr(company, "stockCode", None) or getattr(company, "stock_code", None)
    # KRX 단축코드 (6자리 숫자 또는 숫자 선두 영숫자, 예 0008Z0)
    if not isinstance(code, str) or not isKrStockCode(code):
        return None
    return code


def _loadSanction(company):
    """제재 현황 — providers.dart.panel.text.panelXmlTables(panel '제재' 표) 재건. DART 외/데이터 없음 None."""
    code = _getDartStockCode(company)
    if not code:
        return None
    import polars as pl

    from dartlab.providers.dart.panel.text import panelXmlTables

    rows: list[dict] = []
    for t in panelXmlTables(code, sectionPattern="제재"):
        header = "".join(t[0]) if t else ""
        if "제재기관" not in header and "제재 기관" not in header:
            continue
        for r in t[1:]:
            if len(r) < 4 or not re.match(r"\d{4}", r[0] or ""):
                continue
            rows.append(
                {
                    "year": int(r[0][:4]),
                    "date": r[0],
                    "agency": r[1] if len(r) > 1 else "",
                    "subject": r[2] if len(r) > 2 else "",
                    "action": r[3] if len(r) > 3 else "",
                    "reason": r[5] if len(r) > 5 else "",
                    "amountValue": _parseKrwAmount(r[4]) if len(r) > 4 else None,
                }
            )
    if not rows:
        return None
    return SimpleNamespace(sanctionDf=pl.DataFrame(rows))


def _loadContingentLiability(company):
    """우발부채/지급보증 — providers.dart.panel.text.panelXmlTables(panel '우발부채' 표) 재건.

    소송(lawsuitDf)은 별도 표 부재 시 빈 DF, 지급보증(guaranteeDf)은 표 금액 best-effort 합산.
    """
    code = _getDartStockCode(company)
    if not code:
        return None
    import polars as pl

    from dartlab.providers.dart.panel.text import panelTextRows, panelXmlTables

    # 연도별 지급보증 총액 best-effort — '우발부채' 섹션 표 셀 중 원화 금액 합.
    texts = panelTextRows(code)
    guaranteeRows: list[dict] = []
    if texts is not None and not texts.is_empty():
        sub = texts.filter(pl.col("sectionLeaf").str.contains("우발"))
        for period in {p for p in sub["period"].to_list()}:
            if not (period[:4].isdigit()):
                continue
            total = 0
            for t in panelXmlTables(code, sectionPattern="우발", period=period):
                for r in t[1:]:
                    for cell in r:
                        amt = _parseKrwAmount(cell)
                        if amt and amt > 1_000_000:  # 백만원 이상만(노이즈 컷)
                            total += amt
            if total > 0:
                guaranteeRows.append({"year": int(period[:4]), "totalGuaranteeAmount": total})
    guaranteeDf = pl.DataFrame(guaranteeRows) if guaranteeRows else None
    lawsuitDf = None
    if guaranteeDf is None and lawsuitDf is None:
        return None
    return SimpleNamespace(guaranteeDf=guaranteeDf, lawsuitDf=lawsuitDf)


def _fetchLatestEquity(company, *, basePeriod: str | None = None) -> int | None:
    """BS에서 최근 연도 자기자본(total_equity)을 추출. 실패 시 None."""
    try:
        parsed = toDictBySnakeId(company.select("BS", ["total_equity"]))
    except (AttributeError, ValueError, KeyError, TypeError):
        return None
    if parsed is None:
        return None
    bsData, periods = parsed
    yCols = annualColsFromPeriods(periods, basePeriod=basePeriod, maxYears=1)
    if not yCols:
        return None
    row = bsData.get("total_equity", {})
    val = row.get(yCols[-1])
    try:
        return int(val) if val is not None else None
    except (TypeError, ValueError):
        return None


# ── 법적 이벤트 리스크 ──


# ── 오너 집중도 ──


def _loadExecutiveDocs(company):
    """임원 현황 — providers.dart.panel.text.panelXmlTables(panel '임원' 표) 재건. 표 부재 None."""
    code = _getDartStockCode(company)
    if not code:
        return None
    import polars as pl

    from dartlab.providers.dart.panel.text import panelXmlTables

    rows: list[dict] = []
    for t in panelXmlTables(code, sectionPattern="임원 및 직원"):
        header = "".join(t[0]) if t else ""
        if "성명" not in header and "직위" not in header and "직책" not in header:
            continue
        for r in t[1:]:
            if not r or not r[0]:
                continue
            rows.append({"name": r[0], "cells": " ".join(r[1:])})
    if not rows:
        return None
    return SimpleNamespace(executiveDf=pl.DataFrame(rows))


# ── 대표이사 교체 ──


CEO_TURNOVER_WINDOW_YEARS = 5


def _loadRelatedPartyTx(company):
    """특수관계자 거래 — providers.dart.panel.text.panelXmlTables(panel '특수관계자' 표) 재건. 표 부재 None."""
    code = _getDartStockCode(company)
    if not code:
        return None
    import polars as pl

    from dartlab.providers.dart.panel.text import panelXmlTables

    entities: list[dict] = []
    for t in panelXmlTables(code, sectionPattern="특수관계자"):
        for r in t[1:]:
            ent = (r[0] or "").strip() if r else ""
            if ent and ent not in ("기초", "기말", "소계", "합계", "구분"):
                entities.append({"entity": ent})
    if not entities:
        return None
    return SimpleNamespace(revenueTxDf=pl.DataFrame(entities), guaranteeDf=None)


# ── 특수관계자 거래 집중도 ──


RELATED_PARTY_PARSER_UNIT = 1_000_000  # 사업보고서 표준 단위(백만원) → 원


LEGAL_EVENT_WINDOW_YEARS = 3


# 분리된 깊이 분석 (BC re-export)
from dartlab.analysis.financial._governanceDeep import (  # noqa: E402, F401
    calcCEOTurnover,
    calcGovernanceFlags,
    calcLegalEventRisk,
    calcOwnerConcentration,
    calcRelatedPartyIntensity,
)
