"""
실험 ID: 045-001
실험명: Report parquet 스키마 탐색

목적:
- report parquet의 apiType별 데이터 구조 파악
- 각 apiType별 유효 컬럼(non-null) 목록 추출
- 숫자형 컬럼 vs 문자형 컬럼 구분
- 종목간 스키마 일관성 확인

가설:
1. 모든 종목이 동일한 22개 apiType을 갖는다
2. apiType별 유효 컬럼 셋이 종목간 동일하다
3. 숫자처럼 보이는 문자열 컬럼이 존재한다

방법:
1. 삼성전자(005930) 기준으로 apiType별 유효 컬럼 추출
2. SK하이닉스(000660), 네이버(035420), LG화학(051910) 대조
3. 각 apiType별 숫자 변환 가능 컬럼 식별

결과:
- 22개 apiType 모두 4개 종목 동일
- apiType별 유효 컬럼 셋 종목간 완전 일치
- 숫자형 컬럼 목록 아래 출력

결론:
- report parquet은 매우 일관된 스키마
- apiType별 필터 + null 컬럼 drop으로 깔끔한 DataFrame 추출 가능
- 숫자 파싱 대상 컬럼을 apiType별로 사전 정의할 필요 있음

실험일: 2026-03-09
"""

import polars as pl
from pathlib import Path

REPORT_DIR = Path(r"C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\data\dartData\report")
META_COLS = {"rcept_no", "corp_cls", "corp_code", "corp_name", "stockCode", "corpCode", "year", "quarter", "apiType", "apiName", "fsDiv", "collectStatus"}

CODES = ["005930", "000660", "035420", "051910"]


def getValidCols(df: pl.DataFrame, apiType: str) -> list[str]:
    sub = df.filter(pl.col("apiType") == apiType)
    valid = []
    for c in sub.columns:
        if c in META_COLS:
            continue
        if sub[c].null_count() < sub.height:
            valid.append(c)
    return valid


def isNumericCol(series: pl.Series) -> bool:
    nonNull = series.drop_nulls().filter(series.drop_nulls() != "")
    if nonNull.len() == 0:
        return False
    sample = nonNull.head(min(20, nonNull.len())).to_list()
    numCount = 0
    for v in sample:
        cleaned = str(v).replace(",", "").replace("-", "").strip()
        if cleaned == "":
            numCount += 1
            continue
        try:
            float(cleaned)
            numCount += 1
        except ValueError:
            pass
    return numCount / len(sample) >= 0.7


if __name__ == "__main__":
    print("=" * 60)
    print("1. apiType 일관성 체크")
    print("=" * 60)
    allApiTypes = {}
    for code in CODES:
        df = pl.read_parquet(REPORT_DIR / f"{code}.parquet")
        types = sorted(df["apiType"].unique().to_list())
        allApiTypes[code] = types
        print(f"  {code}: {len(types)} apiTypes")

    ref = allApiTypes[CODES[0]]
    for code in CODES[1:]:
        match = allApiTypes[code] == ref
        print(f"  {CODES[0]} vs {code}: {'MATCH' if match else 'DIFFER'}")

    print()
    print("=" * 60)
    print("2. apiType별 유효 컬럼 + 숫자형 식별")
    print("=" * 60)

    df0 = pl.read_parquet(REPORT_DIR / f"{CODES[0]}.parquet")

    for apiType in ref:
        validCols = getValidCols(df0, apiType)
        sub = df0.filter(pl.col("apiType") == apiType)

        numCols = []
        strCols = []
        for c in validCols:
            if c == "stlm_dt":
                strCols.append(c)
                continue
            if isNumericCol(sub[c]):
                numCols.append(c)
            else:
                strCols.append(c)

        print(f"\n--- {apiType} ({sub.height}rows) ---")
        print(f"  str: {strCols}")
        print(f"  num: {numCols}")

    print()
    print("=" * 60)
    print("3. 종목간 유효 컬럼 일치 확인")
    print("=" * 60)

    for apiType in ref:
        colSets = []
        for code in CODES:
            df = pl.read_parquet(REPORT_DIR / f"{code}.parquet")
            cols = set(getValidCols(df, apiType))
            colSets.append(cols)

        allSame = all(cs == colSets[0] for cs in colSets[1:])
        if not allSame:
            diffs = set()
            for cs in colSets[1:]:
                diffs |= colSets[0].symmetric_difference(cs)
            print(f"  {apiType}: DIFFER — {diffs}")
        else:
            print(f"  {apiType}: MATCH ({len(colSets[0])} cols)")
