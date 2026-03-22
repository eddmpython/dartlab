"""
실험 ID: 056-019
실험명: sectionMappings 초안 자동 생성

목적:
- 전체 최신 사업보고서 기준 canonical boundary 후보를 실제 sectionMappings 초안 형태로 변환할 수 있는지 검증한다.

가설:
1. high-confidence canonical candidate를 기반으로 sectionMappings 초안을 자동 생성할 수 있다.
2. topicId는 규칙 기반 slugify만으로도 실용적인 1차 초안이 가능하다.

방법:
1. 전체 docs parquet의 최신 사업보고서 section_title을 chapter별로 집계한다.
2. coverage 0.7 이상 normalized title을 canonical 후보로 선택한다.
3. normalized title -> topicId 매핑 초안을 출력한다.

결과 (실험 후 작성):

- 후보 수: 34
- chapter별 high-confidence canonical candidate를 `normalizedTitle -> topicId` 초안으로 변환 가능
- 예:
- `5. 정관에 관한 사항 -> articlesOfIncorporation`
결론:

- 일부 항목은 아직 한글 topicId로 남는다 (`회사의개요`, `회사의연혁`, `자본금변동사항`).
- 즉 다음 단계에서 title -> stable english topicId 사전을 더 보강하면 sectionMappings 초안을 실제 프로덕션 데이터로 발전시킬 수 있다.
실험일: 2026-03-11
"""

from __future__ import annotations

import re
from pathlib import Path

import polars as pl

CHAPTER_RE = re.compile(r"^\s*([IVX]{1,5})\.\s*(.*)$")
INDUSTRY_PREFIX_RE = re.compile(r"^\([^)]*업\)")


def docs_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "dart" / "docs"


def normalize_title(title: str) -> str:
    text = title.strip()
    text = INDUSTRY_PREFIX_RE.sub("", text)
    text = text.replace("ㆍ", ",")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def make_topic_id(title: str) -> str:
    text = re.sub(r"^\d+\.\s*", "", title.strip())
    replacements = {
        "회사": "company",
        "개요": "overview",
        "연혁": "history",
        "자본금": "capital",
        "주식의 총수 등": "shareCapital",
        "정관에 관한 사항": "articlesOfIncorporation",
        "사업의 개요": "businessOverview",
        "주요 제품 및 서비스": "productService",
        "원재료 및 생산설비": "rawMaterialAndFacilities",
        "매출 및 수주상황": "salesOrder",
        "위험관리 및 파생거래": "riskDerivative",
        "주요계약 및 연구개발활동": "majorContractsAndRnd",
        "기타 참고사항": "otherReference",
        "요약재무정보": "fsSummary",
        "연결재무제표": "consolidatedStatements",
        "연결재무제표 주석": "consolidatedNotes",
        "재무제표": "financialStatements",
        "재무제표 주석": "financialNotes",
        "배당에 관한 사항": "dividend",
        "증권의 발행을 통한 자금조달에 관한 사항": "fundraising",
        "기타 재무에 관한 사항": "otherFinance",
        "외부감사에 관한 사항": "audit",
        "내부통제에 관한 사항": "internalControl",
        "이사회에 관한 사항": "boardOfDirectors",
        "감사제도에 관한 사항": "auditSystem",
        "주주총회 등에 관한 사항": "shareholderMeeting",
        "임원 및 직원 등의 현황": "employeeExecutive",
        "임원의 보수 등": "executivePay",
        "우발부채 등에 관한 사항": "contingentLiability",
        "제재 등과 관련된 사항": "sanction",
        "작성기준일 이후 발생한 주요사항 등 기타사항": "subsequentEvents",
        "연결대상 종속회사 현황(상세)": "subsidiariesDetail",
        "계열회사 현황(상세)": "affiliateGroupDetail",
        "타법인출자 현황(상세)": "investmentInOtherDetail",
        "연구개발실적(상세)": "rndDetail",
        "【 전문가의 확인 】": "expertConfirmation",
    }
    if text in replacements:
        return replacements[text]
    slug = re.sub(r"[^0-9A-Za-z가-힣]+", " ", text).strip().split()
    if not slug:
        return "unknownTopic"
    first = slug[0].lower()
    rest = [part[:1].upper() + part[1:] for part in slug[1:]]
    return first + "".join(rest)


def build_rows() -> list[dict[str, str]]:
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


def main() -> None:
    rows = build_rows()
    df = pl.DataFrame(rows)
    company_count = df.get_column("stockCode").n_unique()
    candidates = (
        df.group_by(["chapter", "normalizedTitle"])
        .agg(pl.col("stockCode").n_unique().alias("companyCoverage"))
        .with_columns((pl.col("companyCoverage") / company_count).round(3).alias("coverageRatio"))
        .filter(pl.col("coverageRatio") >= 0.7)
        .sort(["chapter", "companyCoverage", "normalizedTitle"], descending=[False, True, False])
    )

    mapping_rows = [
        {
            "chapter": row["chapter"],
            "normalizedTitle": row["normalizedTitle"],
            "topicId": make_topic_id(row["normalizedTitle"]),
            "coverageRatio": row["coverageRatio"],
        }
        for row in candidates.to_dicts()
    ]
    out = pl.DataFrame(mapping_rows)
    print("=" * 72)
    print("056-019 sectionMappings 초안 자동 생성")
    print("=" * 72)
    print("candidate_count=", out.height)
    print(out)


if __name__ == "__main__":
    main()
