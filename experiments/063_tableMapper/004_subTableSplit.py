"""실험 ID: 063-004
실험명: 하위 테이블 분리 + 키워드 기반 topic 매핑 프로토타입

목적:
- 하나의 table 블록에서 하위 테이블을 분리하는 로직 구현
- 각 하위 테이블의 헤더 키워드로 독립 topic명 매핑
- 전종목 적용 시 커버리지 측정

가설:
1. table 블록 내 하위 테이블은 --- 구분자 패턴으로 분리 가능하다
2. 상위 20개 패턴으로 전종목 테이블의 70%+ 커버 가능

방법:
1. companyOverview 2024 테이블에서 하위 테이블 분리 검증
2. 키워드 매핑 규칙 작성
3. 전종목 companyOverview에 적용하여 커버리지 측정

결과 (실험 후 작성):
-

결론:
-

실험일: 2026-03-14
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from dartlab.engines.company.dart.docs.sections.pipeline import sections
from dartlab.core.dataLoader import _dataDir


def splitSubTables(tableContent: str) -> list[dict[str, str]]:
    """table 블록에서 하위 테이블을 분리.

    규칙: 연속된 | 행은 하나의 테이블.
    비-| 행 또는 빈 줄이 나오면 새 테이블 시작.
    --- 단독 행은 구분자로 취급 (테이블 간 경계).
    """
    result: list[dict[str, str]] = []
    lines: list[str] = []

    def flush():
        if not lines:
            return
        # --- 단독 행 제거
        cleaned = [l for l in lines if not re.match(r"^\|\s*---+\s*\|?\s*$", l)]
        if not cleaned:
            return
        # 헤더 추출 (첫 번째 비-구분자 행)
        header = ""
        for l in cleaned:
            if "---" not in l:
                cells = [c.strip() for c in l.split("|") if c.strip()]
                header = " | ".join(cells)
                break
        result.append({
            "header": header,
            "rows": len(cleaned),
            "content": "\n".join(cleaned),
        })

    for line in tableContent.split("\n"):
        stripped = line.strip()
        if stripped.startswith("|"):
            lines.append(stripped)
        else:
            flush()
            lines = []

    flush()
    return result


# 키워드 → topic 매핑 규칙
TABLE_RULES: list[tuple[list[str], str]] = [
    # companyOverview 내 테이블
    (["부문", "주요제품"], "businessSegments"),
    (["부문", "제품"], "businessSegments"),
    (["사업부문", "매출"], "businessSegments"),
    (["연결대상", "회사수"], "subsidiaryCount"),
    (["종속회사수"], "subsidiaryCount"),
    (["자회사", "사유"], "subsidiaryChange"),
    (["주권상장", "등록"], "listingStatus"),
    (["특례상장"], "listingStatus"),
    (["중소기업", "해당"], "smeStatus"),
    (["벤처기업", "해당"], "ventureStatus"),

    # employee 내 테이블
    (["성명", "직위", "등기임원"], "executiveList"),
    (["직원", "소속", "근로자"], "employeeCount"),
    (["인원수", "연간급여", "1인평균"], "employeeSalary"),
    (["사업부문", "성별", "직원수"], "employeeBySegment"),

    # audit 내 테이블
    (["감사인", "감사의견"], "auditOpinion"),
    (["감사인", "감사계약"], "auditContract"),
    (["계약체결일", "용역내용"], "auditService"),
    (["참석자", "논의내용"], "auditCommittee"),
    (["운영실태", "평가결론"], "internalControl"),

    # dividend 내 테이블
    (["주식의종류", "당기", "전기"], "dividendHistory"),
    (["배당횟수", "배당수익률"], "dividendContinuity"),
    (["배당여부", "배당기준일"], "dividendPolicy"),

    # shareCapital 내 테이블
    (["주식의종류", "비고"], "shareType"),
    (["취득방법", "기초수량"], "treasuryStock"),

    # majorHolder 내 테이블
    (["소유주식수", "지분율"], "majorShareholderList"),
    (["출자자수", "대표이사"], "specialPurposeEntity"),

    # executivePay 내 테이블
    (["보수총액", "포함되지않는"], "executivePayDetail"),
    (["주주총회", "승인금액"], "executivePayApproval"),
    (["인원수", "보수총액", "1인당"], "executivePaySummary"),
    (["보수의종류", "산정기준"], "executivePayBreakdown"),

    # boardOfDirectors 내 테이블
    (["이사의수", "사외이사수"], "boardComposition"),
    (["사외이사", "교육"], "boardEducation"),
    (["회차", "의안내용", "가결"], "boardMeeting"),
    (["위원회명", "구성"], "boardCommittee"),

    # companyHistory 내 테이블
    (["선임", "임기만료", "해임"], "directorChange"),
    (["정관변경일", "주총명"], "articlesChange"),

    # 공통
    (["기준일"], "referenceDate"),  # 매칭 최후순위
]


def classifyHeader(header: str) -> str:
    """헤더에서 키워드 매칭으로 topic 분류."""
    h = header.replace(" ", "").lower()
    for keywords, topic in TABLE_RULES:
        normalized = [k.replace(" ", "").lower() for k in keywords]
        if all(k in h for k in normalized):
            return topic
    return "unknown"


if __name__ == "__main__":
    # 1) 삼성전자 companyOverview 검증
    print("=== 삼성전자 companyOverview 2024 ===")
    s = sections("005930")
    t = s.filter((s["topic"] == "companyOverview") & (s["blockType"] == "table"))
    content = t["2024"][0]
    if content:
        subs = splitSubTables(str(content))
        for i, sub in enumerate(subs):
            topic = classifyHeader(sub["header"])
            print(f"  [{i+1}] {topic:25s} | rows={sub['rows']:3d} | {sub['header'][:80]}")

    # 2) 전종목 companyOverview 커버리지
    print("\n=== 전종목 companyOverview 테이블 분류 커버리지 ===")
    codes = sorted(p.stem for p in _dataDir("docs").glob("*.parquet"))
    classified = Counter()
    total = 0
    for code in codes:
        try:
            sec = sections(code)
            if sec is None or "blockType" not in sec.columns:
                continue
            tb = sec.filter((sec["topic"] == "companyOverview") & (sec["blockType"] == "table"))
            if tb.is_empty():
                continue
            pCols = [c for c in tb.columns if c not in {"chapter", "topic", "blockType"}]
            # 최신 non-null 기간
            for p in pCols:
                val = tb[p][0]
                if val:
                    for sub in splitSubTables(str(val)):
                        topic = classifyHeader(sub["header"])
                        classified[topic] += 1
                        total += 1
                    break
        except (KeyError, ValueError, TypeError):
            pass

    print(f"총 하위 테이블: {total}")
    known = sum(v for k, v in classified.items() if k != "unknown")
    print(f"분류 성공: {known}/{total} ({known/total*100:.1f}%)")
    print(f"미분류: {classified['unknown']}/{total}")
    print("\n분류별:")
    for topic, count in classified.most_common():
        print(f"  {topic:25s}: {count:4d}")
