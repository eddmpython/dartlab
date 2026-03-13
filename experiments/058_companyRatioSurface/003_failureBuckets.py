"""
실험 ID: 058-003
실험명: ratio surface 실패군 자동 분류

목적:
- `10행 미만`, `연도 5개 미만`, `empty` 종목을 원인 버킷으로 분류한다
- 금융업 정상 축소와 비금융 이상축소를 구분한다
- 최종 STATUS 문서에 들어갈 실패군 표를 만든다

가설:
1. `10행 미만` 종목 대부분은 금융업 정상 축소 또는 짧은 상장 이력이다
2. `비금융 이상축소`는 거의 없거나 극소수다
3. `empty`는 신규상장/메타부재/원천공백으로 나눌 수 있다

방법:
1. 로컬 finance 전체 파일 순회
2. ratio surface DataFrame row 수와 year 수 측정
3. kindList 메타를 붙여 업종/시장/상장일 확인
4. `정상 / 금융업 정상 축소 / 연도부족 / 비금융 이상축소 / 원천공백-*`으로 분류

결과 (실험 후 작성):
- 전체 분류:
  - 정상: 2,163
  - 연도부족: 399
  - 금융업 정상 축소: 2
  - 원천공백: 89
  - 원천공백-신규상장: 62
  - 원천공백-메타부재: 28
  - 비금융 이상축소: 0

결론:
- 현재 관찰 범위에서는 `비금융 이상축소`가 없다
- 금융업 저행수는 정상 축소로 설명 가능하다
- row가 적지만 연도도 짧은 일부 비금융 사례는 `연도부족`으로 보는 편이 맞다
- empty는 주로 신규상장, 메타부재, 장기 원천공백이다

실험일: 2026-03-13
"""

from __future__ import annotations

import polars as pl

from _common import classifyStatus, kindMeta, localFinanceCodes, ratioSurfaceFrame


def main(limit: int | None = None):
    meta = kindMeta()
    rows: list[dict[str, object]] = []

    for code in localFinanceCodes(limit=limit):
        info = meta.get(code, {"corpName": None, "market": None, "industry": None, "listedAt": None})
        df, yearCount = ratioSurfaceFrame(code)
        rowCount = None if df is None else df.height
        status = classifyStatus(
            rowCount=rowCount,
            yearCount=yearCount,
            industry=info["industry"],
            listedAt=info["listedAt"],
            corpName=info["corpName"],
        )
        rows.append({
            "code": code,
            "corpName": info["corpName"],
            "market": info["market"],
            "industry": info["industry"],
            "listedAt": info["listedAt"],
            "status": status,
            "rowCount": rowCount,
            "yearCount": yearCount,
        })

    df = pl.DataFrame(rows)
    print(df.group_by("status").agg(pl.len().alias("count")).sort(["status"]))
    print()
    print("[ 저행수 / empty 샘플 ]")
    focus = df.filter(pl.col("status") != "정상").sort(["status", "code"])
    print(focus.head(40))


if __name__ == "__main__":
    main()
