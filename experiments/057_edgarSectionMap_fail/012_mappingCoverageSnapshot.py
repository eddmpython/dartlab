"""
실험 ID: 057-012
실험명: EDGAR section mapping coverage snapshot

목적:
- 수집 데이터가 늘어날 때마다 현재 sectionMappings가 얼마나 커버하는지 즉시 측정한다.
- form_type별 candidate coverage, 전체 raw title coverage, 미매핑 상위 title을 함께 기록한다.

가설:
1. 초기 표본이 커질수록 20-F/10-Q/10-K의 미세한 title 변형이 늘어난다.
2. 현재 mappings는 canonical candidate는 대부분 커버하지만 raw long-tail은 점진적으로 보강이 필요하다.

방법:
1. data/edgar/docs/*.parquet를 전수 스캔한다.
2. form_type/section_title별 filing coverage를 계산한다.
3. 현재 package sectionMappings와 대조해 candidate coverage와 raw coverage를 측정한다.
4. 미매핑 상위 title을 출력한다.

결과 (실험 후 작성):
- 실행 후 갱신

결론:
- 실행 후 갱신

실험일: 2026-03-12
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from dartlab import config
from dartlab.providers.edgar.docs.sections.mapper import loadSectionMappings, normalizeSectionTitle

MIN_FILING_COVERAGE = 0.5


def loadDocs() -> pl.DataFrame:
    docsDir = Path(config.dataDir) / "edgar" / "docs"
    frames: list[pl.DataFrame] = []
    for filePath in sorted(docsDir.glob("*.parquet")):
        frames.append(
            pl.read_parquet(
                filePath,
                columns=["accession_no", "form_type", "section_title"],
            ).with_columns(pl.lit(filePath.stem).alias("ticker"))
        )
    if not frames:
        return pl.DataFrame()
    return pl.concat(frames, how="vertical")


def outputDir() -> Path:
    return Path(__file__).resolve().parent / "output"


def buildSnapshot() -> dict[str, object]:
    df = loadDocs()
    if df.is_empty():
        raise RuntimeError("EDGAR docs parquet 없음")

    mappings = loadSectionMappings()
    rawDf = df.with_columns(
        pl.Series(
            "normalized_title",
            [normalizeSectionTitle(str(title)) for title in df["section_title"].to_list()],
        )
    )
    rawCoverage = (
        rawDf.group_by(["form_type", "section_title", "normalized_title"])
        .agg(
            pl.len().alias("rows"),
            pl.col("ticker").n_unique().alias("tickers"),
            pl.col("accession_no").n_unique().alias("filings"),
        )
        .with_columns(
            pl.col("normalized_title").is_in(list(mappings.keys())).alias("mapped")
        )
        .sort(["form_type", "rows"], descending=[False, True])
    )

    filingDf = df.unique(subset=["accession_no", "form_type", "section_title", "ticker"])
    formTotals = filingDf.group_by("form_type").agg(pl.col("accession_no").n_unique().alias("total_filings"))
    candidateDf = (
        filingDf.with_columns(
            pl.Series(
                "normalized_title",
                [normalizeSectionTitle(str(title)) for title in filingDf["section_title"].to_list()],
            )
        )
        .group_by(["form_type", "section_title", "normalized_title"])
        .agg(
            pl.col("accession_no").n_unique().alias("filings"),
            pl.col("ticker").n_unique().alias("tickers"),
        )
        .join(formTotals, on="form_type", how="left")
        .with_columns(
            (pl.col("filings") / pl.col("total_filings")).alias("filing_coverage"),
            pl.col("normalized_title").is_in(list(mappings.keys())).alias("mapped"),
        )
        .filter(pl.col("filing_coverage") >= MIN_FILING_COVERAGE)
        .sort(["form_type", "filings"], descending=[False, True])
    )

    candidateSummaryDf = (
        candidateDf.group_by("form_type")
        .agg(
            pl.len().alias("candidates"),
            pl.col("mapped").sum().alias("mapped_candidates"),
        )
        .with_columns((pl.col("mapped_candidates") / pl.col("candidates")).alias("coverage"))
        .sort("form_type")
    )
    rawSummaryDf = (
        rawCoverage.group_by("form_type")
        .agg(
            pl.len().alias("raw_titles"),
            pl.col("mapped").sum().alias("mapped_titles"),
        )
        .with_columns((pl.col("mapped_titles") / pl.col("raw_titles")).alias("coverage"))
        .sort("form_type")
    )
    unmappedTopDf = rawCoverage.filter(~pl.col("mapped")).select(["form_type", "section_title", "rows", "filings"]).head(20)

    return {
        "docs_files": df["ticker"].n_unique(),
        "candidate_summary": candidateSummaryDf.to_dicts(),
        "raw_summary": rawSummaryDf.to_dicts(),
        "unmapped_top": unmappedTopDf.to_dicts(),
    }


def writeSnapshotFiles(snapshot: dict[str, object]) -> None:
    outDir = outputDir()
    outDir.mkdir(parents=True, exist_ok=True)

    jsonPath = outDir / "mappingCoverage.latest.json"
    txtPath = outDir / "mappingCoverage.latest.txt"

    jsonPath.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")

    lines: list[str] = []
    lines.append("=" * 72)
    lines.append("057-012 mapping coverage snapshot")
    lines.append("=" * 72)
    lines.append(f"docs files={snapshot['docs_files']}")
    lines.append("")
    lines.append("[candidate coverage]")
    for row in snapshot["candidate_summary"]:
        lines.append(str(row))
    lines.append("")
    lines.append("[raw coverage]")
    for row in snapshot["raw_summary"]:
        lines.append(str(row))
    lines.append("")
    lines.append("[unmapped top]")
    for row in snapshot["unmapped_top"]:
        lines.append(str(row))
    txtPath.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    snapshot = buildSnapshot()
    writeSnapshotFiles(snapshot)

    print("=" * 72)
    print("057-012 mapping coverage snapshot")
    print("=" * 72)
    print(f"docs files={snapshot['docs_files']}")
    print()
    print("[candidate coverage]")
    print(pl.DataFrame(snapshot["candidate_summary"]))
    print()
    print("[raw coverage]")
    print(pl.DataFrame(snapshot["raw_summary"]))
    print()
    print("[unmapped top 20]")
    print(pl.DataFrame(snapshot["unmapped_top"]))


if __name__ == "__main__":
    main()
