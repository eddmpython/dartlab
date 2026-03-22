"""실험 ID: 013
실험명: signal 공식 6축 승격 전 재검증

목적:
- 현재 local docs corpus 기준으로 `signal` 축 승격 조건을 다시 검증
- 공식 scan keyword set 기준으로 coverage, 시계열 길이, 대표 키워드 변곡 재현성을 확인
- `008_narrativeSignal.py`의 seed 결과를 현재 엔진 구현 기준으로 재확인

가설:
1. docs coverage가 300사 이상이다
2. 5년 이상 시계열이 확보된다
3. 대표 키워드 3개 이상에서 연도별 변곡이 재현된다

방법:
1. `dartlab.engines.company.dart.scan.signal`의 공식 keyword set과 reader를 사용
2. docs parquet 319개를 전수 스캔해 raw keyword rows를 생성
3. 연도별 trend와 keyword first appearance를 함께 계산
4. AI, ESG, 2차전지를 대표 키워드로 gate를 판정

결과 (실험 후 작성):
- docs files 319개, keyword raw rows 36,141건, hit companies 319사
- active keywords 41개, year range 1999~2026
- AI:
  - 기업수 2023 147 -> 2024 182 -> 2025 263
  - first appearance 2023 +36 / 2024 +38 / 2025 +79
- ESG:
  - 기업수 2021 80 -> 2022 100 -> 2023 127 -> 2024 160 -> 2025 203
  - first appearance 2021 +60 / 2022 +20 / 2023 +29 / 2024 +36 / 2025 +42
- 2차전지:
  - 기업수 2023 39 -> 2024 52 -> 2025 73
  - first appearance 2023 +14 / 2024 +13 / 2025 +28
- gate 판정:
  - coverage 319사 -> 통과
  - 시계열 1999~2026 -> 통과
  - 대표 키워드 3개 변곡 재현 -> 통과

결론:
- 가설1,2,3 모두 채택
- `signal`은 현재 docs corpus 기준으로 공식 scan 축 승격 요건을 충족한다
- 다만 coverage 범위는 local docs corpus에 의존하므로, finance/report 기반 4축과 같은 전종목 완전 커버리지로 해석하면 안 된다

실험일: 2026-03-20
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from dartlab import config
from dartlab.engines.company.dart.scan.signal import _ALL_KEYWORDS, _read_signal_text


def buildRawSignalRows() -> pl.DataFrame:
    """공식 signal keyword set 기준 raw rows 생성."""
    docsDir = Path(config.dataDir) / "dart" / "docs"
    rows: list[dict[str, object]] = []

    for path in sorted(docsDir.glob("*.parquet")):
        df = _read_signal_text(path)
        if df is None or df.is_empty():
            continue

        periodCounts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for yearVal, textVal in df.iter_rows():
            year = str(yearVal)[:4] if yearVal is not None else ""
            text = str(textVal) if textVal is not None else ""
            if year and text:
                for keyword in _ALL_KEYWORDS:
                    count = text.count(keyword)
                    if count > 0:
                        periodCounts[year][keyword] += count

        for year, keywordCounts in periodCounts.items():
            for keyword, count in keywordCounts.items():
                category = _ALL_KEYWORDS[keyword]
                if count > 0:
                    rows.append(
                        {
                            "stockCode": path.stem,
                            "year": year,
                            "keyword": keyword,
                            "category": category,
                            "count": count,
                        }
                    )

    return pl.DataFrame(rows)


if __name__ == "__main__":
    raw = buildRawSignalRows()
    docsFiles = len(list((Path(config.dataDir) / "dart" / "docs").glob("*.parquet")))

    trend = (
        raw.group_by(["year", "keyword", "category"])
        .agg(
            [
                pl.col("stockCode").n_unique().alias("companies"),
                pl.col("count").sum().alias("totalMentions"),
            ]
        )
        .sort(["keyword", "year"])
    )
    emergence = (
        raw.group_by(["stockCode", "keyword"])
        .agg(pl.col("year").min().alias("firstYear"))
        .group_by(["keyword", "firstYear"])
        .agg(pl.col("stockCode").n_unique().alias("newCompanies"))
        .sort(["keyword", "firstYear"])
    )

    print("=== signal revalidation ===")
    print(
        f"docsFiles={docsFiles} rawRows={raw.height} hitCompanies={raw['stockCode'].n_unique()} "
        f"activeKeywords={raw['keyword'].n_unique()} yearRange={raw['year'].min()}~{raw['year'].max()}"
    )
    print()
    for keyword in ["AI", "ESG", "2차전지"]:
        print(f"[{keyword}] trend")
        print(trend.filter(pl.col("keyword") == keyword).select(["year", "companies", "totalMentions"]).tail(10))
        print(f"[{keyword}] emergence")
        print(emergence.filter(pl.col("keyword") == keyword).tail(10))
        print()
