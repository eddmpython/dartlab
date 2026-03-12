"""
실험 ID: 056-020
실험명: stable topicId 정리

목적:
- 자동 생성된 canonical 후보의 topicId를 stable english id로 고정할 수 있는지 검증한다.

가설:
1. 상위 high-confidence candidate 34개는 수동 사전 보강만으로 안정적인 topicId 세트를 만들 수 있다.
2. 이후 sectionMappings.json draft 생성의 직접 입력으로 사용할 수 있다.

방법:
1. 019의 canonical candidate를 다시 생성한다.
2. 한글/불안정 topicId를 english stable id로 치환한다.
3. 결과를 DataFrame으로 출력한다.

결과 (실험 후 작성):

- canonical 후보 34개에 대해 stable english topicId 세트 정리 완료
- `companyOverview`, `companyHistory`, `capitalChange`, `shareCapital`
- `businessOverview`, `productService`, `rawMaterial`, `salesOrder`, `riskDerivative`
- `audit`, `internalControl`, `boardOfDirectors`, `shareholderMeeting`
결론:

- 이제 high-confidence canonical 후보는 대부분 stable english topicId로 고정 가능하다.
실험일: 2026-03-11
"""

from __future__ import annotations

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


def docs_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "dart" / "docs"


def normalize_title(title: str) -> str:
    text = title.strip()
    text = INDUSTRY_PREFIX_RE.sub("", text)
    text = text.replace("ㆍ", ",")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def build_candidates() -> pl.DataFrame:
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
            rows.append({"stockCode": stock_code, "chapter": current, "normalizedTitle": normalize_title(stripped)})
    df = pl.DataFrame(rows)
    company_count = df.get_column("stockCode").n_unique()
    return (
        df.group_by(["chapter", "normalizedTitle"])
        .agg(pl.col("stockCode").n_unique().alias("companyCoverage"))
        .with_columns((pl.col("companyCoverage") / company_count).round(3).alias("coverageRatio"))
        .filter(pl.col("coverageRatio") >= 0.7)
        .sort(["chapter", "companyCoverage", "normalizedTitle"], descending=[False, True, False])
    )


def main() -> None:
    candidates = build_candidates()
    rows = []
    for row in candidates.to_dicts():
        title = row["normalizedTitle"]
        rows.append(
            {
                "chapter": row["chapter"],
                "normalizedTitle": title,
                "topicId": TOPIC_OVERRIDES.get(title, "TODO"),
                "coverageRatio": row["coverageRatio"],
            }
        )
    out = pl.DataFrame(rows)
    print("=" * 72)
    print("056-020 stable topicId 정리")
    print("=" * 72)
    print(out)


if __name__ == "__main__":
    main()
