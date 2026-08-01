"""횡단면 팩터 시계열 빌드. 진짜 시총 기반 SMB/HML/RMW/CMA (Fama-French 표준).

KR (2026-04-24 Phase B0 정정): KRX OpenAPI ``MKTCAP`` 컬럼 직접 사용 → 진짜 시총 기반
SMB (small-minus-big), HML (high-BM-minus-low-BM, BM = equity/marketCap). audit (2026-04-06)
의 −0.51 상관 폐기 사례 해결.

US (EDGAR): 시총 데이터 미수집 → fallback book-equity proxy 유지.

학술 정의:
- SMB = small marketCap 종목 평균 - big marketCap 종목 평균 (Fama-French 1992 원본)
- HML = high BM (= equity / marketCap) 종목 평균 - low BM 종목 평균
- RMW = high ROE 종목 평균 - low ROE 종목 평균 (Asness 정의)
- CMA = conservative (low asset growth) 종목 평균 - aggressive 종목 평균 (Fama-French 2015)

데이터 흐름 (KR):
1. `_build_universe_metrics`: DART finance.parquet 단년도 펀더멘털 + KRX 연도말 시총 (`marketCapAll`)
2. `_quintile_portfolios`: 5분위 상위/하위 (각 ~20%)
3. `_portfolio_returns`: 동일가중 일별 log return
4. `buildFactors`: SMB/HML/RMW/CMA 시계열

빌드된 시계열은 캐시되며, factor.py 의 decomposeFactor 가 회귀 입력으로 사용한다.
calcFactorTearSheet 도 이걸 IC/ICIR/분위 평가에 사용.
"""

from __future__ import annotations

import logging

import numpy as np
import polars as pl

from dartlab.core.polarsUtil import isEmptyDf
from dartlab.quant.screen.dataAccess import (
    extractAccount,
    fetchOhlcv,
    loadScanParquet,
    ohlcvToArrays,
)
from dartlab.synth.scanBridge import extractAnnualConsolidated, isEdgarSchema

log = logging.getLogger(__name__)


_FACTOR_CACHE: dict[tuple[str, str], dict] = {}
_PORTFOLIO_CACHE: dict[tuple[str, str, int], np.ndarray] = {}

# 팩터 형성 시점 규약. 같은 패키지의 `_factorIC.calcFactorIC` 와 같은 규약이다.
# FY Y-1 재무는 Y 년 3 월경 공시되므로, 그 정보로 가른 포트폴리오에 귀속시킬 수 있는
# 수익률은 4 월 1 일부터다. 연초부터 담으면 정렬 정보보다 앞선 수익률이 섞인다.
_RETURN_WINDOW_START = "04-01"
_RETURN_WINDOW_END = "12-31"


def _latestYear(snap: pl.DataFrame, minCount: int = 1000) -> str | None:
    """충분한 universe를 가진 가장 최근 연도."""
    if snap.is_empty():
        return None
    yearCol = "fy" if isEdgarSchema(snap) else "bsns_year"
    # DART finance.parquet 은 회사-연도당 여러 계정 행을 가진 long-form 이다.
    # 행 수를 universe 로 세면 회사 한 곳의 계정 1,000개만으로도 최신 연도가
    # 선택된다. 실제 횡단면 표본인 고유 종목 수로만 완전 연도를 판정한다.
    counts = snap.group_by(yearCol).agg(pl.col("stockCode").n_unique().alias("len")).sort(yearCol, descending=True)
    for row in counts.iter_rows(named=True):
        if row["len"] >= minCount:
            y = row[yearCol]
            return str(y) if y is not None else None
    return None


def _fetchYearEndMarketcaps(market: str, year: str, *, asof: str | None = None) -> dict[str, float]:
    """연도말 (12월 마지막 거래일) 종목별 시가총액.

    KR: KRX OpenAPI ``MKTCAP`` 컬럼 직접 (gather/_hfBulk.loadFiltered).
    US: EDGAR 시총 미수집 → 빈 dict (fallback 으로 book equity proxy 사용).

    Args:
        market: 시장 코드 (현재 KR 만 지원).
        year: 연도 (str).
        asof: Sprint 4 PIT 컷오프 (default None → 기존 동작). bitemporal HF 활성 후 의미 있음.

    Returns:
        {stockCode: marketCap (원)}. 연도말 마지막 거래일 기준.
    """
    if market != "KR":
        return {}
    try:
        from dartlab.gather.bulkData.hfBulk import loadFiltered

        # 연말 ~6일 (12-25 ~ 12-31) 중 마지막 거래일 시총 사용 (휴일 robust)
        long_df = loadFiltered(
            start=f"{year}-12-25",
            end=f"{year}-12-31",
            adjustment="raw",
            asof=asof,
        )
        if long_df is None or long_df.is_empty():
            log.info("factorBuild: 연도말 시총 부재 (year=%s), book proxy fallback", year)
            return {}
        # 종목별 마지막 일자 시총 (descending sort 후 첫 row keep)
        latest = (
            long_df.sort("BAS_DD", descending=True).unique(subset=["ISU_CD"], keep="first").select(["ISU_CD", "MKTCAP"])
        )
        return {
            row["ISU_CD"]: float(row["MKTCAP"])
            for row in latest.iter_rows(named=True)
            if row.get("MKTCAP") is not None and row["MKTCAP"] > 0
        }
    except Exception as exc:
        log.warning("factorBuild: 시총 fetch 실패 (year=%s): %s", year, type(exc).__name__)
        return {}


def _buildUniverseMetrics(market: str, year: str) -> dict[str, dict[str, float]]:
    """전종목 단년도 펀더멘털 + 시총 dict.

    Returns:
        {stockCode: {bookEquity, marketCap, totalAssets, netIncome, roe, bookRatio,
                     bookToMarket, assetGrowth}}
        - marketCap: KRX MKTCAP (KR), None (US 미수집)
        - bookToMarket: equity / marketCap (진짜 BM, 시총 있을 때만)
        - bookRatio: equity / assets (자본구조, fallback 용)
    """
    lf = loadScanParquet("finance", market)
    if lf is None:
        return {}

    snap = extractAnnualConsolidated(lf.collect(engine="streaming"))
    if snap.is_empty():
        return {}

    edgar = isEdgarSchema(snap)
    yearCol = "fy" if edgar else "bsns_year"
    year_val = int(year) if edgar else year
    cur = snap.filter(pl.col(yearCol) == year_val)
    # 전기 (asset growth용)
    try:
        prev_year_val = int(year) - 1
    except ValueError:
        prev_year_val = None
    if prev_year_val is not None:
        pv = prev_year_val if edgar else str(prev_year_val)
        prev = snap.filter(pl.col(yearCol) == pv)
    else:
        prev = None

    # 연도말 시총 (KR 만 채워짐)
    market_caps = _fetchYearEndMarketcaps(market, year)

    out: dict[str, dict[str, float]] = {}
    # 성능 fix (G5): partition_by 한 번 호출 → O(n) lookup. 기존 filter 는 O(n²) 라
    # n=2000 종목에서 5분 timeout 유발 (qFactor / qmj 등 _build_universe_metrics 의존 모듈).
    cur_parts = cur.partition_by("stockCode", as_dict=True)
    prev_parts = prev.partition_by("stockCode", as_dict=True) if prev is not None else {}
    for code_key, stock in cur_parts.items():
        code = code_key[0] if isinstance(code_key, tuple) else code_key
        if not isinstance(code, str) or stock.is_empty():
            continue

        equity = extractAccount(stock, "total_equity")
        assets = extractAccount(stock, "total_assets")
        ni = extractAccount(stock, "net_income")
        if not equity or not assets or equity <= 0 or assets <= 0:
            continue

        roe = (ni / equity) if ni is not None else None
        book_ratio = equity / assets

        asset_growth = None
        prev_stock = prev_parts.get(code_key)
        if prev_stock is not None and not prev_stock.is_empty():
            prev_assets = extractAccount(prev_stock, "total_assets")
            if prev_assets and prev_assets > 0:
                asset_growth = (assets - prev_assets) / prev_assets

        mc = market_caps.get(code)
        book_to_market = (equity / mc) if (mc is not None and mc > 0) else None

        out[code] = {
            "bookEquity": float(equity),
            "marketCap": float(mc) if mc is not None else None,
            "totalAssets": float(assets),
            "netIncome": float(ni) if ni is not None else None,
            "roe": float(roe) if roe is not None else None,
            "bookRatio": float(book_ratio),
            "bookToMarket": float(book_to_market) if book_to_market is not None else None,
            "assetGrowth": float(asset_growth) if asset_growth is not None else None,
        }
    return out


def _quintilePortfolios(metrics: dict[str, dict[str, float]], key: str, reverse: bool) -> tuple[list[str], list[str]]:
    """지표 5분위 → 상위 20% / 하위 20% 종목군.

    reverse=True면 상위가 작은 값.
    """
    items = [(c, m[key]) for c, m in metrics.items() if m.get(key) is not None]
    if len(items) < 50:
        return [], []
    items.sort(key=lambda x: x[1], reverse=reverse)
    n = len(items)
    cutoff = max(int(n * 0.2), 10)
    top = [c for c, _ in items[:cutoff]]
    bot = [c for c, _ in items[-cutoff:]]
    return top, bot


def _portfolioReturns(codes: list[str], market: str, year: str, maxN: int = 30) -> np.ndarray | None:
    """종목 리스트의 동일가중 평균 일별 log return 시계열.

    ``year`` 는 수익률 연도다. 구간은 ``_RETURN_WINDOW_START`` 부터라서 형성 시점보다
    앞선 수익률이 섞이지 않는다. 연초부터 담으면 아직 공시되지 않은 재무로 가른
    포트폴리오에 그 이전 수익률을 귀속시키게 된다.

    KR (Phase B0 정정): `_hfBulk.loadFiltered` 직접 사용 (Yahoo 우회 + 빠름).
    한 번에 종목 리스트 long fetch 후 group_by. 메모리 안전 + 1 query.

    US: 기존 fetchOhlcv (Yahoo) 유지.

    캐시: (market, year, hash(codes))
    """
    if not codes:
        return None
    key = (market, year, hash(tuple(sorted(codes[:maxN]))))
    if key in _PORTFOLIO_CACHE:
        return _PORTFOLIO_CACHE[key]

    rets = []
    if market == "KR":
        # KR: _hfBulk 한 번 호출로 종목 리스트 long fetch
        try:
            from dartlab.gather.bulkData.hfBulk import loadFiltered

            target_codes = codes[:maxN]
            long_df = loadFiltered(
                start=f"{year}-{_RETURN_WINDOW_START}",
                end=f"{year}-{_RETURN_WINDOW_END}",
                adjustment="raw",
            )
            if long_df is None or long_df.is_empty():
                _PORTFOLIO_CACHE[key] = None
                return None
            sub = long_df.filter(pl.col("ISU_CD").is_in(target_codes))
            for code in target_codes:
                stock = sub.filter(pl.col("ISU_CD") == code).sort("BAS_DD")
                if stock.is_empty():
                    continue
                cl = stock["TDD_CLSPRC"].to_numpy().astype(np.float64)
                if len(cl) < 60:
                    continue
                rets.append(np.diff(np.log(cl)))
        except Exception as exc:
            log.warning("factorBuild _portfolio_returns KR 실패: %s", type(exc).__name__)
            _PORTFOLIO_CACHE[key] = None
            return None
    else:
        # US: 기존 fetchOhlcv (Yahoo) 유지
        for c in codes[:maxN]:
            try:
                o = fetchOhlcv(c)
            except (ValueError, KeyError, OSError, AttributeError, RuntimeError):
                continue
            if isEmptyDf(o):
                continue
            cl = ohlcvToArrays(o).get("close")
            if cl is None or len(cl) < 60:
                continue
            rets.append(np.diff(np.log(cl)))

    if len(rets) < 5:
        _PORTFOLIO_CACHE[key] = None
        return None
    ml = min(len(r) for r in rets)
    panel = np.column_stack([r[-ml:] for r in rets])
    avg = panel.mean(axis=1)
    _PORTFOLIO_CACHE[key] = avg
    return avg


def buildFactors(market: str = "KR") -> dict | None:
    """진짜 횡단면 SMB/HML/RMW/CMA 시계열 빌드 (캐시됨).

    Capabilities:
        - Fama-French 5 분위 portfolio 형성 → 종목 등가중 일별 log return → SMB/HML/RMW/CMA 시계열
        - 모듈 캐시 (1 회 빌드 → 세션 동안 재사용)

    Args:
        market: ``"KR"`` 만 지원 (US 추후 추가).

    Returns:
        dict. year/universe/smb/hml/rmw/cma (np.ndarray)/notes. 데이터 부재 시 None.

    Guide:
        Fama-French 1992/2015 표준 5 분위 형성. universe < 100 시 None. proxy 한계 (size 는
        book equity, BM 은 equity/assets) 는 ``notes`` 에 명시.

    When:
        Factor 시계열 빌드 + AI 팩터 SMB/HML/RMW/CMA 답변.

    How:
        finance.parquet → 5 분위 portfolio → 종목 일별 수익률 평균 → SMB/HML 등.

    Requires:
        finance.parquet KR + 종목 100+ + 일별 가격 데이터.

    Raises:
        없음. 부재 시 None.

    Example:
        >>> f = buildFactors("KR")
        >>> f["smb"].shape
        (1260,)

    See Also:
        - factor.calc.decomposeFactor : 사용처
        - synth.scanBridge : 회계 데이터 추출

    AIContext:
        "한국 SMB 팩터 빌드 가능" 답변 시 universe + year 인용.
    """
    cache_key = (market, "latest")
    if cache_key in _FACTOR_CACHE:
        return _FACTOR_CACHE[cache_key]

    lf = loadScanParquet("finance", market)
    if lf is None:
        return None
    snap = extractAnnualConsolidated(lf.collect(engine="streaming"))
    year = _latestYear(snap)
    if year is None:
        return None

    # look-ahead 차단: 정렬 정보가 수익률 구간보다 앞서야 한다. 전년도 재무와 전년 말
    # 시총으로 5분위를 가르고, 그 재무가 공시된 뒤인 당해 4 월부터의 수익률만 귀속한다.
    try:
        fundYear = str(int(str(year)) - 1)
    except ValueError:
        return None
    retYear = str(year)

    metrics = _buildUniverseMetrics(market, fundYear)
    if len(metrics) < 100:
        return None

    # 5분위 포트폴리오. 시총 있으면 진짜 SMB/HML, 없으면 book proxy fallback
    has_mcap = sum(1 for m in metrics.values() if m.get("marketCap") is not None) >= 100
    if has_mcap:
        small, big = _quintilePortfolios(metrics, "marketCap", reverse=False)
        high_bm, low_bm = _quintilePortfolios(metrics, "bookToMarket", reverse=True)
        size_source = "KRX_MKTCAP"
        bm_source = "equity/marketCap"
    else:
        small, big = _quintilePortfolios(metrics, "bookEquity", reverse=False)
        high_bm, low_bm = _quintilePortfolios(metrics, "bookRatio", reverse=True)
        size_source = "book_equity_proxy"
        bm_source = "equity/assets_proxy"
    high_roe, low_roe = _quintilePortfolios(metrics, "roe", reverse=True)
    low_ag, high_ag = _quintilePortfolios(metrics, "assetGrowth", reverse=False)
    # CMA = conservative(low growth) - aggressive(high growth)

    # 시계열
    s_ret = _portfolioReturns(small, market, retYear)
    b_ret = _portfolioReturns(big, market, retYear)
    h_ret = _portfolioReturns(high_bm, market, retYear)
    l_ret = _portfolioReturns(low_bm, market, retYear)
    hr_ret = _portfolioReturns(high_roe, market, retYear)
    lr_ret = _portfolioReturns(low_roe, market, retYear)
    cn_ret = _portfolioReturns(low_ag, market, retYear)
    ag_ret = _portfolioReturns(high_ag, market, retYear)

    if any(x is None for x in [s_ret, b_ret, h_ret, l_ret]):
        return None

    # 길이 정규화 (가장 짧은 시계열 기준)
    arrs = [s_ret, b_ret, h_ret, l_ret]
    if hr_ret is not None and lr_ret is not None:
        arrs.extend([hr_ret, lr_ret])
    if cn_ret is not None and ag_ret is not None:
        arrs.extend([cn_ret, ag_ret])
    ml = min(len(a) for a in arrs)

    smb = s_ret[-ml:] - b_ret[-ml:]
    hml = h_ret[-ml:] - l_ret[-ml:]
    rmw = (hr_ret[-ml:] - lr_ret[-ml:]) if (hr_ret is not None and lr_ret is not None) else None
    cma = (cn_ret[-ml:] - ag_ret[-ml:]) if (cn_ret is not None and ag_ret is not None) else None

    notes = (
        f"SIZE = {size_source}, BM = {bm_source}. "
        + ("진짜 Fama-French 표준 (KRX 시총 직접). " if has_mcap else "fallback proxy (시총 미수집). ")
        + f"형성 {fundYear} 회계연도말 재무와 시총, 수익률 "
        + f"{retYear}-{_RETURN_WINDOW_START}~{_RETURN_WINDOW_END}."
    )
    result = {
        "year": retYear,
        "fundYear": fundYear,
        "retYear": retYear,
        "returnWindow": f"{retYear}-{_RETURN_WINDOW_START}~{retYear}-{_RETURN_WINDOW_END}",
        "market": market,
        "universe": len(metrics),
        "n_obs": int(ml),
        "smb": smb,
        "hml": hml,
        "rmw": rmw,
        "cma": cma,
        "smallN": len(small),
        "bigN": len(big),
        "highBmN": len(high_bm),
        "lowBmN": len(low_bm),
        "sizeSource": size_source,
        "bmSource": bm_source,
        "isRealFamaFrench": has_mcap,
        "notes": notes,
    }
    _FACTOR_CACHE[cache_key] = result
    return result


# 0.10 BC 깸. snake_case alias 제거.
