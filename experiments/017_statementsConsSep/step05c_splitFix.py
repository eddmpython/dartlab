"""splitStatements 개선 테스트.

문제 1: "연 결 재 무 상 태 표" → 공백 포함 패턴 매칭 실패
문제 2: "연결대상이 없어" 메시지만 있고 별도 재무제표 fallback 안 됨

개선:
- 패턴 매칭 시 공백 제거 후 비교
- "연결대상이 없어" → 별도 fallback
"""

import re
import sys

sys.path.insert(0, "src")

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport
from dartlab.core.tableParser import extractAccounts

# 개선된 splitStatements
_STATEMENT_PATTERNS = {
    "BS": r"재무상태표",
    "PNL": r"손익계산서",
    "CI": r"포괄손익",
    "SCE": r"자본변동표",
    "CF": r"현금흐름표",
}


def splitStatementsV2(content: str) -> dict[str, str]:
    """개선된 splitStatements — 공백 포함 패턴 지원."""
    lines = content.split("\n")

    headers: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        s = line.strip()
        if not s or len(s) >= 80:
            continue

        # 테이블 행인 경우
        if s.startswith("|"):
            cells = [c.strip() for c in s.split("|") if c.strip()]
            if len(cells) != 1:
                continue
            s = cells[0]

        # 공백 제거 후 패턴 매칭
        sNoSpace = re.sub(r"\s+", "", s)
        for key, pattern in _STATEMENT_PATTERNS.items():
            if re.search(pattern, sNoSpace):
                headers.append((i, key))
                break

    # 중복 키 처리
    seen: dict[str, int] = {}
    uniqueHeaders: list[tuple[int, str]] = []
    for idx, key in headers:
        if key in seen:
            uniqueHeaders[seen[key]] = (idx, key)
        else:
            seen[key] = len(uniqueHeaders)
            uniqueHeaders.append((idx, key))

    result: dict[str, str] = {}
    for j, (startIdx, key) in enumerate(uniqueHeaders):
        if j + 1 < len(uniqueHeaders):
            endIdx = uniqueHeaders[j + 1][0]
        else:
            endIdx = len(lines)
        result[key] = "\n".join(lines[startIdx:endIdx])

    return result


def extractContentV2(report: pl.DataFrame) -> tuple[str | None, str]:
    """연결 우선, 별도 fallback (연결대상없음 처리 포함)."""
    # 1) 연결재무제표
    cons = report.filter(
        pl.col("section_title").str.contains("연결재무제표")
        & ~pl.col("section_title").str.contains("주석")
    )
    if cons.height > 0:
        content = cons["section_content"][0]
        # "연결대상이 없어" 체크
        if "연결대상" in content and ("없어" in content or "없으므로" in content):
            pass  # 별도로 fallback
        else:
            return content, "consolidated"

    # 2) 별도/개별 재무제표
    sep = report.filter(
        pl.col("section_title").str.contains("재무제표")
        & ~pl.col("section_title").str.contains("연결")
        & ~pl.col("section_title").str.contains("주석")
    )
    if sep.height > 0:
        return sep["section_content"][0], "separate"

    return None, "none"


# 테스트 대상: no_split 케이스
NO_SPLIT_CODES = ["031210", "178920", "332190", "403810", "444530", "460850", "495900", "496320"]


if __name__ == "__main__":
    print("=== splitStatements 개선 테스트 ===\n")

    for code in NO_SPLIT_CODES:
        df = loadData(code)
        corpName = extractCorpName(df)
        years = sorted(df["year"].unique().to_list(), reverse=True)

        report = selectReport(df, years[0], reportKind="annual")
        if report is None:
            print(f"[{code}] {corpName}: 보고서 없음")
            continue

        content, scope = extractContentV2(report)
        if content is None:
            print(f"[{code}] {corpName}: 추출 불가 (scope={scope})")
            continue

        parts = splitStatementsV2(content)
        print(f"[{code}] {corpName} (scope={scope})")
        print(f"  keys: {list(parts.keys())}")

        # BS 파싱 테스트
        bsContent = parts.get("BS")
        if bsContent:
            accounts, order = extractAccounts(bsContent)
            print(f"  BS: {len(accounts)} accounts")
            if accounts:
                for name in order[:3]:
                    print(f"    {name}: {accounts[name]}")
        else:
            print(f"  BS: None")

        print()
