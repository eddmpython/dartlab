"""실험 ID: 063-008
실험명: tableMappings.json 초안 생성

목적:
- 007에서 확인된 상위 헤더 패턴으로 테이블 타입 정의
- 정규화 헤더 → 테이블 타입 매핑 생성
- 실제 수평화 테스트

가설:
1. 상위 50개 헤더 패턴으로 주요 테이블 타입 20개+ 정의 가능
2. 수평화된 테이블이 finance DataFrame처럼 사용 가능

방법:
1. 007 결과의 상위 헤더에서 테이블 타입명 부여
2. tableMappings.json 생성
3. 삼성전자 companyOverview로 수평화 테스트

결과 (실험 후 작성):
-

결론:
-

실험일: 2026-03-16
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import polars as pl
from dartlab.engines.dart.docs.sections.pipeline import sections


# ── 테이블 타입 정의 ──
# 정규화 헤더 패턴 → 테이블 타입명
# 007 결과에서 90%+ 종목 보유율인 헤더 기반

TABLE_TYPE_RULES: list[tuple[list[str], str]] = [
    # (헤더에 포함되어야 할 키워드 목록, 타입명)
    (["부문", "제품"], "productDivision"),
    (["부문", "매출액"], "segmentRevenue"),
    (["연결대상회사수"], "subsidiaryCount"),
    (["자회사", "사 유"], "subsidiaryChange"),
    (["중소기업", "해당"], "smeStatus"),
    (["평가대상유가증권", "신용등급"], "creditRating"),
    (["주권상장", "등록"], "listingStatus"),
    (["구 분", "주식의 종류", "당기"], "dividendDetail"),
    (["배당여부", "배당액확정일"], "dividendPolicy"),
    (["연속 배당횟수"], "dividendHistory"),
    (["현황 및 계획"], "dividendPlan"),
    (["성명", "성별", "출생년월", "직위"], "executiveList"),
    (["인원수", "연간급여"], "employeeSalary"),
    (["직원", "소속 외근로자"], "employeeCount"),
    (["성 명", "관 계", "주식의종류", "소유주식수"], "majorShareholderDetail"),
    (["주주명", "소유주식수", "지분율"], "majorShareholderSimple"),
    (["주주", "소유주식", "비 고"], "shareholderComposition"),
    (["정관변경일", "주요변경사항"], "articlesChange"),
    (["사업목적", "사업영위 여부"], "businessPurpose"),
    (["변동일자", "주총종류", "선임"], "boardChange"),
    (["이사의 수", "사외이사 수"], "boardComposition"),
    (["감사인", "감사의견"], "auditOpinion"),
    (["감사인", "감사계약내역"], "auditContract"),
    (["용역내용", "용역보수"], "nonAuditService"),
    (["기업집단의 명칭", "계열회사의 수"], "affiliateGroupInfo"),
    (["출자목적", "출자회사수"], "affiliateInvestment"),
    (["법인명", "최초취득일자", "출자목적"], "investedCompanyDetail"),
    (["주식발행", "발행", "주식의 내용"], "stockIssuance"),
    (["구 분", "주식의 종류", "비고"], "stockTypeDetail"),
    (["취득방법", "기초수량", "기말수량"], "treasuryStock"),
    (["투표제도 종류", "집중투표제"], "votingSystem"),
    (["구 분", "주식의 종류", "주식수", "비고"], "shareholderVoting"),
    (["재무상태표"], "balanceSheet"),
    (["포괄손익계산서"], "comprehensiveIncome"),
    (["현금흐름표"], "cashFlow"),
    (["자본변동표"], "equityChange"),
    (["인원수", "보수총액", "1인당 평균보수액"], "executivePaySummary"),
    (["주주총회 승인금액"], "executivePayApproval"),
    (["계약 상대방", "항 목", "내 용"], "majorContracts"),
    (["연구개발비용"], "rndExpense"),
    (["연구과제", "연구결과"], "rndProjects"),
]


def classifyHeader(header: str) -> str | None:
    """정규화 헤더 → 테이블 타입."""
    h = header.lower().replace(" ", "")
    for keywords, typeName in TABLE_TYPE_RULES:
        if all(kw.replace(" ", "").lower() in h for kw in keywords):
            return typeName
    return None


def splitSubtables(md: str) -> list[list[str]]:
    tables: list[list[str]] = []
    current: list[str] = []
    for line in md.strip().split("\n"):
        stripped = line.strip()
        if not stripped.startswith("|"):
            if current:
                tables.append(current)
                current = []
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        isSep = all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip())
        if isSep and current:
            if len(current) >= 2:
                prev = current[:-1]
                if prev:
                    tables.append(prev)
                current = [current[-1], stripped]
            else:
                current.append(stripped)
        else:
            current.append(stripped)
    if current:
        tables.append(current)
    return tables


def subtableHeader(lines: list[str]) -> str:
    for line in lines:
        cells = [c.strip() for c in line.strip("|").split("|")]
        isSep = all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip())
        if not isSep:
            return " | ".join(c.strip() for c in cells if c.strip())
    return ""


def normalizeHeader(header: str) -> str:
    h = re.sub(r"\d{4}(Q\d)?", "", header)
    h = re.sub(r"제\s*\d+\s*기", "", h)
    h = re.sub(r"\(\s*단위\s*:\s*[^)]+\)", "", h)
    h = re.sub(r"\(\s*기준일\s*:?[^)]*\)", "", h)
    h = re.sub(r"\d+\.\d+\.\d+", "", h)
    h = re.sub(r"\s+", " ", h).strip()
    return h


def parseRows(lines: list[str]) -> list[tuple[str, str]]:
    """서브테이블 → (항목, 값) 리스트."""
    rows = []
    headerDone = False
    for line in lines:
        cells = [c.strip() for c in line.strip("|").split("|")]
        isSep = all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip())
        if isSep:
            headerDone = True
            continue
        if not headerDone:
            continue
        label = cells[0].strip() if cells else ""
        value = " | ".join(cells[1:]).strip() if len(cells) > 1 else ""
        if label:
            rows.append((label, value))
    return rows


if __name__ == "__main__":
    sec = sections("005930")
    tables = sec.filter(pl.col("blockType") == "table")
    periods = [c for c in tables.columns if c not in {"chapter", "topic", "blockType"}]

    print("=== 삼성전자 서브테이블 타입 분류 ===\n")

    classified = 0
    unclassified = 0

    for row in tables.iter_rows(named=True):
        topic = row["topic"]
        if topic in {"consolidatedNotes", "financialNotes", "fsSummary"}:
            continue

        content = row.get(periods[-1])  # 최신 기간
        if content is None:
            continue

        subs = splitSubtables(str(content))
        print(f"▶ {topic} ({len(subs)}개 서브테이블)")

        for i, sub in enumerate(subs):
            header = subtableHeader(sub)
            normH = normalizeHeader(header)
            tableType = classifyHeader(normH)

            if tableType:
                classified += 1
                dataRows = parseRows(sub)
                print(f"  [{i}] ✓ {tableType} ({len(dataRows)}행)")
                if dataRows:
                    print(f"      항목: {[r[0] for r in dataRows[:3]]}")
            else:
                unclassified += 1
                print(f"  [{i}] ? {normH[:60]}")

    total = classified + unclassified
    print(f"\n분류: {classified}/{total} ({classified/total*100:.1f}%)")
    print(f"미분류: {unclassified}/{total}")
