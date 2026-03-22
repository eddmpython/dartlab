"""
실험 ID: 056-008
실험명: semantic 경계 패턴 커버리지 측정

목적:
- 세분화된 섹션 내부 경계 패턴이 삼성전자 특이값이 아니라 다른 대형주에서도 반복되는지 확인한다.

가설:
1. `가./나.`, `(1)/(2)`, 표 행(`|`) 패턴은 다수 기업에서 반복된다.
2. semantic unit 분해는 특정 기업 전용이 아니라 범용 규칙으로 설계 가능하다.

방법:
1. 대표 10개 기업의 최신 사업보고서에서 II장/III장 핵심 섹션 텍스트를 수집한다.
2. 패턴(`가.`, `(1)`, `|`, `☞`)의 존재 여부를 측정한다.

결과 (실험 후 작성):

- `가./나.` heading: 8/10
- `(1)/(2)` 번호 패턴: 8/10
- 표 row (`|`): 8/10
- `☞` 안내문: 1/10
결론:

- semantic unit 분해는 특정 기업 전용이 아니라 범용 규칙으로 설계 가능하다.
- 특히 `가./나.`, `(1)/(2)`, 표 전후 텍스트는 2차 경계 추출의 핵심 신호다.
실험일: 2026-03-11
"""

from __future__ import annotations

import re
from pathlib import Path

import polars as pl

TARGET_CODES = ["005930", "000660", "035420", "035720", "005380", "005490", "012330", "051910", "066570", "207940"]
TARGET_TITLES = {"1. 사업의 개요", "4. 매출 및 수주상황", "5. 위험관리 및 파생거래", "6. 주요계약 및 연구개발활동"}
PATTERNS = {
    "korean_heading": r"(?m)^[가-힣]\.\s+",
    "paren_number": r"(?m)^\(\d+\)",
    "table_row": r"(?m)^\|",
    "guide_arrow": r"☞",
}


def load_target_texts(stock_code: str) -> list[str]:
    root = Path(__file__).resolve().parents[2]
    path = root / "data" / "dart" / "docs" / f"{stock_code}.parquet"
    df = pl.read_parquet(path).with_columns(pl.col("year").cast(pl.Utf8))
    annual = df.filter(pl.col("report_type").str.contains("사업보고서"))
    latest_year = annual.get_column("year").max()
    if latest_year is None:
        return []
    rows = (
        annual.filter(pl.col("year") == latest_year)
        .filter(pl.col("section_title").is_in(TARGET_TITLES))
        .get_column("section_content")
        .to_list()
    )
    return rows


def main() -> None:
    hit_counts = {name: 0 for name in PATTERNS}
    for code in TARGET_CODES:
        texts = load_target_texts(code)
        merged = "\n".join(texts)
        for name, pattern in PATTERNS.items():
            if re.search(pattern, merged):
                hit_counts[name] += 1

    print("=" * 72)
    print("056-008 semantic 경계 패턴 커버리지")
    print("=" * 72)
    for name, count in hit_counts.items():
        print(f"{name}: {count}/{len(TARGET_CODES)}")


if __name__ == "__main__":
    main()
