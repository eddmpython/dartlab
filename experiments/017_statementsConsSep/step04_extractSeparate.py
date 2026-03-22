"""'4. 재무제표' 섹션에서 별도재무제표 추출 테스트.

step03에서 확인:
- 연결 섹션 없는 103개 기업은 statements() 결과 없음
- 이들 모두 '4. 재무제표' 섹션은 가지고 있음

이 step에서:
1. extractSeparateContent() 함수 테스트
2. splitStatements() 호환 확인
3. extractAccounts() 파싱 성공률 측정
"""

import os
import sys

sys.path.insert(0, "src")

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport
from dartlab.core.tableParser import extractAccounts
from dartlab.finance.statements.extractor import splitStatements

DATA_DIR = r"C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\data\dartData\docsData"


def extractSeparateContent(report: pl.DataFrame) -> str | None:
    """보고서에서 별도/개별재무제표 섹션 내용을 추출.

    DART 패턴:
    - '4. 재무제표' (가장 흔함)
    - 'III. 재무에 관한 사항' > '4. 재무제표'
    - 연결이 없는 기업의 유일한 재무제표
    """
    # '재무제표' 포함, '연결' 미포함, '주석' 미포함
    section = report.filter(
        pl.col("section_title").str.contains("재무제표")
        & ~pl.col("section_title").str.contains("연결")
        & ~pl.col("section_title").str.contains("주석")
    )
    if section.height == 0:
        return None
    return section["section_content"][0]


def extractConsolidatedContent(report: pl.DataFrame) -> str | None:
    """연결재무제표 추출 (기존 로직 복사)."""
    section = report.filter(pl.col("section_title").str.contains("연결재무제표"))
    if section.height == 0:
        return None
    section = section.filter(~pl.col("section_title").str.contains("주석"))
    if section.height == 0:
        return None
    return section["section_content"][0]


if __name__ == "__main__":
    codes = sorted(
        f.replace(".parquet", "")
        for f in os.listdir(DATA_DIR)
        if f.endswith(".parquet")
    )

    # 카테고리별 카운트
    consOk = 0          # 연결 추출 성공
    sepOk = 0           # 별도 추출 성공 (연결 없을 때)
    sepExtraOk = 0      # 별도 추출 성공 (연결 있을 때, 추가)
    noExtract = 0       # 아무것도 추출 안됨

    # 파싱 성공률
    sepBsOk = 0
    sepIsOk = 0
    sepCfOk = 0
    sepTotal = 0

    failCodes = []

    for code in codes:
        df = loadData(code)
        corpName = extractCorpName(df)
        years = sorted(df["year"].unique().to_list(), reverse=True)

        report = selectReport(df, years[0], reportKind="annual")
        if report is None:
            continue

        cons = extractConsolidatedContent(report)
        sep = extractSeparateContent(report)

        if cons is not None:
            consOk += 1
            if sep is not None:
                sepExtraOk += 1
        elif sep is not None:
            sepOk += 1
        else:
            noExtract += 1
            failCodes.append((code, corpName))
            continue

        # 별도 파싱 테스트 (연결 없는 기업만)
        if cons is None and sep is not None:
            sepTotal += 1
            parts = splitStatements(sep)

            bsContent = parts.get("BS")
            isContent = parts.get("PNL")
            cfContent = parts.get("CF")

            hasBs = False
            hasIs = False
            hasCf = False

            if bsContent:
                accounts, order = extractAccounts(bsContent)
                if accounts:
                    hasBs = True
                    sepBsOk += 1

            if isContent:
                accounts, order = extractAccounts(isContent)
                if accounts:
                    hasIs = True
                    sepIsOk += 1

            if cfContent:
                accounts, order = extractAccounts(cfContent)
                if accounts:
                    hasCf = True
                    sepCfOk += 1

            if not hasBs and not hasIs and not hasCf:
                failCodes.append((code, corpName))

    print("=== 추출 결과 ===")
    print(f"총 기업: {len(codes)}")
    print(f"연결 추출 성공: {consOk}")
    print(f"  (이 중 별도도 있음: {sepExtraOk})")
    print(f"별도만으로 추출: {sepOk}")
    print(f"아무것도 없음: {noExtract}")

    print(f"\n=== 별도 파싱 성공률 (연결 없는 {sepTotal}개) ===")
    print(f"BS: {sepBsOk}/{sepTotal}")
    print(f"IS: {sepIsOk}/{sepTotal}")
    print(f"CF: {sepCfOk}/{sepTotal}")

    if failCodes:
        print(f"\n추출/파싱 실패 기업 ({len(failCodes)}개):")
        for code, name in failCodes[:20]:
            print(f"  [{code}] {name}")
