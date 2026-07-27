"""Altman Z-Score 횡단면 quant factor.

학술: Altman (1968) Journal of Finance — 제조업 상장사 부실 확률 5변수 모형.
       Altman & Hotchkiss (2006) — Z'' (비제조업/신흥시장) 4변수 모형.

Z = 1.2·(WC/TA) + 1.4·(RE/TA) + 3.3·(EBIT/TA) + 0.6·(MC/TL) + 1.0·(S/TA)

해석 (원본 1968):
    Z > 2.99 : 안전 (safe zone)
    1.81 ≤ Z ≤ 2.99 : 회색지대 (grey zone)
    Z < 1.81 : 부실 가능 (distress zone)

Z'' (제조업/서비스/신흥시장 공통):
    Z'' = 6.56·(WC/TA) + 3.26·(RE/TA) + 6.72·(EBIT/TA) + 1.05·(Eq/TL)
    Z'' > 2.6 / 1.1~2.6 / < 1.1

dartlab 데이터: DART finance.parquet (자산/부채/유동자산/유동부채/이익잉여금/영업이익/매출)
               + KRX 연도말 MKTCAP (gather/_hfBulk).
"""

from __future__ import annotations

import logging

import polars as pl

from dartlab.quant.factor.build import _fetchYearEndMarketcaps, _latestYear
from dartlab.quant.screen.dataAccess import extractAccount, loadScanParquet
from dartlab.synth.scanBridge import extractAnnualConsolidated, isEdgarSchema

log = logging.getLogger(__name__)


def _zoneZ(z: float) -> str:
    if z > 2.99:
        return "safe"
    if z > 1.81:
        return "grey"
    return "distress"


def _zoneZpp(z: float) -> str:
    if z > 2.6:
        return "safe"
    if z > 1.1:
        return "grey"
    return "distress"


def calcAltmanFactor(
    *,
    market: str = "KR",
    variant: str = "auto",
    stockCode: str | None = None,
    **kwargs,
) -> dict | None:
    """Altman Z-Score 횡단면 quant factor — 한국 시장 전종목 부실 확률 스코어.

    Capabilities:
        - 전종목 Z (시가총액 기반 1968 모형) 또는 Z'' (신흥시장 모형) 자동 분기
        - safe / grey / distress 3 zone 분포
        - Top (안전) / Bottom (부실) 각 10종목 추출
        - 한국 시장 부실 risk 지도

    AIContext:
        - Sprint 2 재무 알파 9축 중 하나 — credit engine 과 연결
        - story `altmanFactorBlock` (시장분석 섹션) 자동 호출
        - 저 Z-Score 기업은 quant 포트폴리오에서 자동 제외 후보

    Guide:
        - 전체 시장 스냅샷 : calcAltmanFactor()
        - Z'' (제조업 외 포함) : calcAltmanFactor(variant="zpp")
        - 원본 Z (제조업 상장) : calcAltmanFactor(variant="z")

    See Also:
        - credit.metrics : 단일 종목 altmanZScore 필드
        - core.finance.ratios._calcAltmanZ : 원 공식 구현
        - calcPiotroskiFactor : 같은 Sprint 2 재무 건강 축

    When:
        Quant 재무 알파 9 축 + AI 부실 위험 답변 1 차.

    How:
        scan finance.parquet 연결 → 최신 연도 → Z/Z'' 계산 → safe/grey/distress
        분포 + top/bottom 10.

    Requires:
        scan finance.parquet + (Z 사용 시) 시가총액 데이터.

    Raises:
        없음 — 실패는 None.

    Args:
        market: ``"KR"`` | ``"US"``. 기본 ``"KR"``.
        variant: ``"auto"`` (MKTCAP 있으면 Z, 없으면 Z''), ``"z"``, ``"zpp"``.

    Returns:
        dict
            market : str
            year : str — 펀더멘털 기준 연도
            variant : str — "z" | "zpp"
            universe : int — 계산 성공 종목 수
            scores : dict[str, float] — {stockCode: Z}
            zones : dict[str, dict] — {safe: {...}, grey: {...}, distress: {...}} 각 count/pct
            topSafe : list[tuple[str, float]] — Z 상위 10
            topDistress : list[tuple[str, float]] — Z 하위 10
            interpretation : str

    Examples:
        >>> from dartlab.quant.alphas.altman import calcAltmanFactor
        >>> r = calcAltmanFactor(market="KR")
        >>> print(r["zones"]["distress"]["pct"], "%")
        12.3 %

    Notes:
        - Z 는 제조업 상장 5변수 원본. 한국 시장에서도 상장 제조업에 광범위 사용.
        - Z'' 는 1995 이후 비제조업/신흥시장 공통 4변수. 한국엔 Z'' 권장 (금융/서비스/IT 포함).
        - Z < 1.81 이어도 회생 케이스 있음 — 단일 지표 판정 금지, Piotroski/Beneish 교차.
    """
    try:
        lf = loadScanParquet("finance", market)
        if lf is None:
            return None
        snap = extractAnnualConsolidated(lf.collect(engine="streaming"))
        year = _latestYear(snap)
        if year is None:
            return None
    except (OSError, ValueError, KeyError, AttributeError) as exc:
        log.warning("calcAltmanFactor year 추출 실패: %s", type(exc).__name__)
        return None

    edgar = isEdgarSchema(snap)
    yearCol = "fy" if edgar else "bsns_year"
    year_val = int(year) if edgar else year
    cur = snap.filter(pl.col(yearCol) == year_val)
    if cur.is_empty():
        return None

    market_caps = _fetchYearEndMarketcaps(market, str(year))

    scores: dict[str, float] = {}
    # 성능 fix (G5): partition_by 한 번 호출 → 종목당 O(1) lookup. 기존 filter 는 O(n²).
    partitions = cur.partition_by("stockCode", as_dict=True)
    for code_key, stock in partitions.items():
        # polars partition_by as_dict=True 는 키를 tuple 로 줌
        code = code_key[0] if isinstance(code_key, tuple) else code_key
        if not isinstance(code, str) or stock.is_empty():
            continue

        ta = extractAccount(stock, "total_assets")
        tl = extractAccount(stock, "total_liabilities")
        ca = extractAccount(stock, "current_assets")
        cl = extractAccount(stock, "current_liabilities")
        re = extractAccount(stock, "retained_earnings")
        op = extractAccount(stock, "operating_profit")
        sales = extractAccount(stock, "sales")
        eq = extractAccount(stock, "total_equity")
        mc = market_caps.get(code)

        if not ta or ta <= 0 or not tl or tl <= 0:
            continue
        wc = (ca or 0) - (cl or 0)

        if variant == "zpp" or (variant == "auto" and (mc is None or not eq or eq <= 0)):
            # Z'' (4변수, 비제조업/신흥시장)
            if eq is None or eq <= 0:
                continue
            z = 6.56 * (wc / ta) + 3.26 * ((re or 0) / ta) + 6.72 * ((op or 0) / ta) + 1.05 * (eq / tl)
            scores[code] = z
        else:
            # Z (원본 5변수, 시총 기반)
            if mc is None or mc <= 0:
                # fallback: Z' (장부가 기반)
                if eq is None or eq <= 0:
                    continue
                z = (
                    0.717 * (wc / ta)
                    + 0.847 * ((re or 0) / ta)
                    + 3.107 * ((op or 0) / ta)
                    + 0.420 * (eq / tl)
                    + 0.998 * ((sales or 0) / ta)
                )
            else:
                z = (
                    1.2 * (wc / ta)
                    + 1.4 * ((re or 0) / ta)
                    + 3.3 * ((op or 0) / ta)
                    + 0.6 * (mc / tl)
                    + 1.0 * ((sales or 0) / ta)
                )
            scores[code] = z

    if not scores:
        return None

    zone_fn = _zoneZpp if variant == "zpp" else _zoneZ
    counts = {"safe": 0, "grey": 0, "distress": 0}
    for z in scores.values():
        counts[zone_fn(z)] += 1

    total = len(scores)
    zones = {k: {"count": v, "pct": round(100 * v / total, 1)} for k, v in counts.items()}

    sorted_items = sorted(scores.items(), key=lambda x: -x[1])
    top_safe = [(c, round(z, 2)) for c, z in sorted_items[:10]]
    top_distress = [(c, round(z, 2)) for c, z in sorted_items[-10:]]

    resolved_variant = "zpp" if variant == "zpp" else ("z" if variant == "z" else "z" if market_caps else "zpp")

    # 단일 종목 분기 (Step 6)
    if stockCode:
        z_value = scores.get(stockCode)
        if z_value is None:
            return {
                "stockCode": stockCode,
                "market": market,
                "year": str(year),
                "error": f"{stockCode} 데이터 없음 (universe {total}개 중 미포함)",
            }
        zone = zone_fn(z_value)
        # universe 내 percentile 계산
        sorted_z = sorted(scores.values())
        rank = sum(1 for v in sorted_z if v <= z_value)
        percentile = round(100 * rank / total, 1)
        return {
            "stockCode": stockCode,
            "market": market,
            "year": str(year),
            "variant": resolved_variant,
            "score": round(z_value, 2),
            "zone": zone,
            "percentile": percentile,
            "universe": total,
            "interpretation": (
                f"{stockCode} Altman {resolved_variant.upper()}={round(z_value, 2)} ({zone}) — "
                f"전종목 {total}개 중 {percentile}백분위. "
                + ("안전 (Z>2.99)." if zone == "safe" else "회색지대." if zone == "grey" else "부실 위험 (Z<1.81).")
            ),
        }

    return {
        "market": market,
        "year": str(year),
        "variant": resolved_variant,
        "universe": total,
        "scores": {c: round(z, 2) for c, z in scores.items()},
        "zones": zones,
        "topSafe": top_safe,
        "topDistress": top_distress,
        "interpretation": (
            f"{market} 시장 {year}년 {total}개 종목 중 부실 위험 "
            f"{zones['distress']['pct']}% ({zones['distress']['count']}사), "
            f"안전 {zones['safe']['pct']}%. variant={resolved_variant}."
        ),
    }
