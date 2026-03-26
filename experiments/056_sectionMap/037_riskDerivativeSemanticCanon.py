"""
실험 ID: 056-037
실험명: riskDerivative semantic unit canonicalization 초안

목적:
- 공통 canonical section 하나를 골라 내부 semantic unit까지 stable id로 표준화할 수 있는지 검증한다.
- section map 다음 단계인 `canonicalSection -> canonicalSubsection -> semanticUnit` 흐름을 실제 데이터로 올린다.

가설:
1. `riskDerivative`는 `가./나.`와 `(1)/(2)` 패턴이 반복되어 semantic unit canonicalization에 적합하다.
2. latest annual 기준 다기업에서 핵심 risk semantic unit을 안정적으로 포착할 수 있다.

방법:
1. latest annual 보고서에서 `5. 위험관리 및 파생거래`가 `riskDerivative`로 매핑되는 row를 수집한다.
2. `가./나.` 및 `(1)/(2)`와 괄호형 리스크 label을 기준으로 semantic unit를 분리한다.
3. label 정규화 후 stable semantic id를 부여한다.
4. canonical hit 수와 미매핑 label을 집계한다.

결과 (실험 후 작성):
- matched section rows: `223`
- companies: `223`
- extracted semantic rows: `1,701`
- canonical hit ratio: `0.689`
- canonical semantic ids: `11`
- top semantic ids:
  - `marketRisk`: `223`
  - `creditRisk`: `223`
  - `liquidityRisk`: `223`
  - `riskManagementPolicy`: `222`
  - `majorRiskManagement`: `222`

결론:
- `riskDerivative`는 company-level canonical section 아래 semantic unit 축까지 표준화할 수 있는 대표 사례로 적합하다.
- 아직 세부 괄호형 label과 table-before/after narrative를 더 흡수해야 하지만, core risk profile 축은 이미 안정적으로 잡힌다.
- 따라서 다음 단계는 topic별로 이런 semantic canonicalizer를 누적해 canonical report profile을 더 깊게 만드는 것이다.

실험일: 2026-03-12
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import polars as pl

from dartlab.providers.dart.docs.sections.mapper import mapSectionTitle, stripSectionPrefix

RE_MAJOR = re.compile(r"^([가-힣])\.\s+(.+)$")
RE_MINOR = re.compile(r"^\((\d+)\)\s*(.+)$")
RE_PAREN_LABEL = re.compile(r"^\(([^)]+)\)$")

SEMANTIC_OVERRIDES = {
    "재무위험관리정책": "riskManagementPolicy",
    "위험관리정책": "riskManagementPolicy",
    "주요재무위험관리": "majorRiskManagement",
    "재무위험관리요소": "majorRiskManagement",
    "시장위험": "marketRisk",
    "시장위험과위험관리": "marketRisk",
    "환율변동위험": "foreignExchangeRisk",
    "이자율변동위험": "interestRateRisk",
    "이자율위험": "interestRateRisk",
    "주가변동위험": "equityPriceRisk",
    "신용위험": "creditRisk",
    "신용위험관리": "creditRisk",
    "유동성위험": "liquidityRisk",
    "유동성위험관리": "liquidityRisk",
    "자본위험": "capitalRisk",
    "자본위험관리": "capitalRisk",
    "파생상품및위험회피회계": "derivativesAndHedgeAccounting",
    "파생상품및풋백옵션등거래현황": "derivativesAndStructuredTrades",
    "파생상품등거래현황": "derivativesAndStructuredTrades",
    "리스크관리": "riskManagement",
}


def root_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def docs_dir() -> Path:
    return root_dir() / "data" / "dart" / "docs"


def normalize_label(label: str) -> str:
    text = stripSectionPrefix(label)
    text = RE_MAJOR.sub(lambda m: m.group(2), text)
    text = RE_MINOR.sub(lambda m: m.group(2), text)
    paren_match = RE_PAREN_LABEL.match(text)
    if paren_match:
        text = paren_match.group(1)
    text = text.replace("ㆍ", "")
    text = re.sub(r"\s+", "", text)
    return text


def latest_risk_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(docs_dir().glob("*.parquet")):
        stock_code = path.stem
        df = pl.read_parquet(path).with_columns(pl.col("year").cast(pl.Utf8))
        annual = df.filter(pl.col("report_type").str.contains("사업보고서"))
        if annual.height == 0:
            continue
        latest_year = annual.get_column("year").max()
        if latest_year is None:
            continue
        latest = annual.filter(pl.col("year") == latest_year)
        for row in latest.select(["section_title", "section_content", "year"]).to_dicts():
            raw_title = (row["section_title"] or "").strip()
            if mapSectionTitle(raw_title) != "riskDerivative":
                continue
            rows.append(
                {
                    "stockCode": stock_code,
                    "year": row["year"],
                    "rawTitle": raw_title,
                    "text": row["section_content"] or "",
                }
            )
    return rows


def extract_semantic_rows(stock_code: str, year: str, raw_title: str, text: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    current_major = "(root)"
    current_minor = "(root)"
    buffer: list[str] = []
    table_rows = 0

    def flush() -> None:
        nonlocal buffer, table_rows
        body = "\n".join(buffer).strip()
        if not body and table_rows == 0:
            return
        label = current_minor if current_minor != "(root)" else current_major
        normalized = normalize_label(label)
        rows.append(
            {
                "stockCode": stock_code,
                "year": year,
                "rawTitle": raw_title,
                "majorLabel": current_major,
                "unitLabel": label,
                "normalizedLabel": normalized,
                "semanticId": SEMANTIC_OVERRIDES.get(normalized, ""),
                "textChars": len(body),
                "tableRows": table_rows,
                "text": body,
            }
        )
        buffer = []
        table_rows = 0

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("|"):
            table_rows += 1
            continue
        major_match = RE_MAJOR.match(stripped)
        minor_match = RE_MINOR.match(stripped)
        paren_match = RE_PAREN_LABEL.match(stripped)
        if major_match:
            flush()
            current_major = stripped
            current_minor = "(root)"
            continue
        if minor_match:
            flush()
            current_minor = stripped
            continue
        if paren_match:
            flush()
            current_minor = stripped
            continue
        buffer.append(stripped)

    flush()
    return rows


def canonicalize_all() -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for row in latest_risk_rows():
        rows.extend(extract_semantic_rows(row["stockCode"], row["year"], row["rawTitle"], row["text"]))
    if not rows:
        return pl.DataFrame()
    return pl.DataFrame(rows)


def print_stock_detail(df: pl.DataFrame, stock_code: str) -> None:
    stock_df = df.filter(pl.col("stockCode") == stock_code).sort(["year", "semanticId", "normalizedLabel"])
    print()
    print("=" * 72)
    print(f"{stock_code} riskDerivative semantic units")
    print("=" * 72)
    print(
        stock_df.select(
            ["year", "semanticId", "normalizedLabel", "textChars", "tableRows", "unitLabel"]
        )
    )


def main() -> None:
    df = canonicalize_all()
    if df.height == 0:
        print("NO_ROWS")
        return

    hit_ratio = df.filter(pl.col("semanticId") != "").height / df.height
    summary = df.select(
        pl.col("stockCode").n_unique().alias("companies"),
        pl.len().alias("semanticRows"),
        pl.col("rawTitle").n_unique().alias("rawTitleVariants"),
        pl.lit(hit_ratio).alias("canonicalHitRatio"),
        pl.col("semanticId").filter(pl.col("semanticId") != "").n_unique().alias("canonicalSemanticIds"),
    )
    semantic_counts = (
        df.filter(pl.col("semanticId") != "")
        .group_by("semanticId")
        .agg(pl.len().alias("rows"), pl.col("stockCode").n_unique().alias("companies"))
        .sort(["companies", "rows", "semanticId"], descending=[True, True, False])
    )
    unknowns = (
        df.filter(pl.col("semanticId") == "")
        .group_by("normalizedLabel")
        .agg(pl.len().alias("rows"), pl.col("stockCode").n_unique().alias("companies"))
        .sort(["companies", "rows", "normalizedLabel"], descending=[True, True, False])
        .head(20)
    )

    print("=" * 72)
    print("056-037 riskDerivative semantic unit canonicalization")
    print("=" * 72)
    print(f"matchedSectionRows={df.select(pl.col('stockCode').n_unique()).item()}")
    print(summary)
    print()
    print("[top semantic ids]")
    print(semantic_counts.head(20))
    print()
    print("[top unknown labels]")
    print(unknowns)

    stock_code = sys.argv[1] if len(sys.argv) > 1 else "005930"
    print_stock_detail(df, stock_code)


if __name__ == "__main__":
    main()
