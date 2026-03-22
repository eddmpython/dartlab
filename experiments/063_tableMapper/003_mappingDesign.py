"""실험 ID: 063-003
실험명: 테이블 매퍼 규칙 설계 — companyOverview 테이블 분류

목적:
- companyOverview 내 테이블의 헤더 패턴으로 독립 topic명 매핑 규칙 설계
- 실제 삼성전자 원본 데이터로 테이블별 내용 확인
- 매핑 규칙의 프로토타입 구현

가설:
1. companyOverview 내 테이블은 5~10종류로 분류 가능하다
2. 헤더 키워드 매칭으로 90%+ 자동 분류 가능하다

방법:
1. 삼성전자 companyOverview의 table 블록을 파싱
2. 각 테이블의 의미를 식별하여 독립 topic명 부여
3. 전종목에 적용 가능한 매핑 규칙 도출

결과 (실험 후 작성):
-

결론:
-

실험일: 2026-03-14
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from dartlab.engines.company.dart.docs.sections.pipeline import sections


def splitTables(content: str) -> list[dict[str, str]]:
    """하나의 table 블록에서 개별 테이블을 분리.

    연속된 | 행 = 하나의 테이블. 빈 줄이나 비-테이블 줄이 나오면 분리.
    """
    tables: list[dict[str, str]] = []
    current_lines: list[str] = []

    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("|"):
            current_lines.append(stripped)
        else:
            if current_lines:
                header = _extractHeader(current_lines)
                tables.append({
                    "header": header or "",
                    "content": "\n".join(current_lines),
                    "rows": len(current_lines),
                })
                current_lines = []

    if current_lines:
        header = _extractHeader(current_lines)
        tables.append({
            "header": header or "",
            "content": "\n".join(current_lines),
            "rows": len(current_lines),
        })

    return tables


def _extractHeader(lines: list[str]) -> str | None:
    """테이블 행 목록에서 헤더 행 추출 (--- 직전 행)."""
    for i, line in enumerate(lines):
        if "---" not in line:
            cells = [c.strip() for c in line.split("|") if c.strip()]
            return " | ".join(cells)
    return None


def classifyTable(header: str) -> str:
    """헤더 패턴으로 테이블 topic 분류.

    규칙 기반 매핑 — 헤더 키워드로 판별.
    """
    h = header.lower().replace(" ", "")

    # 부문/사업/제품
    if any(k in h for k in ["부문", "주요제품", "사업부문"]):
        return "businessSegments"

    # 연결대상 종속회사
    if any(k in h for k in ["연결대상", "종속회사수", "자회사"]):
        return "subsidiaryCount"

    # 상장 여부
    if any(k in h for k in ["주권상장", "등록ㆍ지정", "특례상장"]):
        return "listingStatus"

    # 중소기업 해당 여부
    if "중소기업" in h:
        return "smeStatus"

    # 종속회사 상세
    if any(k in h for k in ["상호", "설립일", "주소", "주요사업"]) and "자산총액" in h:
        return "subsidiaryDetail"

    # 기준일 테이블 (주주/자본 관련에서 많이 나옴)
    if re.search(r"기준일", h):
        return "referenceDate"

    return "unknown"


if __name__ == "__main__":
    s = sections("005930")
    if s is None:
        print("삼성전자 sections 없음")
        sys.exit(1)

    tables = s.filter(
        (s["topic"] == "companyOverview") & (s["blockType"] == "table")
    )

    periodCols = [c for c in tables.columns if c not in {"chapter", "topic", "blockType"}]

    # 최신 기간 3개 확인
    for period in periodCols[:3]:
        content = tables[period][0]
        if content is None:
            continue

        print(f"\n{'='*80}")
        print(f"=== {period} ===")

        subTables = splitTables(str(content))
        print(f"테이블 수: {len(subTables)}")

        for i, t in enumerate(subTables):
            classified = classifyTable(t["header"])
            print(f"\n  [{i+1}] {classified}")
            print(f"      헤더: {t['header'][:100]}")
            print(f"      행 수: {t['rows']}")
            print(f"      내용: {t['content'][:200]}")
