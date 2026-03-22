"""
실험 ID: 058-004
실험명: 비금융 이상축소 케이스 원인 추적

목적:
- `비금융 이상축소`로 분류된 종목만 깊게 파고들어 원인을 특정한다
- row가 줄어드는 단계가 `buildAnnual / calcRatioSeries / toDataFrame / show("ratios")` 중 어디인지 확인한다
- 후속 조치가 필요한지 결정한다

가설:
1. 현재 데이터셋에서는 `비금융 이상축소`가 없을 가능성이 높다
2. 존재하더라도 원천 데이터 결손 또는 매핑 부족 중 하나로 귀결될 것이다

방법:
1. `058-003`과 동일 기준으로 전체 파일 분류
2. `비금융 이상축소`만 추출
3. 각 종목에 대해 annual availability, ratio dict field 수, DataFrame row 수를 단계별로 비교

결과 (실험 후 작성):
- 비금융 이상축소 종목: 0개
- 현재 데이터셋에서는 추가 원인 추적 대상이 발견되지 않았다

결론:
- 현 시점에서 `ratios` surface를 막는 비금융 이상축소 문제는 없다
- 후속 구현은 금융업 전용 ratio set 필요 여부 판단에 집중하면 된다

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
        if status != "비금융 이상축소":
            continue

        rows.append({
            "code": code,
            "corpName": info["corpName"],
            "market": info["market"],
            "industry": info["industry"],
            "rowCount": rowCount,
            "yearCount": yearCount,
        })

    df = pl.DataFrame(rows) if rows else pl.DataFrame(
        schema={
            "code": pl.Utf8,
            "corpName": pl.Utf8,
            "market": pl.Utf8,
            "industry": pl.Utf8,
            "rowCount": pl.Int64,
            "yearCount": pl.Int64,
        }
    )
    print(df)
    print()
    print({"nonFinancialAnomalies": df.height})


if __name__ == "__main__":
    main()
