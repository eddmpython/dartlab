"""Story Validation. Damodaran *Narrative and Numbers* 검증.

스토리의 타당성은 3단계 테스트를 통과해야 한다:

1. Possible (History). 과거 유사 사례가 있는가
2. Plausible (Experience). 유사 경로에서 실제로 달성된 수치 분포 안에 있는가
3. Probable (Common Sense). 수학/경제 첫 원칙에 부합하는가

엔진은 dict 만 반환. 해석 문장은 story narrate 층.
새 엔진 만들지 않고 scan/KnowledgeDB/consistency 기존 자산 조합.
"""

from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger(__name__)


def calcStoryPrecedents(
    company: Any = None,
    *,
    basePeriod: str | None = None,
    stockCode: str | None = None,
    lifeCyclePhase: str | None = None,
    sectorCode: str | None = None,
    limit: int = 5,
    skipIfScanMissing: bool = True,
) -> dict[str, Any]:
    """Possible Test. 유사 경로 기업 수집 (scan + KnowledgeDB insights).

    Phase 4 G15b: skipIfScanMissing=True 기본. scan 프리빌드 (271MB) 미다운로드 시
    즉시 skip 반환. AI 대화 첫 호출에서 강제 다운로드로 인한 timeout 방지.

    Capabilities:
        - 유사 sector/lifeCycle 기업 narrative + outcome 코퍼스 수집.

    Guide:
        스토리 검증 1 단계. 비슷한 경로 회사의 결말을 사례로 본다.

    When:
        "이 회사 시나리오, 비슷한 사례 있나?" 의도 진입 시.

    How:
        scan parquet + KnowledgeDB sector insights → 유사도 정렬 후 limit.

    Requires:
        scan finance.parquet (271MB) 또는 KnowledgeDB 인덱스.

    Raises:
        없음 (스킵 시 hint 포함 dict).

    Example:
        >>> calcStoryPrecedents(c, limit=3)["count"]
        3

    See Also:
        - calcPlausibilityBand : 시나리오 가능 폭
        - calcValuationSins : 밸류 모델 오류 패턴

    AIContext:
        AI 답변 "비슷한 경로 N 개" 카드의 코퍼스 공급원.

    Returns
    -------
    dict
        precedents : list[dict{stockCode, name, narrative, outcome, similarity}]
        count : int
        confidence : str. "low" | "mid" | "high"
        source : str. 데이터 경로 요약
    """
    # Phase 4 G15b: scan 프리빌드 없으면 강제 다운로드 회피. AI timeout 방지
    if skipIfScanMissing:
        from pathlib import Path

        scan_path = Path("data/dart/scan/finance.parquet")
        if not scan_path.exists():
            return {
                "precedents": [],
                "count": 0,
                "confidence": "low",
                "source": "scan_not_downloaded",
                "hint": "scan 프리빌드 또는 collect 데이터 준비 후 재시도",
            }

    # company 객체에서 기본값 추출
    if company is not None:
        if stockCode is None:
            stockCode = getattr(company, "stockCode", None)
        if sectorCode is None:
            sec = getattr(company, "sector", None)
            if sec:
                sectorCode = getattr(sec, "code", None) or getattr(sec, "sector", None)
        if lifeCyclePhase is None:
            try:
                from dartlab.analysis.financial.lifeCycle import calcLifeCycle

                lc = calcLifeCycle(company, basePeriod=basePeriod)
                if lc:
                    lifeCyclePhase = lc.get("phase")
            except (ImportError, AttributeError, ValueError, TypeError):
                pass

    precedents: list[dict] = []
    sources: list[str] = []

    # (옛 KnowledgeDB insights 경로 제거. `dartlab.ai.persistence` 모듈이 부재해 import 가
    # 항상 실패하던 silent no-op 였고, analysis(L2)→ai(L4) 역방향 의존이라 부활도 레이어 위반.
    # precedent 는 아래 scan peer 경로로만 수집한다. debt-honesty P2-4 / PH-4)

    # scan peer. 동일 lifeCyclePhase 기업 (phase 기반 precedent)
    if lifeCyclePhase and stockCode:
        try:
            phase_peers = _findPhaseMatchingPeers(stockCode, lifeCyclePhase, limit=limit)
            for p in phase_peers:
                precedents.append(p)
            if phase_peers:
                sources.append("scan_phase_match")
        except (ImportError, AttributeError, TypeError, ValueError, OSError):
            pass

    count = len(precedents)
    if count >= 5:
        confidence = "high"
    elif count >= 2:
        confidence = "mid"
    else:
        confidence = "low"

    return {
        "precedents": precedents[:limit],
        "count": count,
        "confidence": confidence,
        "source": ",".join(sources) if sources else "none",
    }


# 판정 문구에 이미 나가 있는 긴 줄표 (U+2014). 문구가 곧 반환 계약이라 바꾸지 않고,
# 소스에는 리터럴을 남기지 않으려 코드포인트로 고정한다 (신규 문구에는 쓰지 않는다).
# scan finance.parquet 에서 한 종목의 매출·영업이익을 찾을 때 쓰는 계정명 우선순위.
_REVENUE_ACCOUNT_NAMES = ["매출액", "수익(매출액)", "영업수익"]
_OPERATING_ACCOUNT_NAMES = ["영업이익", "영업이익(손실)"]

# scan snapshot 에서 읽고 싶은 컬럼. 실제 파일에 있는 것만 골라 select 한다.
_SCAN_COLUMNS = [
    "stockCode",
    "bsns_year",
    "sj_div",
    "account_nm",
    "thstrm_amount",
    "frmtrm_amount",
    "fs_nm",
    "reprt_nm",
]


def _stockAmounts(pl, stock, parseNumStr):
    """한 종목 행묶음에서 (당기 매출, 전기 매출, 당기 영업이익) 을 뽑는다.

    peer 탐색과 분포 표본 수집 두 곳이 계정명 우선순위 순회를 똑같이 반복하고 있었다.
    계정명이 없으면 그 자리는 None 으로 남는다.
    """
    revCur = revPrev = opCur = None
    for nm in _REVENUE_ACCOUNT_NAMES:
        r = stock.filter(pl.col("account_nm") == nm)
        if not r.is_empty():
            revCur = parseNumStr(r["thstrm_amount"][0])
            if "frmtrm_amount" in r.columns:
                revPrev = parseNumStr(r["frmtrm_amount"][0])
            break
    for nm in _OPERATING_ACCOUNT_NAMES:
        o = stock.filter(pl.col("account_nm") == nm)
        if not o.is_empty():
            opCur = parseNumStr(o["thstrm_amount"][0])
            break
    return revCur, revPrev, opCur


_PHASE_SIGNATURES = {
    "earlyGrowth": {"growthMin": 30, "marginMax": 5},
    "highGrowth": {"growthMin": 15, "growthMax": 35, "marginMin": 0},
    "matureGrowth": {"growthMin": 5, "growthMax": 20, "marginMin": 3},
    "matureStable": {"growthMax": 8, "marginMin": 5},
    "decline": {"growthMax": 0},
    "turnaround": {"growthMin": -5, "growthMax": 15, "marginMin": -5},
}


def _findPhaseMatchingPeers(stockCode: str, phase: str, *, limit: int = 5) -> list[dict]:
    """scan/finance.parquet 에서 같은 lifeCyclePhase signature 를 가진 기업 추출.

    완벽한 phase 계산은 무거우므로 growth/margin signature 로 근사.
    """
    sig = _PHASE_SIGNATURES.get(phase)
    if not sig:
        return []

    try:
        import importlib

        import polars as pl

        _h = importlib.import_module("dartlab.scan.io.parquet")
        _ensureScanData = _h._ensureScanData
        parseNumStr = _h.parseNumStr
    except ImportError:
        return []

    scan_dir = _ensureScanData()
    path = scan_dir / "finance.parquet"
    if not path.exists():
        return []

    try:
        lf = pl.scan_parquet(str(path))
        avail = lf.collect_schema().names()
        cols = [c for c in _SCAN_COLUMNS if c in avail]
        snap = (
            lf.select(cols)
            .filter(pl.col("fs_nm").str.contains("연결"))
            .filter(pl.col("reprt_nm").str.contains("4분기"))
            .collect(engine="streaming")
        )
    except (pl.exceptions.PolarsError, OSError):
        return []
    if snap.is_empty():
        return []

    years = sorted(snap["bsns_year"].unique().to_list(), reverse=True)
    if not years:
        return []
    cur = snap.filter(pl.col("bsns_year") == years[0])

    matches: list[dict] = []
    for sc in cur["stockCode"].unique().to_list():
        if sc == stockCode:
            continue
        stock = cur.filter(pl.col("stockCode") == sc)
        if stock.is_empty():
            continue
        rev_cur, rev_prev, op_cur = _stockAmounts(pl, stock, parseNumStr)
        if not (rev_cur and rev_prev and rev_prev > 0):
            continue
        yoy = (rev_cur - rev_prev) / rev_prev * 100
        margin = op_cur / rev_cur * 100 if (op_cur is not None and rev_cur > 0) else None

        if not _matchesPhaseSignature(sig, yoy, margin):
            continue

        matches.append(
            {
                "stockCode": sc,
                "name": sc,
                "narrative": f"YoY {yoy:.1f}%, 영업마진 {margin:.1f}%" if margin is not None else f"YoY {yoy:.1f}%",
                "outcome": None,
                "similarity": None,
                "source": "scan_phase_match",
            }
        )
        if len(matches) >= limit:
            break
    return matches


def _matchesPhaseSignature(sig: dict, yoy: float, margin: float | None) -> bool:
    """성장률·마진이 phase signature 의 상하한 안에 드는지. 키가 없는 조건은 통과."""
    if "growthMin" in sig and yoy < sig["growthMin"]:
        return False
    if "growthMax" in sig and yoy > sig["growthMax"]:
        return False
    if "marginMin" in sig and (margin is None or margin < sig["marginMin"]):
        return False
    if "marginMax" in sig and (margin is None or margin > sig["marginMax"]):
        return False
    return True


def calcPlausibilityBand(
    company: Any = None,
    *,
    basePeriod: str | None = None,
    stockCode: str | None = None,
    forecastAssumptions: dict[str, Any] | None = None,
    sectorCode: str | None = None,
) -> dict[str, Any]:
    """Plausible Test. 현재 forecast 가정이 섹터 피어 분포 어디에 위치하는지.

    Capabilities:
        - 성장률/마진 가정의 피어 분포 percentile + 밴드 판정.

    Guide:
        within (p25~p75) / stretch (p75~p95) / unrealistic (>p95).

    When:
        forecast 입력값이 "현실적인지" 검증 요청 시.

    How:
        scan finance.parquet 샘플 500 → growth/margin 분포 → percentile.

    Requires:
        scan finance.parquet + forecastAssumptions or growthTrend.

    Raises:
        없음 (예외는 try/except 흡수 → source="none").

    Example:
        >>> calcPlausibilityBand(c, forecastAssumptions={"growthRate": 12})["band"]
        "stretch"

    See Also:
        - calcStoryPrecedents : 사례 코퍼스
        - calcValuationSins : 모델 오류 패턴

    AIContext:
        AI "가정 검증" 답변에서 stretch/unrealistic 라벨 표시에 사용.

    Returns
    -------
    dict
        growthPercentile : float | None. 0.0~100.0
        marginPercentile : float | None
        band : str. "within" (p25~p75) | "stretch" (p75~p95) | "unrealistic" (>p95)
        peerStats : dict. {growthMedian, growthP75, growthP95, marginMedian, ...}
        source : str
    """
    if company is not None and stockCode is None:
        stockCode = getattr(company, "stockCode", None)
    if company is not None and sectorCode is None:
        sec = getattr(company, "sector", None)
        if sec:
            sectorCode = getattr(sec, "code", None) or getattr(sec, "sector", None)
    if forecastAssumptions is None:
        forecastAssumptions = _inferForecastAssumptions(company, basePeriod)

    growth = forecastAssumptions.get("growthRate") or forecastAssumptions.get("revenueGrowth")
    op_margin = forecastAssumptions.get("operatingMargin") or forecastAssumptions.get("opm")

    peer_growth, peer_margin = _peerGrowthMarginSamples()

    growth_pctile = _percentile(peer_growth, growth)
    margin_pctile = _percentile(peer_margin, op_margin)

    band = "within"
    if growth_pctile is not None:
        if growth_pctile > 95:
            band = "unrealistic"
        elif growth_pctile > 75:
            band = "stretch"

    return {
        "growthPercentile": growth_pctile,
        "marginPercentile": margin_pctile,
        "band": band,
        "peerStats": {
            "growthMedian": _quantile(peer_growth, 0.5),
            "growthP75": _quantile(peer_growth, 0.75),
            "growthP95": _quantile(peer_growth, 0.95),
            "marginMedian": _quantile(peer_margin, 0.5),
            "marginP75": _quantile(peer_margin, 0.75),
            "count": len(peer_growth),
        },
        "source": "scan_peer" if peer_growth else "none",
    }


def _inferForecastAssumptions(company: Any, basePeriod: str | None) -> dict[str, Any]:
    """company 에서 성장률·마진 가정을 추론한다 (growthTrend CAGR + 최근 마진).

    가정을 못 얻어도 밴드 판정 자체는 돌아야 해서 실패는 빈 dict 로 접는다.
    """
    assumptions: dict[str, Any] = {}
    if company is None:
        return assumptions
    try:
        from dartlab.analysis.financial.growthAnalysis import calcGrowthTrend
        from dartlab.analysis.financial.profitability import calcMarginTrend

        g = calcGrowthTrend(company, basePeriod=basePeriod)
        m = calcMarginTrend(company, basePeriod=basePeriod)
        if g:
            assumptions["growthRate"] = (g.get("cagr") or {}).get("revenue")
        if m and m.get("history"):
            assumptions["operatingMargin"] = m["history"][0].get("operatingMargin")
    except (ImportError, AttributeError, ValueError, TypeError):
        pass
    return assumptions


def _peerGrowthMarginSamples() -> tuple[list[float], list[float]]:
    """scan/finance.parquet 직접 쿼리 → 전종목 매출 YoY + 영업마진 분포.

    표본이 없어도 밴드 판정은 "within" 으로 돌아가야 하므로 준비 실패는 전부 흡수하고
    빈 표본을 돌려준다. 극단값 컷 (-80~300%, -100~80%) 은 분포 왜곡 방지용이다.
    """
    peerGrowth: list[float] = []
    peerMargin: list[float] = []
    try:
        import importlib

        import polars as pl

        _h = importlib.import_module("dartlab.scan.io.parquet")
        _ensureScanData = _h._ensureScanData
        parseNumStr = _h.parseNumStr

        scan_dir = _ensureScanData()
        path = scan_dir / "finance.parquet"
        if path.exists():
            lf = pl.scan_parquet(str(path))
            avail = lf.collect_schema().names()
            cols = [c for c in _SCAN_COLUMNS if c in avail]
            snap = (
                lf.select(cols)
                .filter(pl.col("fs_nm").str.contains("연결"))
                .filter(pl.col("reprt_nm").str.contains("4분기"))
                .collect(engine="streaming")
            )
            if not snap.is_empty():
                years = sorted(snap["bsns_year"].unique().to_list(), reverse=True)
                if years:
                    cur = snap.filter(pl.col("bsns_year") == years[0])
                    stockcodes = [s for s in cur["stockCode"].unique().to_list() if s is not None]
                    for sc in stockcodes[:500]:  # 샘플 500 (메모리 + 속도)
                        stock = cur.filter(pl.col("stockCode") == sc)
                        if stock.is_empty():
                            continue
                        # 매출 + 영업이익 현재기/전기 추출
                        rev_cur, rev_prev, op_cur = _stockAmounts(pl, stock, parseNumStr)
                        # YoY
                        if rev_cur and rev_prev and rev_prev > 0:
                            yoy = (rev_cur - rev_prev) / rev_prev * 100
                            if -80 < yoy < 300:
                                peerGrowth.append(float(yoy))
                        # Margin
                        if rev_cur and op_cur is not None and rev_cur > 0:
                            margin = op_cur / rev_cur * 100
                            if -100 < margin < 80:
                                peerMargin.append(float(margin))
    except Exception as exc:
        log.warning("peer 성장률 및 마진 표본 준비 실패: %s: %s", type(exc).__name__, exc)
    return peerGrowth, peerMargin


def _percentile(series: list[float], value: float | None) -> float | None:
    """시리즈 내 값의 백분위 위치 산출 (0~100)."""
    if value is None or not series:
        return None
    below = sum(1 for x in series if x < value)
    return round(below / len(series) * 100, 1)


def _quantile(series: list[float], q: float) -> float | None:
    """시리즈에서 q 분위수 값 추출."""
    if not series:
        return None
    sorted_s = sorted(series)
    idx = int(q * (len(sorted_s) - 1))
    return round(sorted_s[idx], 2)


def calcValuationSins(
    company: Any = None,
    *,
    basePeriod: str | None = None,
    valuation: dict[str, Any] | None = None,
    peerStats: dict[str, Any] | None = None,
    roicPct: float | None = None,
    waccPct: float | None = None,
    operatingMarginPct: float | None = None,
    country: str | None = None,
    currency: str | None = None,
) -> dict[str, Any]:
    """Probable Test. 경제·수학 첫 원칙 위반 규칙 순회.

    `consistency.calcCashFlowConsistency` 와 구별: consistency 는 **가정 간 매칭**,
    이쪽은 **경쟁 수렴 / 마진 상한 / 서사-숫자 갭 등 정성적 판단 규칙** 까지 포함.

    Capabilities:
        - ROIC-WACC · 마진 상한 · 영구성장 등 valuation 7 죄 검출.

    Guide:
        info/warn/critical severity + suggestedRetry 함께 반환.

    When:
        DCF 결과를 사용자에게 보여주기 직전 sanity check 단계.

    How:
        valuation dict + ROIC/WACC/마진 → 룰 7 종 순회 → flags.

    Requires:
        valuation 결과 (dFV) + ROIC/마진 timeline.

    Raises:
        없음 (소스 부재 시 빈 flags).

    Example:
        >>> calcValuationSins(c, roicPct=8, waccPct=12)["severity"]
        "warn"

    See Also:
        - calcPlausibilityBand : 가정 분포 검증
        - valuation.consistency : 가정 간 매칭

    AIContext:
        AI 가 valuation 모델 사용자에게 "이 가정 위험" 경고 출력 시 인용.

    Returns
    -------
    dict
        flags : list[dict{key, severity, reason, suggestedRetry}]
        severity : str. 전체 최고 (info/warn/critical)
        count : int
    """
    from dartlab.analysis.valuation.consistency import calcCashFlowConsistency

    # company 에서 자동 추출
    valuation, roicPct, waccPct, operatingMarginPct, currency = _valuationInputsFromCompany(
        company,
        basePeriod,
        valuation,
        roicPct,
        waccPct,
        operatingMarginPct,
        currency,
    )

    # consistency 호출 (수학적 정합성은 거기서)
    consistency = calcCashFlowConsistency(
        valuation=valuation,
        roicPct=roicPct,
        waccPct=waccPct,
        country=country,
        currency=currency,
    )

    flags: list[dict] = []

    # consistency 결과를 flags 에 흡수
    for f in consistency.get("flags", []):
        flags.append(
            {
                "key": f.get("rule"),
                "severity": f.get("severity"),
                "reason": f.get("message"),
                "suggestedRetry": None,
            }
        )

    # 추가 규칙 4 종. 룰끼리 의존이 없어 각자 자기 게이트를 들고 dict 또는 None 을 낸다.
    for rule in (
        _roicWaccPersistFlag(roicPct, waccPct),
        _marginCeilingFlag(peerStats, operatingMarginPct),
        _storyNumbersGapFlag(valuation),
        _controlSynergyOverlapFlag(valuation),
    ):
        if rule is not None:
            flags.append(rule)

    return {
        "flags": flags,
        "severity": _maxSeverity(flags),
        "count": len(flags),
    }


def _valuationInputsFromCompany(
    company: Any,
    basePeriod: str | None,
    valuation: dict[str, Any] | None,
    roicPct: float | None,
    waccPct: float | None,
    operatingMarginPct: float | None,
    currency: str | None,
) -> tuple:
    """비어 있는 valuation 입력만 company 에서 채운다. 이미 주어진 인자는 건드리지 않는다."""
    if company is None:
        return valuation, roicPct, waccPct, operatingMarginPct, currency

    if currency is None:
        currency = getattr(company, "currency", None)
    if valuation is None:
        try:
            from dartlab.analysis.valuation.dFV import calcDFV

            valuation = calcDFV(company, basePeriod=basePeriod)
        except (ImportError, AttributeError, ValueError, TypeError):
            pass
    if roicPct is None or operatingMarginPct is None:
        try:
            from dartlab.analysis.financial.investmentAnalysis import calcRoicTimeline
            from dartlab.analysis.financial.profitability import calcMarginTrend

            r = calcRoicTimeline(company, basePeriod=basePeriod)
            if r and r.get("history"):
                roicPct = roicPct if roicPct is not None else r["history"][0].get("roic")
                if waccPct is None:
                    waccPct = r["history"][0].get("waccEstimate")
            m = calcMarginTrend(company, basePeriod=basePeriod)
            if m and m.get("history"):
                operatingMarginPct = (
                    operatingMarginPct if operatingMarginPct is not None else m["history"][0].get("operatingMargin")
                )
        except (ImportError, AttributeError, ValueError, TypeError):
            pass
    return valuation, roicPct, waccPct, operatingMarginPct, currency


def _roicWaccPersistFlag(roicPct: float | None, waccPct: float | None) -> dict | None:
    """경쟁 수렴 위반: ROIC 가 WACC 의 3 배를 넘는 상태를 영구 가정."""
    if not (roicPct is not None and waccPct is not None and waccPct > 0):
        return None
    ratio = roicPct / waccPct
    if not (ratio > 3.0):
        return None
    return {
        "key": "roic_wacc_persist",
        "severity": "warn",
        "reason": (f"ROIC {roicPct:.1f}% / WACC {waccPct:.1f}% = {ratio:.1f}x. 장기 경쟁 수렴 가정 위반"),
        "suggestedRetry": {"terminalGrowth": 2.0},
    }


def _marginCeilingFlag(peerStats: dict[str, Any] | None, operatingMarginPct: float | None) -> dict | None:
    """마진 상한: 업종 상위 기준치의 1.5 배 초과."""
    if not (peerStats and operatingMarginPct is not None):
        return None
    p95 = peerStats.get("marginP75") or peerStats.get("marginMedian")
    if not (isinstance(p95, (int, float)) and p95 > 0 and operatingMarginPct > p95 * 1.5):
        return None
    return {
        "key": "margin_ceiling",
        "severity": "warn",
        "reason": f"영업마진 {operatingMarginPct:.1f}% 가 업종 상위 기준치 {p95:.1f}% 의 1.5배 초과",
        "suggestedRetry": None,
    }


def _storyNumbersGapFlag(valuation: dict[str, Any] | None) -> dict | None:
    """스토리 ↔ 숫자 갭: storyTemplate 없이 valuation 을 돌린 경우."""
    if not (valuation and not valuation.get("companyType")):
        return None
    return {
        "key": "story_numbers_gap",
        "severity": "info",
        "reason": "기업유형 미판정. 서사 없는 숫자, Damodaran 원칙 위반",
        "suggestedRetry": None,
    }


def _controlSynergyOverlapFlag(valuation: dict[str, Any] | None) -> dict | None:
    """Control + Synergy 이중계산 (Damodaran Dark Side Ch.17)."""
    if not valuation:
        return None
    cp = valuation.get("controlPremium") or (valuation.get("control") or {}).get("controlPremium")
    syn = valuation.get("synergy") or (valuation.get("synergy") or {}).get("synergy")
    sq = valuation.get("dFV") or valuation.get("statusQuoValue")
    if not (isinstance(cp, (int, float)) and isinstance(syn, (int, float)) and isinstance(sq, (int, float)) and sq > 0):
        return None
    if not ((cp + syn) > sq * 0.5):
        return None
    return {
        "key": "control_synergy_overlap",
        "severity": "critical",
        "reason": (
            f"Control premium {cp:,.0f} + Synergy {syn:,.0f} = {cp + syn:,.0f}"
            f" 이 standalone {sq:,.0f} × 50% 초과. 이중계산 위험"
        ),
        "suggestedRetry": None,
    }


def _maxSeverity(flags: list[dict]) -> str:
    """flags 중 가장 높은 severity (info < warn < critical)."""
    severity = "info"
    order = {"info": 0, "warn": 1, "critical": 2}
    for f in flags:
        if order.get(f.get("severity", "info"), 0) > order.get(severity, 0):
            severity = f["severity"]
    return severity
