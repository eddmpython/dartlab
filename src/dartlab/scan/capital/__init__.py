"""주주환원 전수 스캔 — 배당, 자사주, 증자/감자 → 순환원 분류.

Public API:
    scanCapital()  → pl.DataFrame (전체 상장사 주주환원 현황)
"""

from __future__ import annotations

import polars as pl

from dartlab.core.logger import getLogger

_log = getLogger(__name__)


from dartlab.scan.capital.classifier import classifyReturn
from dartlab.scan.capital.scanner import (
    scanCapitalChange,
    scanDividend,
    scanOfferingUsage,
    scanShareTotal,
    scanTreasuryStock,
)


def scanCapital(*, verbose: bool = True) -> pl.DataFrame:
    """전체 상장사 주주환원 스캔 → 순환원 분류 DataFrame.

    Parameters
    ----------
    verbose : bool, default True
        진행 라인을 ``logger.info`` 로 출력.

    Returns
    -------
    pl.DataFrame
        stockCode : str — 종목코드
        배당여부 : bool — DPS > 0
        DPS : float — 주당 현금배당금 (원)
        배당수익률 : float — 현금배당수익률 (%)
        자사주보유 / 자사주취득 / 자사주처분 / 자사주소각 : bool
        취득수량 / 처분수량 / 소각수량 : float
        최근증자 : bool
        환원점수 : float — 0~3 누적 점수
        분류 : str — 적극환원/환원형/중립/희석형
        모순형 : bool — 배당 + 최근 증자

    Raises
    ------
    polars.PolarsError
        dividend · treasuryStock · capitalChange report parquet 손상 시.

    Examples
    --------
    >>> import dartlab
    >>> df = dartlab.scan("capital")
    >>> df.filter(pl.col("분류") == "환원형").select(["종목코드", "DPS"]).head()

    Capabilities:
        - 3 sub-scanner (scanDividend / scanTreasuryStock / scanCapitalChange) 결과 union →
          종목별 환원 점수 (0~3) + 분류 4 종 (적극환원/환원형/중립/희석형) + 모순형 (배당+증자) 플래그.
        - 자사주 소각 = 가장 강한 환원 신호 (점수 +1 가중).

    AIContext:
        Agent 가 ``dartlab.scan("capital")`` 호출 시 본 함수 dispatch. "환원형 종목" 스크리닝,
        "모순형 (배당+증자) 종목" 감지, 배당+자사주 통합 정책 분석 source.

    Guide:
        - 모순형 (배당 + 최근 증자) 은 자본정책 일관성 결여 신호 — risk 단락 인용.
        - 분류 SSOT: ``classifyReturn(hasDividend, hasBuyback, recentIncrease)`` private.

    When:
        대시보드 capital 카드 빌드 시. 환원/희석 스크리닝 시.

    How:
        scanDividend / scanTreasuryStock / scanCapitalChange 순차 호출 → all_codes union →
        종목별 dict merge → classifyReturn 분류 → 점수 + 모순형 결합 → wide row 적재.

    Requires:
        - 로컬 ``data/dart/scan/report/{dividend,treasuryStock,capitalChange}.parquet`` (``buildReport`` 산출)

    SeeAlso:
        - :func:`scanDividend` · :func:`scanTreasuryStock` · :func:`scanCapitalChange` — sub-scanner
        - :func:`classifyReturn` — 분류 정책
        - :func:`dartlab.scan.dividendTrend.scanDividendTrend` — 배당 시계열 보완 axis
    """

    def _say(msg: str) -> None:
        if verbose:
            _log.info(msg)

    _say("1/3 배당 스캔...")
    div_map = scanDividend()
    _say(f"  → {len(div_map)}종목")

    _say("2/3 자사주 스캔...")
    treasury_map = scanTreasuryStock()
    _say(f"  → {len(treasury_map)}종목")

    _say("3/5 증자/감자 스캔...")
    cap_map = scanCapitalChange()
    _say(f"  → {len(cap_map)}종목")

    _say("4/5 주식총수 현황...")
    share_map = scanShareTotal()
    _say(f"  → {len(share_map)}종목")

    _say("5/5 공모/사모 자금사용...")
    offering_map = scanOfferingUsage()
    _say(f"  → {len(offering_map)}종목")

    all_codes = set(div_map) | set(treasury_map) | set(cap_map) | set(share_map) | set(offering_map)

    results = []
    for code in all_codes:
        d = div_map.get(code, {})
        t = treasury_map.get(code, {})
        c = cap_map.get(code, {})
        sh = share_map.get(code, {})
        of = offering_map.get(code, {})

        hasDividend = d.get("배당여부", False)
        hasBuyback = t.get("당기취득", False)
        has_treasury = t.get("자사주보유", False)
        has_disposal = t.get("당기처분", False)
        has_cancel = t.get("당기소각", False)
        recentIncrease = c.get("최근증자", False)

        category, contradiction = classifyReturn(hasDividend, hasBuyback, recentIncrease)

        # 환원 점수 (참고용) — 소각은 가장 강한 환원 신호
        return_score = 0
        if hasDividend:
            return_score += 1
        if hasBuyback:
            return_score += 1
        if has_cancel:
            return_score += 1
        if recentIncrease:
            return_score -= 1

        results.append(
            {
                "stockCode": code,
                "배당여부": hasDividend,
                "DPS": d.get("DPS", 0.0),
                "배당수익률": d.get("배당수익률", 0.0),
                "자사주보유": has_treasury,
                "자사주취득": hasBuyback,
                "자사주처분": has_disposal,
                "자사주소각": has_cancel,
                "취득수량": t.get("취득수량", 0),
                "처분수량": t.get("처분수량", 0),
                "소각수량": t.get("소각수량", 0),
                "최근증자": recentIncrease,
                "환원점수": return_score,
                "분류": category,
                "모순형": contradiction,
                "발행주식총수": sh.get("발행주식총수"),
                "자기주식비율": sh.get("자기주식비율"),
                "조달금액": of.get("조달금액"),
                "목적외사용": of.get("목적외사용", False),
            }
        )

    df = pl.DataFrame(results)
    _say(f"주주환원 스캔 완료: {df.shape[0]}종목")
    return df


__all__ = ["scanCapital"]
