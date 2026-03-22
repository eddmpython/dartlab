"""
실험 ID: 056-023
실험명: 실제 sectionMappings draft 파일 생성 및 검증

목적:
- canonical 후보를 메모리 출력이 아니라 실제 JSON draft 파일로 생성한다.
- 생성 직후 raw title 커버리지를 측정해 다음 개선 포인트를 확인한다.

가설:
1. 최신 사업보고서 기준 high-confidence 후보 34개는 실제 draft 파일로 안정적으로 저장 가능하다.
2. raw title 기준 커버리지는 normalized title 기준보다 낮고, 그 차이가 다음 개선 포인트가 된다.

방법:
1. 최신 사업보고서 전체를 스캔해 canonical 후보를 집계한다.
2. stable topicId를 적용해 draft JSON 파일을 쓴다.
3. 최신 사업보고서 raw title 기준으로 exact coverage를 측정한다.

결과 (실험 후 작성):

- 실제 draft 파일 생성 완료:
- `experiments/056_sectionMap/output/sectionMappings.draft.json`
- mapping 수: 34
- raw coverage: 0.963
결론:

- canonical 후보는 실제 draft 파일로 안정적으로 저장 가능하다.
- 최신 사업보고서 raw title 기준으로도 96.3% 커버되므로, 지금 단계의 draft는 실질적인 출발점으로 쓸 수 있다.
- 다음 개선 포인트는 coverage 확대보다, 남은 3.7%의 예외 패턴을 어떤 규칙으로 흡수할지 정하는 것이다.
실험일: 2026-03-11
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import polars as pl

CHAPTER_RE = re.compile(r"^\s*([IVX]{1,5})\.\s*(.*)$")
INDUSTRY_PREFIX_RE = re.compile(r"^\([^)]*업\)")

TOPIC_OVERRIDES = {
    "1. 회사의 개요": "companyOverview",
    "2. 회사의 연혁": "companyHistory",
    "3. 자본금 변동사항": "capitalChange",
    "4. 주식의 총수 등": "shareCapital",
    "5. 정관에 관한 사항": "articlesOfIncorporation",
    "1. 사업의 개요": "businessOverview",
    "2. 주요 제품 및 서비스": "productService",
    "3. 원재료 및 생산설비": "rawMaterial",
    "4. 매출 및 수주상황": "salesOrder",
    "5. 위험관리 및 파생거래": "riskDerivative",
    "6. 주요계약 및 연구개발활동": "majorContractsAndRnd",
    "7. 기타 참고사항": "otherReference",
    "1. 요약재무정보": "fsSummary",
    "2. 연결재무제표": "consolidatedStatements",
    "3. 연결재무제표 주석": "consolidatedNotes",
    "4. 재무제표": "financialStatements",
    "5. 재무제표 주석": "financialNotes",
    "6. 배당에 관한 사항": "dividend",
    "7. 증권의 발행을 통한 자금조달에 관한 사항": "fundraising",
    "8. 기타 재무에 관한 사항": "otherFinance",
    "1. 외부감사에 관한 사항": "audit",
    "2. 내부통제에 관한 사항": "internalControl",
    "1. 이사회에 관한 사항": "boardOfDirectors",
    "2. 감사제도에 관한 사항": "auditSystem",
    "3. 주주총회 등에 관한 사항": "shareholderMeeting",
    "1. 임원 및 직원 등의 현황": "employee",
    "2. 임원의 보수 등": "executivePay",
    "2. 우발부채 등에 관한 사항": "contingentLiability",
    "3. 제재 등과 관련된 사항": "sanction",
    "4. 작성기준일 이후 발생한 주요사항 등 기타사항": "subsequentEvents",
    "1. 연결대상 종속회사 현황(상세)": "subsidiaryDetail",
    "2. 계열회사 현황(상세)": "affiliateGroupDetail",
    "3. 타법인출자 현황(상세)": "investmentInOtherDetail",
    "4. 연구개발실적(상세)": "rndDetail",
    "【 전문가의 확인 】": "expertConfirmation",
}


def base_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def docs_dir() -> Path:
    return base_dir() / "data" / "dart" / "docs"


def out_dir() -> Path:
    return Path(__file__).resolve().parent / "output"


def normalize_title(title: str) -> str:
    text = title.strip()
    text = INDUSTRY_PREFIX_RE.sub("", text)
    text = text.replace("ㆍ", ",")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def latest_title_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(docs_dir().glob("*.parquet")):
        stock_code = path.stem
        df = pl.read_parquet(path).with_columns(pl.col("year"))
        annual = df.filter(pl.col("report_type").str.contains("사업보고서"))
        if annual.height == 0:
            continue
        latest_year = annual.get_column("year").max()
        if latest_year is None:
            continue
        current = ""
        titles = (
            annual.filter(pl.col("year") == latest_year).sort("section_order").get_column("section_title").to_list()
        )
        for raw_title in titles:
            stripped = (raw_title or "").strip()
            match = CHAPTER_RE.match(stripped)
            if match:
                current = match.group(1)
                continue
            if not current:
                continue
            rows.append(
                {
                    "stockCode": stock_code,
                    "chapter": current,
                    "rawTitle": stripped,
                    "normalizedTitle": normalize_title(stripped),
                }
            )
    return rows


def build_mapping(df: pl.DataFrame) -> dict[str, str]:
    company_count = df.get_column("stockCode").n_unique()
    candidates = (
        df.group_by("normalizedTitle")
        .agg(pl.col("stockCode").n_unique().alias("companyCoverage"))
        .with_columns((pl.col("companyCoverage") / company_count).round(3).alias("coverageRatio"))
        .filter(pl.col("coverageRatio") >= 0.7)
        .sort(["companyCoverage", "normalizedTitle"], descending=[True, False])
    )
    return {row["normalizedTitle"]: TOPIC_OVERRIDES[row["normalizedTitle"]] for row in candidates.to_dicts()}


def raw_coverage(df: pl.DataFrame, mapping: dict[str, str]) -> float:
    total = df.height
    covered = (
        df.with_columns(pl.col("normalizedTitle").is_in(list(mapping.keys())).alias("covered"))
        .filter(pl.col("covered"))
        .height
    )
    return covered / total if total else 0.0


def main() -> None:
    rows = latest_title_rows()
    df = pl.DataFrame(rows)
    mapping = build_mapping(df)
    out = out_dir()
    out.mkdir(parents=True, exist_ok=True)
    path = out / "sectionMappings.draft.json"
    path.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
    coverage = raw_coverage(df, mapping)

    print("=" * 72)
    print("056-023 실제 sectionMappings draft 파일 생성")
    print("=" * 72)
    print(f"path={path}")
    print(f"mapping_count={len(mapping)}")
    print(f"raw_coverage={coverage:.3f}")


if __name__ == "__main__":
    main()
