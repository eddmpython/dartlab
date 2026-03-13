"""
실험 ID: 058-002
실험명: 로컬 finance 기준 ratio surface 전체 스윕

목적:
- 로컬 finance parquet 전체를 기준으로 ratio surface DataFrame 변환이 얼마나 안정적인지 측정
- `Company` 표면에 올린 `ratios`가 구조적으로 충분히 재현 가능한지 확인
- row 수가 지나치게 적은 회사군과 empty 범위를 파악한다

가설:
1. 로컬 finance 보유 종목 다수에서 ratio surface DataFrame 생성이 성공한다
2. 에러보다 empty와 short history가 문제의 중심이다
3. 대부분 종목은 30행 이상 시계열 ratio table을 가진다

방법:
1. 로컬 finance parquet 전체 목록 수집
2. `buildAnnual` → `calcRatioSeries` → `toSeriesDict` → `_ratioSeriesToDataFrame` 변환
3. 성공/empty, row 수, 연도 수를 집계

결과 (실험 후 작성):
- 전체 2,743개 finance 파일 기준:
  - 정상 DataFrame: 2,564
  - empty: 179
  - error: 0
  - 30행 이상: 2,106
  - 10행 미만: 2
  - 연도 5개 미만: 401

결론:
- ratio surface 변환 로직은 구조적으로 안정적이다
- 남는 품질 이슈는 코드 에러보다 연도 부족과 원천 공백 쪽에 가깝다
- 저행수 2개만 남았고, 둘 다 금융업/신규상장 축에 가깝다

실험일: 2026-03-13
"""

from __future__ import annotations

from _common import localFinanceCodes, ratioSurfaceFrame


def main(limit: int | None = None):
    codes = localFinanceCodes(limit=limit)

    summary = {
        "total": len(codes),
        "success": 0,
        "empty": 0,
        "errors": 0,
        "full_ge30": 0,
        "reduced_lt10": 0,
        "years_lt5": 0,
    }
    examples: list[tuple[str, int, int]] = []

    for code in codes:
        try:
            df, yearCount = ratioSurfaceFrame(code)
            if df is None or df.is_empty():
                summary["empty"] += 1
                continue

            summary["success"] += 1
            if df.height >= 30:
                summary["full_ge30"] += 1
            if df.height < 10:
                summary["reduced_lt10"] += 1
            if yearCount is not None and yearCount < 5:
                summary["years_lt5"] += 1
            if len(examples) < 12:
                examples.append((code, df.height, yearCount or 0))
        except Exception:
            summary["errors"] += 1

    print(summary)
    print(examples)


if __name__ == "__main__":
    main()
