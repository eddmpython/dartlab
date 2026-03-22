"""
실험 ID: 061-001
실험명: report pivot Result를 metric(행)×year(열) 와이드 DataFrame으로 변환

목적:
- 5개 pivot Result(dividend, employee, majorHolder, executive, audit)를
  finance와 동일한 metric(행)×year(열) 와이드 DataFrame으로 변환 가능한지 검증
- 나머지 23개 apiType 중 와이드 변환이 의미 있는 대상 식별
- 변환 후 DataFrame 구조가 finance BS/IS/CF와 동일 축인지 확인

가설:
1. 5개 pivot Result는 모두 toWide() 변환 가능 (years + 시계열 리스트 보유)
2. 나머지 23개 중 시계열 의미 있는 것은 10개 미만
3. 와이드 DataFrame의 컬럼은 연도 문자열 (finance와 동일)

방법:
1. 삼성전자(005930)로 5개 pivot 결과 조회
2. 각 Result에서 시계열 필드 추출 → metric(행)×year(열) DataFrame 생성
3. 나머지 23개 apiType에 대해 extractAnnual() 결과 확인
4. 와이드 변환 가능 여부 + 결과 구조 출력

결과 (실험 후 작성):
- 5개 pivot Result 모두 toWide() 변환 성공
  - dividend: 2행×10열 (주당현금배당금, 현금배당수익률)
  - employee: 3행×10열 (총직원수, 월평균급여, 연간총급여)
  - majorHolder: 1행×10열 (최대주주총지분율)
  - audit: 2행×10열 (감사의견, 감사법인) — 문자열
  - executive: 3행×1열 (snapshot, 시계열 아님)
- 나머지 23개 apiType: 데이터 있음 18개, 없음 6개
  - 단순 와이드 5개 (1행/년)
  - 그룹 와이드 7개 (다행/년, 집계 필요)
  - 텍스트/부적합 6개

결론:
- 5개 pivot Result의 toWide() 채택
- 범용 reportToWide() 함수로 단순 와이드 5개 자동 변환
- 그룹 와이드 7개는 향후 개별 처리
- 축: metric(행)×year(열) — finance와 동일

실험일: 2026-03-14
"""

import sys
import time

sys.path.insert(0, "src")

import polars as pl


def dividendToWide(result) -> pl.DataFrame | None:
    if result is None:
        return None
    years = [str(y) for y in result.years]
    rows = []
    for label, series in [
        ("주당현금배당금", result.dps),
        ("현금배당수익률(%)", result.dividendYield),
        ("주식배당", result.stockDividend),
        ("주식배당수익률(%)", result.stockDividendYield),
    ]:
        if any(v is not None for v in series):
            row = {"metric": label}
            for y, v in zip(years, series):
                row[y] = v
            rows.append(row)
    return pl.DataFrame(rows) if rows else None


def employeeToWide(result) -> pl.DataFrame | None:
    if result is None:
        return None
    years = [str(y) for y in result.years]
    rows = []
    for label, series in [
        ("총직원수", result.totalEmployee),
        ("월평균급여(천원)", result.avgMonthlySalary),
        ("연간총급여(백만원)", result.totalAnnualSalary),
    ]:
        if any(v is not None for v in series):
            row = {"metric": label}
            for y, v in zip(years, series):
                row[y] = v
            rows.append(row)
    return pl.DataFrame(rows) if rows else None


def majorHolderToWide(result) -> pl.DataFrame | None:
    if result is None:
        return None
    years = [str(y) for y in result.years]
    rows = []
    if any(v is not None for v in result.totalShareRatio):
        row = {"metric": "최대주주 총지분율(%)"}
        for y, v in zip(years, result.totalShareRatio):
            row[y] = v
        rows.append(row)
    return pl.DataFrame(rows) if rows else None


def auditToWide(result) -> pl.DataFrame | None:
    if result is None:
        return None
    years = [str(y) for y in result.years]
    rows = []
    for label, series in [
        ("감사의견", result.opinions),
        ("감사법인", result.auditors),
    ]:
        if any(v is not None for v in series):
            row = {"metric": label}
            for y, v in zip(years, series):
                row[y] = v
            rows.append(row)
    return pl.DataFrame(rows) if rows else None


def executiveToWide(result) -> pl.DataFrame | None:
    if result is None:
        return None
    rows = [
        {"metric": "총임원수", "latest": result.totalCount},
        {"metric": "사내이사", "latest": result.registeredCount},
        {"metric": "사외이사", "latest": result.outsideCount},
    ]
    return pl.DataFrame(rows)


def main():
    from dartlab.engines.company.dart.company import Company

    c = Company("005930")

    print("=" * 80)
    print("Phase 1: 5개 pivot Result → toWide() 변환")
    print("=" * 80)

    pivotTests = [
        ("dividend", c.report.dividend, dividendToWide),
        ("employee", c.report.employee, employeeToWide),
        ("majorHolder", c.report.majorHolder, majorHolderToWide),
        ("audit", c.report.audit, auditToWide),
        ("executive", c.report.executive, executiveToWide),
    ]

    for name, result, toWide in pivotTests:
        print(f"\n--- {name} ---")
        if result is None:
            print("  결과 없음")
            continue
        if hasattr(result, "years"):
            print(f"  years: {result.years}")
        wide = toWide(result)
        if wide is not None:
            print(f"  wide shape: {wide.shape}")
            print(wide)
        else:
            print("  wide 변환 실패")

    print()
    print("=" * 80)
    print("Phase 2: 나머지 apiType extractAnnual 확인")
    print("=" * 80)

    from dartlab.engines.company.dart.report.types import API_TYPES
    pivotNames = {"dividend", "employee", "majorHolder", "executive", "audit"}
    remaining = [t for t in API_TYPES if t not in pivotNames]

    available = []
    empty = []

    for apiType in remaining:
        df = c.report.extractAnnual(apiType)
        if df is not None and not df.is_empty():
            available.append((apiType, df))
        else:
            empty.append(apiType)

    print(f"\n데이터 있음: {len(available)}개")
    print(f"데이터 없음: {len(empty)}개 → {empty}")

    for apiType, df in available:
        print(f"\n--- {apiType} ---")
        print(f"  shape: {df.shape}")
        print(f"  columns: {df.columns}")
        years = sorted(df["year"].unique().to_list())
        print(f"  years: {years}")
        print(f"  rows/year: {df.height / len(years):.1f}" if years else "  no years")

    print()
    print("=" * 80)
    print("Phase 3: 와이드 변환 가능성 분류")
    print("=" * 80)

    for apiType, df in available:
        years = sorted(df["year"].unique().to_list())
        numericCols = [c for c in df.columns
                       if df[c].dtype in (pl.Float64, pl.Int32, pl.Int64)
                       and c not in ("year", "quarterNum")]
        strCols = [c for c in df.columns
                   if df[c].dtype == pl.Utf8
                   and c not in ("stlm_dt", "apiType", "stockCode", "quarter")]
        rowsPerYear = df.height / len(years) if years else 0

        if rowsPerYear <= 1.5 and numericCols:
            kind = "단순 와이드 (1행/년, 숫자 컬럼 → metric)"
        elif rowsPerYear > 1.5 and numericCols:
            kind = "그룹 와이드 (다행/년, 집계 필요)"
        else:
            kind = "텍스트 주도 (와이드 부적합)"

        print(f"  {apiType:<30} {kind}")
        print(f"    rows/year={rowsPerYear:.1f}, numeric={numericCols}, str={strCols[:3]}")


if __name__ == "__main__":
    main()
