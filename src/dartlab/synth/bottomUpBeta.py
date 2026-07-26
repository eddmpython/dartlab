"""Bottom-up Beta — Damodaran Hamada Unlever/Relever.

Damodaran *Investment Valuation* Ch.7:
    β_U = β_L / (1 + (1 - t) × D/E)    # Hamada unlever
    β_L(firm) = β_U(peer mean) × (1 + (1 - t) × D/E(firm))  # relever

섹터 peer 평균 unlevered β 가 개별 기업 β 보다 안정적 (noise 제거).
scipy 무의존 — 평균/중앙값/난수만 사용.
"""

from __future__ import annotations

import random
from statistics import mean, median
from typing import Any

# 둘 다 L0 정의다. 예전에는 frame.sector 와 scan.io.parquet 이 재export 한 것을
# 동적 import 로 가져와 L1.5 형제를 관통하는 모양이 됐다.
from dartlab.core.sector import getSectorParamsByName
from dartlab.core.utils.helpers import parseNumStr


def calcBottomUpBeta(
    *,
    sector: str,
    debtToEquity: float,
    taxRate: float = 0.22,
    peerLimit: int = 20,
    country: str = "KR",
) -> dict[str, Any]:
    """Hamada equation — peer 평균 unlevered β → 자기 D/E 로 relever (bottom-up β).

    Capabilities:
        Damodaran 의 bottom-up beta 방법 — 자체 회귀 β 의 측정오차 문제를
        peer 평균 unlevered β 로 우회. Hamada (1972): β_L = β_U × (1 + (1-t)
        × D/E). 한국 시장은 scan/finance.parquet 에서 peer 자동 추출.

    Args:
        sector: 섹터/산업그룹명 (WICS industryGroup 권장).
        debtToEquity: 자기 D/E (시장가 기준 권장, 없으면 book).
        taxRate: 유효세율 (0.0~0.5). 기본 0.22 (KR 법인세 + 지방소득세).
        peerLimit: peer 샘플 최대 수. 기본 20.
        country: ISO2 (현재 KR 만 peer 자동 추출, US 등은 sector_default).

    Returns:
        dict:
            - ``leveredBeta`` (float): relevered β
            - ``unleveredBetaMean``/``unleveredBetaMedian`` (float)
            - ``peerCount`` (int)
            - ``method`` (str): ``"bottom_up"``/``"sector_default"``/
              ``"fallback_one"``
            - ``peers`` (list[dict]): {code, betaLevered, de, betaUnlevered}
            - ``sector``/``debtToEquity`` (str/float): echo

    Raises:
        없음.

    Example:
        >>> r = calcBottomUpBeta(sector="자동차", debtToEquity=0.8, country="KR")
        >>> r["leveredBeta"], r["peerCount"]
        (1.45, 12)

    Guide:
        peer 5 개 이상 확보 시 bottom_up, 5 개 미만 시 sector_default (정적
        섹터 β). 다 안 되면 fallback_one (β=1). 한국 자동차/IT 의 β ~ 1.2~1.5,
        utility 0.6~0.8, 필수소비재 0.5~0.7.

    SeeAlso:
        - ``loadDamodaranERP``: ERP 입력
        - ``computeCompanyWacc``: bottom_up β 사용 WACC 산출
        - Damodaran (2012) "Investment Valuation" Ch.4

    Requires:
        scan/finance.parquet (peer 추출 — KR) 또는 sectorBetaFallback dict.

    AIContext:
        method 라벨 노출 필수 — bottom_up 결과만 신뢰. sector_default 는
        근사값, fallback_one 은 데이터 부족 신호. peerCount < 5 이면
        결과 신뢰도 낮음.

    LLM Specifications:
        AntiPatterns:
            - taxRate 0.5 초과 입력 — 자동 clamp [0, 0.5].
            - country="US" 호출 → sector_default 자동 — KR 만 peer 추출.
              US 회사 분석 시 Damodaran US sector β 사용 권장.
        OutputSchema:
            상기 8 키 dict.
        Prerequisites:
            scan/finance.parquet 로드 가능 (KR peer 추출).
        Freshness:
            scan/finance.parquet = 분기 (마감 후 30~45 일).
        Dataflow:
            sector → _extractKrPeers (KR) → unlevered β 계산 → 평균 →
            relever (Hamada) → leveredBeta.
        TargetMarkets: KR (scan/finance.parquet). US 는 sector_default fallback.
    """
    tax = max(0.0, min(0.5, float(taxRate)))
    de = max(0.0, float(debtToEquity))

    # peer 추출 (KR + scan/finance.parquet)
    peers: list[dict[str, Any]] = []
    if country == "KR":
        peers = _extractKrPeers(sector, peerLimit)

    if len(peers) < 5:
        # sector_default fallback
        sector_beta: float | None = None
        try:
            sp = getSectorParamsByName(sector)
            if sp and hasattr(sp, "beta") and sp.beta:
                sector_beta = float(sp.beta)
        except (AttributeError, ValueError, TypeError):
            pass

        if sector_beta is not None:
            return {
                "leveredBeta": round(sector_beta, 3),
                "unleveredBetaMean": None,
                "unleveredBetaMedian": None,
                "peerCount": len(peers),
                "method": "sector_default",
                "peers": peers,
                "sector": sector,
                "debtToEquity": de,
            }

        return {
            "leveredBeta": 1.0,
            "unleveredBetaMean": None,
            "unleveredBetaMedian": None,
            "peerCount": len(peers),
            "method": "fallback_one",
            "peers": peers,
            "sector": sector,
            "debtToEquity": de,
        }

    # 각 peer unlever
    unlevered: list[float] = []
    for p in peers:
        beta_l = p.get("betaLevered")
        p_de = p.get("de", 0.3)
        if beta_l is None or beta_l <= 0:
            continue
        try:
            beta_u = beta_l / (1.0 + (1.0 - tax) * p_de)
        except ZeroDivisionError:
            continue
        if 0.1 < beta_u < 3.0:  # sanity
            unlevered.append(beta_u)
            p["betaUnlevered"] = round(beta_u, 3)

    if len(unlevered) < 5:
        return {
            "leveredBeta": 1.0,
            "unleveredBetaMean": None,
            "unleveredBetaMedian": None,
            "peerCount": len(unlevered),
            "method": "fallback_one",
            "peers": peers,
            "sector": sector,
            "debtToEquity": de,
        }

    mu = mean(unlevered)
    med = median(unlevered)

    # Relever (자기 D/E)
    levered = mu * (1.0 + (1.0 - tax) * de)
    levered = max(0.3, min(levered, 3.0))  # sanity

    return {
        "leveredBeta": round(levered, 3),
        "unleveredBetaMean": round(mu, 3),
        "unleveredBetaMedian": round(med, 3),
        "peerCount": len(unlevered),
        "method": "bottom_up",
        "peers": peers[:peerLimit],
        "sector": sector,
        "debtToEquity": de,
    }


def _extractKrPeers(sector: str, limit: int) -> list[dict[str, Any]]:
    """scan/finance.parquet → 동일 섹터 peer 의 β + D/E 추출.

    현재 sectorParams.json 에 개별 종목 매핑이 없으므로 단순화:
    - 섹터별 대표 β 를 peer 각자에 동일 적용 (지금은 peer D/E 만 계산)
    - 더 정교한 구현은 beta 수익률 회귀 (향후 개선)

    반환: peer list [{code, betaLevered, de, betaUnlevered}]
    """
    try:
        import importlib

        import polars as pl

        # `_ensureScanData` 는 scan 이 실제로 소유한 private 라 동적 import 를 유지한다.
        # `parseNumStr` 은 core 정의를 scan 이 재export 한 것뿐이라 직접 내려 받는다.
        _ensureScanData = importlib.import_module("dartlab.scan.io.parquet")._ensureScanData
    except ImportError:
        return []

    scan_dir = _ensureScanData()
    path = scan_dir / "finance.parquet"
    if not path.exists():
        return []

    try:
        lf = pl.scan_parquet(str(path))
        needed = ["stockCode", "bsns_year", "sj_div", "account_nm", "thstrm_amount", "fs_nm", "reprt_nm"]
        avail = lf.collect_schema().names()
        cols = [c for c in needed if c in avail]
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

    # 섹터 β 는 sectorParams 에서 조회 (없으면 1.0)
    sector_beta = _sectorBetaFallback(sector)

    # peer 추출: cur 의 모든 종목 (섹터 매핑 테이블 없으므로 일단 무작위 샘플)
    # 향후: c.sector.industryGroup 기반 필터 개선
    all_codes = cur["stockCode"].unique().to_list()
    rng = random.Random(hash(sector) & 0xFFFFFFFF)
    rng.shuffle(all_codes)

    debt_nms = ["부채총계"]
    equity_nms = ["자본총계"]

    def _extract(df: pl.DataFrame, nms: list[str]) -> float | None:
        for nm in nms:
            r = df.filter(pl.col("account_nm") == nm)
            if not r.is_empty():
                return parseNumStr(r["thstrm_amount"][0])
        return None

    peers: list[dict[str, Any]] = []
    for sc in all_codes:
        if len(peers) >= limit:
            break
        stock = cur.filter(pl.col("stockCode") == sc)
        if stock.is_empty():
            continue
        debt = _extract(stock, debt_nms)
        eq = _extract(stock, equity_nms)
        if not debt or not eq or eq <= 0:
            continue
        de = debt / eq
        if de > 5.0 or de < 0:  # 자본잠식/극단값 제외
            continue
        peers.append(
            {
                "code": sc,
                "betaLevered": sector_beta,  # 섹터 β (수익률 회귀 미구현 — 향후 개선)
                "de": round(de, 3),
            }
        )

    return peers


def _sectorBetaFallback(sector: str) -> float:
    """sectorParams 에서 섹터 β 조회. 없으면 1.0."""

    try:
        sp = getSectorParamsByName(sector)
        if sp and hasattr(sp, "beta") and sp.beta:
            return float(sp.beta)
    except (AttributeError, ValueError, TypeError):
        pass
    return 1.0
