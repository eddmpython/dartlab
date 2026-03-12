"""
실험 ID: 056-026
실험명: 최종 sectionMappings draft 생성

목적:
- stable topicId + 하드코딩 예외를 병합한 최종 sectionMappings draft 파일을 생성한다.
- 생성 직후 최종 raw coverage를 재검증한다.

가설:
1. 019~025 결과를 합치면 실용 가능한 최종 draft를 만들 수 있다.
2. 최종 draft는 최신 사업보고서 raw title 기준 약 98% 수준 커버리지를 확보한다.

방법:
1. latest annual report 기준 canonical candidate를 집계한다.
2. stable topicId를 적용한다.
3. 하드코딩 예외를 병합해 final draft JSON 파일을 작성한다.
4. 최종 raw coverage를 다시 계산한다.

결과 (실험 후 작성):

- 최종 draft 파일 생성 완료:
- `experiments/056_sectionMap/output/sectionMappings.final.draft.json`
- final mapping 수: 41
- final raw coverage: 0.980
결론:

- 056 실험은 이제 실제로 사용할 수 있는 `sectionMappings` 최종 초안 파일까지 도달했다.
- coverage 98.0% 수준이면 다음 단계는 추가 실험보다, 이 draft를 실제 엔진 spike에 연결해보는 작업이 더 가치 있다.
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

HARDCODED_EXCEPTIONS = {
    "1. 공시내용 진행 및 변경사항": "disclosureChanges",
    "2. 영업의 현황": "businessStatus",
    "4. 연구개발실적(상세)": "rndDetail",
    "4. 연구개발 실적(상세)": "rndDetail",
    "4. 영업설비": "operatingFacilities",
    "5. 재무건전성 등 기타 참고사항": "financialSoundnessOtherReference",
    "1. 전문가의 확인": "expertConfirmation",
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


def build_base_mapping(df: pl.DataFrame) -> dict[str, str]:
    company_count = df.get_column("stockCode").n_unique()
    candidates = (
        df.group_by("normalizedTitle")
        .agg(pl.col("stockCode").n_unique().alias("companyCoverage"))
        .with_columns((pl.col("companyCoverage") / company_count).round(3).alias("coverageRatio"))
        .filter(pl.col("coverageRatio") >= 0.7)
        .sort(["companyCoverage", "normalizedTitle"], descending=[True, False])
    )
    return {row["normalizedTitle"]: TOPIC_OVERRIDES[row["normalizedTitle"]] for row in candidates.to_dicts()}


def coverage(df: pl.DataFrame, mapping_keys: set[str]) -> float:
    total = df.height
    covered = df.filter(pl.col("normalizedTitle").is_in(list(mapping_keys))).height
    return covered / total if total else 0.0


def main() -> None:
    df = pl.DataFrame(latest_title_rows())
    base_mapping = build_base_mapping(df)
    final_mapping = {**base_mapping, **HARDCODED_EXCEPTIONS}

    out = out_dir()
    out.mkdir(parents=True, exist_ok=True)
    final_path = out / "sectionMappings.final.draft.json"
    final_path.write_text(json.dumps(final_mapping, ensure_ascii=False, indent=2), encoding="utf-8")

    final_coverage = coverage(df, set(final_mapping.keys()))

    print("=" * 72)
    print("056-026 최종 sectionMappings draft 생성")
    print("=" * 72)
    print(f"path={final_path}")
    print(f"mapping_count={len(final_mapping)}")
    print(f"final_coverage={final_coverage:.3f}")


if __name__ == "__main__":
    main()
