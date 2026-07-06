"""인력/급여 전수 스캔 — 직원 현황, 인건비 효율, 급여 성장, 고액 보수.

Public API:
    scanWorkforce()  → pl.DataFrame (전체 상장사 인력 현황)
"""

from __future__ import annotations

import polars as pl

from dartlab.core.logger import getLogger

_log = getLogger(__name__)


from dartlab.scan.workforce.growth import (
    computeSalaryVsRevenue,
    scanRevenueGrowth,
    scanSalaryGrowth,
)
from dartlab.scan.workforce.scanner import (
    scanEmployee,
    scanHighPay,
    scanRevenuePerEmployee,
    scanTopPay,
    scanUnregExecPay,
)


def scanWorkforce(*, verbose: bool = True) -> pl.DataFrame:
    """전체 상장사 인력 스캔 → 종합 DataFrame.

    Parameters
    ----------
    verbose : bool, default True
        진행 라인을 ``logger.info`` 로 출력.

    Returns
    -------
    pl.DataFrame
        stockCode : str — 종목코드
        직원수 : float | None — 정규+계약 합산 (명)
        평균급여_만원 : float | None — 직원수 가중평균 (만원/연)
        남녀격차 : float | None — 남여 평균급여 차이 (%)
        근속_년 : float | None — 평균 근속연수
        직원당매출_억 : float | None — 매출/직원수 (억)
        급여성장률 / 매출성장률 / 급여매출괴리 : float | None — 전년 대비 변화 (%)
        최고보수_억 : float | None — 임원 최고 보수 (억)
        공개인원 : float | None — 보수 공시 인원 (명)

    Raises
    ------
    polars.PolarsError
        employee · executivePayIndividual · finance.parquet 손상 시.

    Examples
    --------
    >>> import dartlab
    >>> df = dartlab.scan("workforce")
    >>> df.sort("직원당매출_억", descending=True).head()

    Capabilities:
        - 4 sub-scanner (scanEmployee / scanRevenuePerEmployee / scanSalaryGrowth + scanRevenueGrowth
          / scanTopPay) 결과 통합. 직원수 + 평균급여 + 남녀격차 + 근속 + 직원당매출 + 성장률 +
          고액 보수 wide column.
        - 급여매출괴리 = 급여성장률 - 매출성장률. 양수면 인건비가 매출보다 빨리 늘어남 (warning 신호).

    AIContext:
        Agent 가 ``dartlab.scan("workforce")`` 호출 시 본 함수 dispatch. "직원당 매출 높은 회사"
        스크리닝, "급여 급증 회사" watchlist, 1 사 인력 효율 비교 source.

    Guide:
        - 직원수 = 정규 + 계약 합산. 외주는 제외.
        - 평균급여 가중평균 = 직원수 가중. 남녀격차는 (남-여)/남 정의.

    When:
        대시보드 workforce 카드 빌드 시. 인력 효율 스크리닝 시.

    How:
        4 sub-scanner 순차 호출 → growth_df 변환 (scanSalaryGrowth + scanRevenueGrowth →
        computeSalaryVsRevenue) → all_codes union → 종목별 dict merge → 명시적 schema 로
        DataFrame 적재 (null safety).

    Requires:
        - 로컬 ``data/dart/scan/report/{employee,executivePayIndividual}.parquet`` (``buildReport``)
        - ``data/dart/scan/finance.parquet`` (직원당매출 / 성장률 계산)

    SeeAlso:
        - :func:`scanEmployee` · :func:`scanRevenuePerEmployee` · :func:`scanTopPay` —
          기본 sub-scanner
        - :func:`computeSalaryVsRevenue` — 급여 vs 매출 성장률 결합
        - :func:`dartlab.scan.builders.kr.payload.workforceToInsight` — 카드 변환
    """

    def _say(msg: str) -> None:
        if verbose:
            _log.info(msg)

    _say("1/6 직원 현황...")
    emp_map = scanEmployee()
    _say(f"  → {len(emp_map)}종목")

    _say("2/6 직원당 매출...")
    rpe_map = scanRevenuePerEmployee()
    _say(f"  → {len(rpe_map)}종목")

    _say("3/5 급여 vs 매출 성장률...")
    salMap = scanSalaryGrowth()
    revMap = scanRevenueGrowth()
    growth_df = computeSalaryVsRevenue(salMap, revMap)
    growth_dict: dict[str, dict] = {}
    for row in growth_df.iter_rows(named=True):
        growth_dict[row["stockCode"]] = row
    _say(f"  → {len(growth_dict)}종목")

    _say("4/6 고액 보수...")
    top_map = scanTopPay()
    _say(f"  → {len(top_map)}종목")

    _say("5/6 5억+ 개인별 보수...")
    high_map = scanHighPay()
    unreg_map = scanUnregExecPay()
    _say(f"  → {len(high_map)}종목 / 미등기 {len(unreg_map)}종목")

    # 합집합
    all_codes = set(emp_map) | set(rpe_map) | set(growth_dict) | set(top_map) | set(high_map) | set(unreg_map)

    results = []
    for code in all_codes:
        emp = emp_map.get(code, {})
        rpe = rpe_map.get(code)
        g = growth_dict.get(code, {})
        tp = top_map.get(code, {})
        hp = high_map.get(code, {})

        results.append(
            {
                "stockCode": code,
                "직원수": emp.get("직원수"),
                "평균급여_만원": emp.get("평균급여_만원"),
                "남녀격차": emp.get("남녀격차"),
                "근속_년": emp.get("근속_년"),
                "직원당매출_억": rpe,
                "급여성장률": g.get("급여성장률"),
                "매출성장률": g.get("매출성장률"),
                "급여매출괴리": g.get("급여매출괴리"),
                "최고보수_억": tp.get("최고보수_억"),
                "공개인원": tp.get("공개인원"),
                "최고개인보수_억": hp.get("최고개인보수_억"),
                "고액보수인원": hp.get("고액보수인원"),
                "미등기임원보수_억": unreg_map.get(code),
            }
        )

    schema = {
        "stockCode": pl.Utf8,
        "직원수": pl.Float64,
        "평균급여_만원": pl.Float64,
        "남녀격차": pl.Float64,
        "근속_년": pl.Float64,
        "직원당매출_억": pl.Float64,
        "급여성장률": pl.Float64,
        "매출성장률": pl.Float64,
        "급여매출괴리": pl.Float64,
        "최고보수_억": pl.Float64,
        "공개인원": pl.Float64,
        "최고개인보수_억": pl.Float64,
        "고액보수인원": pl.Float64,
        "미등기임원보수_억": pl.Float64,
    }
    df = pl.DataFrame(results, schema=schema)
    _say(f"인력 스캔 완료: {df.shape[0]}종목, 6/6")
    return df


__all__ = ["scanWorkforce"]
