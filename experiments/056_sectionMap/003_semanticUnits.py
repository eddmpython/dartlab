"""
실험 ID: 056-003
실험명: semantic unit 후보 추출

목적:
- 세분화된 섹션 내부에서도 추가 분해가 필요한지 실제 텍스트 기준으로 확인한다.
- 삼성전자 2022 사업보고서의 대표 섹션에서 의미 단위 경계 패턴을 추출한다.

가설:
1. 세분화된 섹션 내부에도 `가.`, `(1)`, 표 앞 설명, 표 뒤 설명 같은 반복 경계가 존재한다.
2. 이 경계는 canonicalSubsection 아래 semanticUnit 수준으로 재사용 가능하다.

방법:
1. 삼성전자 2022 사업보고서에서 대표 섹션 4개를 선택한다.
2. 정규식으로 heading/bullet/table 패턴을 추출한다.
3. 섹션별 경계 패턴 개수와 예시를 출력한다.

결과 (실험 후 작성):

- 분석 섹션: `1. 사업의 개요`, `4. 매출 및 수주상황`, `5. 위험관리 및 파생거래`, `6. 주요계약 및 연구개발활동`
- `1. 사업의 개요` → `☞` 안내문 중심 (`guide_arrow=2`)
- `4. 매출 및 수주상황` → `가.` 6개, `(1)` 8개, 테이블행 77개
- `5. 위험관리 및 파생거래` → `가.` 3개, `(1)` 6개, 테이블행 38개
결론:

- 세분화된 section 내부에도 추가 semantic unit 경계가 반복적으로 존재한다.
- 다음 단계는 title 매핑이 아니라 `가./나.`, `(1)/(2)`, 표 전후 설명, 안내문(`☞`)을 이용한 내부 분해 규칙 검증이다.
실험일: 2026-03-11
"""

from __future__ import annotations

import re
from pathlib import Path

import polars as pl

PATTERNS: dict[str, str] = {
    "korean_heading": r"(?m)^([가-힣])\.\s+",
    "paren_number": r"(?m)^\((\d+)\)",
    "table_row": r"(?m)^\|",
    "guide_arrow": r"☞",
}

TARGET_TITLES = [
    "1. 사업의 개요",
    "4. 매출 및 수주상황",
    "5. 위험관리 및 파생거래",
    "6. 주요계약 및 연구개발활동",
]


def load_section_map() -> dict[str, str]:
    root = Path(__file__).resolve().parents[2]
    path = root / "data" / "dart" / "docs" / "005930.parquet"
    df = pl.read_parquet(path).with_columns(pl.col("year").cast(pl.Utf8))
    rows = (
        df.filter((pl.col("year") == "2022") & pl.col("report_type").str.contains("사업보고서"))
        .filter(pl.col("section_title").is_in(TARGET_TITLES))
        .select(["section_title", "section_content"])
        .to_dicts()
    )
    return {row["section_title"]: row["section_content"] for row in rows}


def count_patterns(text: str) -> dict[str, int]:
    return {name: len(re.findall(pattern, text)) for name, pattern in PATTERNS.items()}


def sample_lines(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    samples: list[str] = []
    for line in lines:
        if re.match(r"^[가-힣]\.\s+", line) or re.match(r"^\(\d+\)", line) or line.startswith("|") or "☞" in line:
            samples.append(line[:120])
        if len(samples) >= 6:
            break
    return samples


def main() -> None:
    section_map = load_section_map()
    print("=" * 72)
    print("056-003 semantic unit 후보 추출")
    print("=" * 72)
    for title in TARGET_TITLES:
        text = section_map[title]
        counts = count_patterns(text)
        print(f"\n[{title}]")
        print(counts)
        for sample in sample_lines(text):
            print(" -", sample)


if __name__ == "__main__":
    main()
