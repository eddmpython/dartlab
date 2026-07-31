"""부채 구조 전수 스캔 — 사채 만기, 부채비율, ICR, 위험등급.

Public API:
    scanDebt()  → pl.DataFrame (전체 상장사 부채 현황)
"""

from __future__ import annotations

import polars as pl

from dartlab.core.logger import getLogger

_log = getLogger(__name__)


from dartlab.scan.debt.risk import classifyRisk, scanIcr
from dartlab.scan.debt.scanner import scanBonds, scanDebtMix, scanDebtSecurities, scanShortDebt


def scanDebt(*, verbose: bool = True) -> pl.DataFrame:
    """전체 상장사 부채 스캔 → 종합 DataFrame.

    Parameters
    ----------
    verbose : bool, default True
        진행 라인을 ``logger.info`` 로 출력.

    Returns
    -------
    pl.DataFrame
        stockCode : str — 종목코드
        사채잔액 : float — 사채 총잔액 (백만원)
        단기잔액 : float — 1년 이내 만기 잔액 (백만원)
        단기비중 : float — 단기잔액/사채잔액 (%)
        단기사채잔액 / CP잔액 : float — 별도 측정
        단기채무합계 : float — 단기사채 + CP
        총부채 / 부채비율 : float — finance BS 기준
        ICR : float — 영업이익 / 이자비용
        위험등급 : str, 안전/관찰/주의/고위험.
            ICR 결측이고 상향 신호도 없으면 "자료부족", 부채 자료가 아예 없으면 null.

    Raises
    ------
    polars.PolarsError
        corporateBond · shortTermBond · finance.parquet 손상 시.

    Examples
    --------
    >>> import dartlab
    >>> df = dartlab.scan("debt")
    >>> df.filter(pl.col("위험등급") == "고위험").select(["종목코드", "ICR"]).head()

    Capabilities:
        - 4 sub-scanner (scanBonds / scanShortDebt / scanDebtMix / scanIcr) 결과 union → 종목별
          사채잔액 + 단기비중 + CP + 부채비율 + ICR + 종합 위험등급 (안전/관찰/주의/고위험).
        - ICR (영업이익/이자비용) 이 가장 강한 부채 위험 지표.

    AIContext:
        Agent 가 ``dartlab.scan("debt")`` 호출 시 본 함수 dispatch. 부채 리스크 스크리닝
        (ICR < 1 종목 watchlist) · 단기차입 비중 비교 · 위험등급 cross-company 분석 source.

    Guide:
        - infer_schema_length=None 강제 — 큰 금액 (1.2e11+) 에서 polars schema inference overflow
          회귀 방지 (재발 사례 있음).
        - 위험등급 SSOT: ``classifyRisk(icr, shortRatio, shortDebtTotal)``.

    When:
        대시보드 debt 카드 빌드 시. 부채 리스크 스크리닝 시.

    How:
        scanBonds / scanShortDebt / scanDebtMix / scanIcr 순차 호출 → all_codes union →
        종목별 dict merge → classifyRisk 위험등급 → wide row 적재. infer_schema_length 가드.

    Requires:
        - 로컬 ``data/dart/scan/report/{corporateBond,shortTermBond}.parquet`` (``buildReport``)
        - ``data/dart/scan/finance.parquet`` (부채비율/ICR 계산)

    SeeAlso:
        - :func:`scanBonds` · :func:`scanShortDebt` · :func:`scanDebtMix` · :func:`scanIcr` — sub-scanner
        - :func:`classifyRisk` — 위험등급 정책
        - :func:`dartlab.scan.financial.liquidity.scanLiquidity` — 유동성 보완 axis
    """

    def _say(msg: str) -> None:
        if verbose:
            _log.info(msg)

    _say("1/4 사채 만기...")
    bond_map = scanBonds()
    _say(f"  -> {len(bond_map)}종목")

    _say("2/4 단기사채/CP...")
    short_map = scanShortDebt()
    _say(f"  -> {len(short_map)}종목")

    _say("3/4 부채비율...")
    debt_map = scanDebtMix()
    _say(f"  -> {len(debt_map)}종목")

    _say("4/5 이자보상배율...")
    icr_map = scanIcr()
    _say(f"  -> {len(icr_map)}종목")

    _say("5/5 채무증권 발행...")
    sec_map = scanDebtSecurities()
    _say(f"  -> {len(sec_map)}종목")

    all_codes = set(bond_map) | set(debt_map) | set(icr_map) | set(short_map) | set(sec_map)

    results = []
    for code in all_codes:
        b = bond_map.get(code, {})
        s = short_map.get(code, {})
        d = debt_map.get(code, {})
        sec = sec_map.get(code, {})
        icr = icr_map.get(code)

        shortRatio = b.get("단기비중")
        shortDebtTotal = s.get("단기채무합계")
        risk = classifyRisk(icr, shortRatio, shortDebtTotal) if (b or s or icr is not None) else None

        results.append(
            {
                "stockCode": code,
                "사채잔액": b.get("사채잔액"),
                "단기잔액": b.get("단기잔액"),
                "단기비중": shortRatio,
                "단기사채잔액": s.get("단기사채잔액"),
                "CP잔액": s.get("CP잔액"),
                "단기채무합계": shortDebtTotal,
                "채무증권발행액": sec.get("채무증권발행액"),
                "채무증권평균이자율": sec.get("채무증권평균이자율"),
                "총부채": d.get("총부채"),
                "부채비율": d.get("부채비율"),
                "ICR": icr,
                "위험등급": risk,
            }
        )

    # infer_schema_length=None: 전체 행 스캔 (기본 100행 추론이 큰 금액에서 overflow
    # 유발. "ComputeError: could not append value 1.2e11 of type f64" 재발 방지.
    df = pl.DataFrame(results, infer_schema_length=None)
    _say(f"부채 스캔 완료: {df.shape[0]}종목")
    return df


__all__ = ["scanDebt"]
