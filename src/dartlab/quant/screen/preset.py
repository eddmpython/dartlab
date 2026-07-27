"""팩터 스크리닝 프리셋.

학술 근거: Novy-Marx (2013), Piotroski (2000) F-Score.
"""

from __future__ import annotations

import logging

import polars as pl

from dartlab.core.polarsUtil import isEmptyDf
from dartlab.quant.numeric import parseNumber
from dartlab.quant.screen.dataAccess import loadScanParquet
from dartlab.synth.scanBridge import extractAnnualConsolidated, isEdgarSchema

log = logging.getLogger(__name__)

_PRESETS = {
    "quality": {"desc": "고품질: ROA > 5%, 부채비율 < 60%", "roa_min": 5, "debt_max": 60},
    "value": {"desc": "가치주: 부채비율 < 40%, 영업마진 > 10%", "debt_max": 40, "margin_min": 10},
    "growth": {"desc": "성장주: 매출 YoY 성장 > 10%", "growth_min": 10},
    "dividend": {"desc": "배당주: DPS > 0 (배당 지급 종목)"},
    "momentum": {"desc": "모멘텀: 가격 데이터 필요 — dartlab.quant('모멘텀', code) 사용", "price_only": True},
    "lowvol": {"desc": "저변동: 가격 데이터 필요 — dartlab.quant('변동성', code) 사용", "price_only": True},
    "breakout_240w": {
        "desc": "주봉 240SMA 상향 돌파 (장기 추세 전환)",
        "price_based": True,
        "sma_period": 240,
        "freq": "W",
    },
    "breakout_60d": {"desc": "일봉 60SMA 상향 돌파", "price_based": True, "sma_period": 60, "freq": "D"},
    "golden_cross": {"desc": "골든크로스 (5SMA > 20SMA)", "price_based": True, "sma_short": 5, "sma_long": 20},
    "ma_aligned": {"desc": "이평선 정배열 (5>20>60>120)", "price_based": True, "ma_align": True},
}


def _screenPriceBased(preset: str, market: str, universe: list[str] | None = None) -> dict:
    """가격 기반 프리셋 — 종목 풀에 대해 SMA 계산.

    universe가 None이면 시총 상위 100종목으로 제한 (성능).
    """
    cfg = _PRESETS[preset]
    result: dict = {"market": market, "preset": preset, "criteria": cfg["desc"]}

    # 종목 풀 결정
    if universe is None:
        try:
            from dartlab.gather.krx.listing import getTopStocks

            universe = getTopStocks(market=market, limit=100)
        except (ImportError, AttributeError):
            try:
                from dartlab.gather.krx.listing import getKindList

                df = getKindList()
                universe = df.head(100)["종목코드"].to_list() if df is not None else []
            except (ImportError, AttributeError, KeyError):
                universe = []

    if not universe:
        return {**result, "error": "종목 풀 로드 실패", "stocks": []}

    from dartlab.quant.screen.dataAccess import fetchOhlcv

    passed = []
    for code in universe:
        try:
            ohlcv = fetchOhlcv(code)
            if isEmptyDf(ohlcv):
                continue
            closes = ohlcv.get_column("close").to_list()
            if cfg.get("ma_align"):
                if len(closes) < 120:
                    continue
                sma5 = sum(closes[-5:]) / 5
                sma20 = sum(closes[-20:]) / 20
                sma60 = sum(closes[-60:]) / 60
                sma120 = sum(closes[-120:]) / 120
                if sma5 > sma20 > sma60 > sma120:
                    passed.append(
                        {
                            "stockCode": code,
                            "currentPrice": closes[-1],
                            "sma5": round(sma5, 2),
                            "sma20": round(sma20, 2),
                            "sma60": round(sma60, 2),
                            "sma120": round(sma120, 2),
                        }
                    )
            elif "sma_short" in cfg:
                short_p = cfg["sma_short"]
                long_p = cfg["sma_long"]
                if len(closes) < long_p + 1:
                    continue
                sma_s_now = sum(closes[-short_p:]) / short_p
                sma_l_now = sum(closes[-long_p:]) / long_p
                sma_s_prev = sum(closes[-short_p - 1 : -1]) / short_p
                sma_l_prev = sum(closes[-long_p - 1 : -1]) / long_p
                if sma_s_now > sma_l_now and sma_s_prev <= sma_l_prev:
                    passed.append(
                        {
                            "stockCode": code,
                            "currentPrice": closes[-1],
                            f"sma{short_p}": round(sma_s_now, 2),
                            f"sma{long_p}": round(sma_l_now, 2),
                        }
                    )
            else:
                period = cfg["sma_period"]
                # 주봉 변환은 단순화: 일봉의 5배 윈도우
                window = period * 5 if cfg.get("freq") == "W" else period
                if len(closes) < window + 1:
                    continue
                sma_now = sum(closes[-window:]) / window
                sma_prev = sum(closes[-window - 1 : -1]) / window
                # 돌파: 어제 종가 ≤ SMA, 오늘 종가 > SMA
                if closes[-1] > sma_now and closes[-2] <= sma_prev:
                    passed.append(
                        {
                            "stockCode": code,
                            "currentPrice": closes[-1],
                            f"sma{period}{cfg.get('freq', 'D')}": round(sma_now, 2),
                        }
                    )
        except (KeyError, ValueError, TypeError, AttributeError, IndexError):
            continue

    result["stocks"] = passed
    result["count"] = len(passed)
    return result


def calcScreen(*, market: str = "KR", preset: str = "quality", stockCode: str | None = None, **kwargs) -> dict:
    """팩터 스크리닝.

    프리셋 조건(quality/value/growth/dividend/momentum/lowvol/breakout 등)에
    해당하는 종목을 필터링한다.

    Parameters
    ----------
    market : str
        시장. 기본 "KR".
    preset : str
        스크리닝 프리셋 키. 기본 "quality".
    stockCode : str | None
        특정 종목이 프리셋을 통과했는지 확인.

    Returns
    -------
    dict
        market : str — 시장
        preset : str — 사용된 프리셋
        criteria : str — 프리셋 설명
        year : str — 기준 연도
        count : int — 통과 종목 수
        stocks : list[dict] — 통과 종목 리스트 (최대 30개)
            stockCode : str, name : str,
            ROA : float (%) | opMargin : float (%) | salesGrowth : float (%)
        targetPassed : bool — stockCode 지정 시 통과 여부
        target : dict | None — stockCode 지정 시 해당 종목 정보

    Capabilities:
        - quality/value/growth/dividend/momentum/lowvol/breakout 프리셋별 종목 필터링
        - stockCode 지정 시 단일 종목 pass/fail 진단

    Guide:
        프리셋 명세 ``_PRESETS`` SSOT. 신규 프리셋 추가 시 본 dict 등록.

    When:
        Universe 스크리닝 + AI "이 조건 통과 종목" 답변.

    How:
        프리셋 분기 → finance.parquet 로드 또는 가격 기반 screening.

    Requires:
        scan finance.parquet 또는 가격 데이터.

    Raises:
        없음 — 미지정 프리셋 시 ``available`` 키 반환.

    Example:
        >>> calcScreen(preset="quality", market="KR")["count"]
        42

    See Also:
        - factor.ranking.calcRanking : 종합 ranking
        - screen.dataAccess.loadScanParquet : 데이터

    AIContext:
        "퀄리티 종목 추천" 답변 시 preset + stocks 인용.
    """
    if preset not in _PRESETS:
        return {"error": f"알 수 없는 프리셋: {preset}", "available": list(_PRESETS.keys())}

    cfg = _PRESETS[preset]
    result: dict = {"market": market, "preset": preset, "criteria": cfg["desc"]}

    if cfg.get("price_only"):
        return {**result, "info": cfg["desc"]}

    if cfg.get("price_based"):
        return _screenPriceBased(preset, market)

    if preset == "dividend":
        return _screenDividend(result, market, stockCode)

    lf = loadScanParquet("finance", market)
    if lf is None:
        return {**result, "error": "finance.parquet 없음"}

    try:
        full = lf.collect(engine="streaming")
        df = extractAnnualConsolidated(full)
        if df.is_empty():
            df = full
    except (KeyError, ValueError, TypeError, AttributeError) as e:
        return {**result, "error": str(e)}

    edgar = isEdgarSchema(df)
    yearCol = "fy" if edgar else "bsns_year"
    yr = str(df.get_column(yearCol).sort(descending=True).to_list()[0])
    year_val = int(yr) if edgar else yr
    df = df.filter(pl.col(yearCol) == year_val)

    # 종목별 지표
    stocks: dict[str, dict] = {}
    if edgar:
        for row in df.iter_rows(named=True):
            code = row.get("stockCode")
            if not code:
                continue
            stocks[code] = {
                "name": row.get("company_name", ""),
                "sales": row.get("sales"),
                "prev_sales": None,
                "op": row.get("operating_profit"),
                "ni": row.get("net_profit"),
                "assets": row.get("total_assets"),
                "debt": row.get("total_liabilities"),
            }
    else:
        for row in df.iter_rows(named=True):
            code = row.get("stockCode")
            if not code:
                continue
            if code not in stocks:
                stocks[code] = {"name": row.get("corp_name", "")}
            sj = row.get("sj_div", "")
            nm = str(row.get("account_nm", ""))
            amt = parseNumber(row.get("thstrm_amount"))
            prev = parseNumber(row.get("frmtrm_amount"))
            s = stocks[code]
            if sj == "IS" and nm == "매출액":
                s["sales"] = amt
                s["prev_sales"] = prev
            if sj == "IS" and nm == "영업이익":
                s["op"] = amt
            if sj == "IS" and "당기순이익" in nm:
                s["ni"] = amt
            if sj == "BS" and nm == "자산총계":
                s["assets"] = amt
            if sj == "BS" and nm == "부채총계":
                s["debt"] = amt

    passed = []
    for code, s in stocks.items():
        sales = s.get("sales")
        op = s.get("op")
        ni = s.get("ni")
        assets = s.get("assets")
        debt = s.get("debt")

        margin = (op / sales * 100) if sales and sales > 0 and op else None
        roa = (ni / assets * 100) if assets and assets > 0 and ni else None
        dr = (debt / assets * 100) if assets and assets > 0 and debt else None

        if preset == "quality":
            if roa is not None and roa > cfg["roa_min"] and dr is not None and dr < cfg["debt_max"]:
                passed.append(
                    {"stockCode": code, "name": s.get("name", ""), "ROA": round(roa, 2), "debtRatio": round(dr, 2)}
                )
        elif preset == "value":
            if dr is not None and dr < cfg["debt_max"] and margin is not None and margin > cfg["margin_min"]:
                passed.append(
                    {
                        "stockCode": code,
                        "name": s.get("name", ""),
                        "opMargin": round(margin, 2),
                        "debtRatio": round(dr, 2),
                    }
                )
        elif preset == "growth":
            prev_sales = s.get("prev_sales")
            if sales and prev_sales and prev_sales > 0:
                growth = (sales - prev_sales) / abs(prev_sales) * 100
                if growth > cfg["growth_min"]:
                    passed.append({"stockCode": code, "name": s.get("name", ""), "salesGrowth": round(growth, 2)})

    # 정렬
    sort_key = {"quality": "ROA", "value": "opMargin", "growth": "salesGrowth"}.get(preset, "ROA")
    passed.sort(key=lambda x: x.get(sort_key, 0), reverse=True)

    if stockCode:
        target = [s for s in passed if s["stockCode"] == stockCode]
        result["targetPassed"] = len(target) > 0
        if target:
            result["target"] = target[0]

    result["stocks"] = passed[:30]
    result["count"] = len(passed)
    result["year"] = yr
    return result


def _screenDividend(result: dict, market: str, stockCode: str | None) -> dict:
    lf = loadScanParquet("dividend", market)
    if lf is None:
        return {**result, "error": "dividend.parquet 없음"}
    try:
        df = lf.collect(engine="streaming")
    except (KeyError, ValueError, TypeError, AttributeError) as e:
        return {**result, "error": str(e)}

    # DPS > 0인 종목 찾기
    code_col = next((c for c in ["stockCode", "종목코드"] if c in df.columns), None)
    if code_col is None:
        return {**result, "error": "종목코드 컬럼 없음"}

    # thstrm 또는 DPS 관련 컬럼 탐색
    dps_col = next((c for c in df.columns if "주당" in c or "DPS" in c or "thstrm" == c), None)
    if dps_col:
        stocks_with_div = df.filter(pl.col(dps_col).is_not_null()).select(code_col).unique().to_series().to_list()
        result["count"] = len(stocks_with_div)
        result["stocks"] = [{"stockCode": s} for s in stocks_with_div[:30]]
    else:
        result["count"] = 0
        result["stocks"] = []

    return result
