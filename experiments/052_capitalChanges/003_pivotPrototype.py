"""실험 ID: 003
실험명: SCE 피벗 프로토타입

목적:
- 002의 정규화 함수를 사용하여 실제 연도별 자본변동 매트릭스 생성
- 피벗 결과의 데이터 구조 설계 및 검증
- 기초/기말 자본 정합성 검증 (기초 + 변동 = 기말)
- 다양한 회사에서 피벗 동작 확인

가설:
1. 정규화된 (cause, detail) 조합으로 피벗하면 연도별 자본변동 매트릭스가 생성될 것
2. 기초자본 + 변동사유 합계 ≈ 기말자본 (BS의 equity와도 일치)
3. CFS/OFS 선택 로직은 BS/IS와 동일하게 적용 가능할 것

방법:
1. 삼성전자 SCE → 연도별 피벗 → 매트릭스 출력
2. 기초+변동=기말 검증
3. 다양한 회사 테스트

결과:
1. 피벗 결과 구조 — 2가지 출력 형태:
   a) pivotSce(): matrix[year][cause][detail] = 금액  (연도별 매트릭스)
   b) pivotSceAnnual(): series["SCE"]["cause__detail"] = [v1, v2, ...]  (연도별 시계열)

2. 삼성전자 결과:
   - 11년 × 20사유 × 7항목 = 128개 시계열 키
   - 2023: 기초+변동=기말 **차=0억** (완벽 매칭)
   - 2024: 차=-218,241억 (배당 부호 불일치 — 원본 데이터 이슈)
   - 2025: 차=-250,434억 (1Q만 있어 연간 누적 미완료)

3. 다회사 검증:
   | 회사 | 연도수 | 사유수 | 항목수 | 최신년도 차이(%) |
   |------|--------|--------|--------|-----------------|
   | 삼성전자 | 11 | 20 | 7 | 6.06% |
   | SK하이닉스 | 11 | 21 | 8 | 1.86% |
   | KB금융 | 3 | 20 | 9 | 4.13% |
   | 동화약품 | 8 | 16 | 8 | 0.76% |
   | 에코프로비엠 | 6 | 21 | 8 | 4.38% |
   | 포스코퓨처엠 | 11 | 23 | 9 | 2.19% |

4. 기초+변동=기말 차이 원인:
   - 배당 부호 불일치 (일부 연도 양수/음수 혼재)
   - equity_change_total/소유주거래합계를 제외하지만 원본에서 중복 포함 가능
   - 2025년은 1Q만 있어서 연간 누적 미완성

5. maxQ 전략:
   - 각 연도에서 가장 높은 분기 보고서만 사용 (4Q 우선)
   - 2025년은 1Q만 → 1Q 데이터 사용 (YTD 누적)

결론:
1. 가설 1 채택 — (cause, detail) 조합 피벗이 정상 동작
2. 가설 2 부분 채택 — 4Q 데이터에서 기초+변동=기말 정합성 있음.
   단 배당/자기주식 부호가 연도별로 불일치(DART 원본 이슈)
3. 가설 3 채택 — CFS/OFS 선택 로직은 fs_div 필터로 동일하게 적용 가능
4. 프로덕션 배치 시 고려사항:
   a) 배당 부호 정규화 필요 (양수→음수 통일)
   b) equity_change_total 같은 소계 행은 별도 처리 필요
   c) 연도별 시계열과 매트릭스 형태 모두 제공 가능
   d) 2가지 API: pivotSce(매트릭스), pivotSceAnnual(시계열)

실험일: 2026-03-10
"""

from __future__ import annotations

import importlib.util
import pathlib
from collections import Counter
from typing import Optional

import polars as pl

_modPath = pathlib.Path(__file__).parent / "002_detailNormalize.py"
_spec = importlib.util.spec_from_file_location("detailNormalize", _modPath)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
_normalizeCause = _mod._normalizeCause
_normalizeDetail = _mod._normalizeDetail

QUARTER_ORDER = {"1분기": 1, "2분기": 2, "3분기": 3, "4분기": 4}


def _parseAmount(val) -> Optional[float]:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().replace(",", "")
    if not s or s == "-":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def pivotSce(
    stockCode: str,
    fsDivPref: str = "CFS",
) -> Optional[tuple[dict[str, dict[str, dict[str, Optional[float]]]], list[str]]]:
    """SCE 원본 → 연도별 자본변동 매트릭스.

    Returns:
        (matrix, years)
        matrix[year][cause_snakeId][detail_snakeId] = 금액
    """
    from dartlab.core.dataLoader import loadData

    df = loadData(stockCode, category="finance")
    if df is None or df.is_empty():
        return None

    if "sj_div" not in df.columns:
        return None

    sce = df.filter(pl.col("sj_div") == "SCE")
    if sce.is_empty():
        return None

    sce = _applyCfsPriority(sce, fsDivPref)

    for col in ["thstrm_amount"]:
        if col in sce.columns:
            sce = sce.with_columns(
                pl.when(
                    pl.col(col).is_not_null()
                    & (pl.col(col).str.strip_chars() != "")
                    & (pl.col(col).str.strip_chars() != "-")
                )
                .then(pl.col(col).str.strip_chars().str.replace_all(",", "").cast(pl.Float64, strict=False))
                .otherwise(pl.lit(None).cast(pl.Float64))
                .alias(col)
            )

    yearMaxQ: dict[str, int] = {}
    for row in sce.iter_rows(named=True):
        year = row.get("bsns_year", "")
        reprtNm = row.get("reprt_nm", "")
        qNum = QUARTER_ORDER.get(reprtNm, 0)
        if qNum > 0:
            yearMaxQ[year] = max(yearMaxQ.get(year, 0), qNum)

    yearSet = set()
    matrix: dict[str, dict[str, dict[str, Optional[float]]]] = {}

    for row in sce.iter_rows(named=True):
        year = row.get("bsns_year", "")
        reprtNm = row.get("reprt_nm", "")
        qNum = QUARTER_ORDER.get(reprtNm, 0)
        if qNum == 0:
            continue

        maxQ = yearMaxQ.get(year, 4)
        if qNum != maxQ:
            continue

        nm = row.get("account_nm", "") or ""
        detail = row.get("account_detail", "") or ""
        amount = row.get("thstrm_amount")

        cause = _normalizeCause(nm)
        component = _normalizeDetail(detail)

        if cause.startswith("unmapped:") or component.startswith("unmapped:"):
            continue

        yearSet.add(year)
        if year not in matrix:
            matrix[year] = {}
        if cause not in matrix[year]:
            matrix[year][cause] = {}

        if amount is not None:
            matrix[year][cause][component] = amount

    years = sorted(yearSet)
    return matrix, years


def _applyCfsPriority(df: pl.DataFrame, pref: str) -> pl.DataFrame:
    if "fs_div" not in df.columns:
        return df

    available = set(df["fs_div"].drop_nulls().unique().to_list())
    if pref not in available:
        if pref == "CFS" and "OFS" in available:
            pref = "OFS"
        elif pref == "OFS" and "CFS" in available:
            pref = "CFS"
        elif available:
            pref = next(iter(available))
        else:
            return df

    return df.filter(pl.col("fs_div") == pref)


def pivotSceAnnual(
    stockCode: str,
    fsDivPref: str = "CFS",
) -> Optional[tuple[dict[str, dict[str, list[Optional[float]]]], list[str]]]:
    """SCE → 연도별 시계열 (BS/IS/CF와 유사한 출력 형태).

    Returns:
        (series, years)
        series["SCE"]["{cause}__{detail}"] = [v2016, v2017, ..., v2024]
    """
    result = pivotSce(stockCode, fsDivPref)
    if result is None:
        return None

    matrix, years = result
    nYears = len(years)
    yearIdx = {y: i for i, y in enumerate(years)}

    allKeys = set()
    for year in matrix:
        for cause in matrix[year]:
            for detail in matrix[year][cause]:
                allKeys.add((cause, detail))

    series: dict[str, list[Optional[float]]] = {}
    for cause, detail in sorted(allKeys):
        key = f"{cause}__{detail}"
        vals: list[Optional[float]] = [None] * nYears
        for year in matrix:
            idx = yearIdx[year]
            val = matrix[year].get(cause, {}).get(detail)
            vals[idx] = val
        series[key] = vals

    return {"SCE": series}, years


def exploreSamsung():
    result = pivotSce("005930")
    if result is None:
        print("SCE 데이터 없음")
        return

    matrix, years = result
    print(f"=== 삼성전자 SCE 피벗 ===")
    print(f"연도: {years}")
    print()

    CORE_CAUSES = [
        "beginning_equity", "net_income", "dividends",
        "treasury_acquired", "fx_translation", "fvoci_valuation",
        "remeasurement_db", "ending_equity",
    ]
    CORE_DETAILS = [
        "share_capital", "share_premium", "retained_earnings",
        "other_equity", "owners_equity", "noncontrolling_interest", "total",
    ]

    for year in years[-3:]:
        print(f"\n--- {year} ---")
        yearData = matrix.get(year, {})

        header = f"{'변동사유':25s}"
        for d in CORE_DETAILS:
            header += f" {d:>18s}"
        print(header)
        print("-" * len(header))

        for cause in CORE_CAUSES:
            causeData = yearData.get(cause, {})
            if not causeData:
                continue
            line = f"{cause:25s}"
            for d in CORE_DETAILS:
                val = causeData.get(d)
                if val is not None:
                    line += f" {val/1e8:>18,.0f}"
                else:
                    line += f" {'–':>18s}"
            print(line)

    print()
    print("--- 기초+변동=기말 검증 ---")
    for year in years[-3:]:
        yearData = matrix.get(year, {})
        beginTotal = yearData.get("beginning_equity", {}).get("total")
        endTotal = yearData.get("ending_equity", {}).get("total")
        if beginTotal is not None and endTotal is not None:
            diff = endTotal - beginTotal
            changes = 0
            for cause, details in yearData.items():
                if cause in ("beginning_equity", "ending_equity", "adjusted_beginning", "equity_change_total"):
                    continue
                val = details.get("total")
                if val is not None:
                    changes += val
            gap = diff - changes
            print(f"  {year}: 기초={beginTotal/1e8:,.0f}억 → 기말={endTotal/1e8:,.0f}억"
                  f"  차이={diff/1e8:,.0f}억  변동합={changes/1e8:,.0f}억  차={gap/1e8:,.0f}억")


def exploreMultiple():
    from dartlab import config

    codes = [
        ("005930", "삼성전자"),
        ("000660", "SK하이닉스"),
        ("105560", "KB금융"),
        ("000020", "동화약품"),
        ("247540", "에코프로비엠"),
        ("003670", "포스코퓨처엠"),
    ]

    for code, name in codes:
        result = pivotSce(code)
        if result is None:
            print(f"{name}({code}): SCE 없음")
            continue

        matrix, years = result

        allCauses = set()
        allDetails = set()
        for year in matrix:
            for cause in matrix[year]:
                allCauses.add(cause)
                for detail in matrix[year][cause]:
                    allDetails.add(detail)

        print(f"\n{name}({code}): {len(years)}년 × {len(allCauses)}사유 × {len(allDetails)}항목")

        lastYear = years[-1]
        yearData = matrix.get(lastYear, {})
        beginTotal = yearData.get("beginning_equity", {}).get("total")
        endTotal = yearData.get("ending_equity", {}).get("total")
        if beginTotal is not None and endTotal is not None:
            diff = endTotal - beginTotal
            changes = 0
            for cause, details in yearData.items():
                if cause in ("beginning_equity", "ending_equity", "adjusted_beginning", "equity_change_total"):
                    continue
                val = details.get("total")
                if val is not None:
                    changes += val
            gap = diff - changes
            pct = abs(gap / endTotal * 100) if endTotal else 0
            print(f"  {lastYear}: 기초={beginTotal/1e8:,.0f}억 기말={endTotal/1e8:,.0f}억"
                  f"  변동합={changes/1e8:,.0f}억  차={gap/1e8:,.0f}억 ({pct:.2f}%)")


def testAnnualSeries():
    result = pivotSceAnnual("005930")
    if result is None:
        print("SCE 시계열 없음")
        return

    series, years = result
    sceData = series["SCE"]
    print(f"\n=== 삼성전자 SCE 연도별 시계열 ===")
    print(f"연도: {years}")
    print(f"키 수: {len(sceData)}")

    print("\n--- 핵심 시계열 (억원) ---")
    coreKeys = [
        "beginning_equity__total",
        "ending_equity__total",
        "net_income__total",
        "dividends__total",
        "treasury_acquired__total",
        "net_income__retained_earnings",
        "dividends__retained_earnings",
    ]
    for key in coreKeys:
        vals = sceData.get(key)
        if vals is None:
            continue
        vStr = "  ".join(
            f"{v/1e8:>10,.0f}" if v is not None else f"{'–':>10s}"
            for v in vals
        )
        print(f"  {key:40s}: {vStr}")


if __name__ == "__main__":
    exploreSamsung()
    print("\n" + "=" * 60 + "\n")
    exploreMultiple()
    print("\n" + "=" * 60 + "\n")
    testAnnualSeries()
