"""
실험 ID: 003
실험명: 타법인출자 현황 파서 개발 + 10종목 검증

목적:
- 16셀 구조 타법인출자 테이블 파싱 로직 구현
- 10개 대표 종목 검증

가설:
1. 16셀 표준 구조로 10/10 파싱 성공

방법:
1. 파서 구현: 헤더 탐지 → 데이터 행 추출 → 합계 행 처리
2. 10개 종목 적용

결과:

결론:

실험일: 2026-03-07
"""
import re
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import polars as pl

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "docsData"

STOCKS = [
    "005930",
    "000660",
    "035420",
    "005380",
    "055550",
    "051910",
    "006400",
    "003550",
    "034020",
    "000270",
]


def parseAmount(text: str) -> float | None:
    if not text or text.strip() in ("", "-", "\u3000", "\u2015", "\u2013"):
        return None
    cleaned = text.strip()
    isNegative = "\u25b3" in cleaned or "(" in cleaned
    cleaned = cleaned.replace("\u25b3", "").replace(",", "").replace(" ", "")
    cleaned = cleaned.replace("(", "").replace(")", "")
    cleaned = re.sub(r"[^\d.]", "", cleaned)
    if not cleaned:
        return None
    if cleaned.count(".") > 1:
        return None
    cleaned = cleaned.strip(".")
    if not cleaned:
        return None
    val = float(cleaned)
    return -val if isNegative else val


def parseSubsidiaryTable(content: str) -> list[dict]:
    lines = content.split("\n")
    results = []
    inTable = False

    for line in lines:
        s = line.strip()
        if not s.startswith("|"):
            continue

        cells = [c.strip() for c in s.split("|")]
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]

        if len(cells) < 10:
            continue

        txt = " ".join(cells)
        if all(c.replace("-", "") == "" for c in cells):
            continue

        if "법인명" in txt or "법 인 명" in txt:
            inTable = True
            continue

        if not inTable:
            continue

        if "수량" in cells[0] and ("지분율" in txt or "금액" in txt):
            continue

        name = cells[0]
        if name in ("합 계", "합계", "계"):
            break

        if len(cells) < 16:
            continue

        if not name or name in ("수량", "지분율", "장부가액"):
            continue

        record = {
            "name": name,
            "listed": cells[1] if len(cells) > 1 else None,
            "firstAcquired": cells[2] if len(cells) > 2 else None,
            "purpose": cells[3] if len(cells) > 3 else None,
            "firstAmount": parseAmount(cells[4]) if len(cells) > 4 else None,
            "beginShares": parseAmount(cells[5]) if len(cells) > 5 else None,
            "beginRatio": parseAmount(cells[6]) if len(cells) > 6 else None,
            "beginBook": parseAmount(cells[7]) if len(cells) > 7 else None,
            "acquiredShares": parseAmount(cells[8]) if len(cells) > 8 else None,
            "acquiredAmount": parseAmount(cells[9]) if len(cells) > 9 else None,
            "valuationGain": parseAmount(cells[10]) if len(cells) > 10 else None,
            "endShares": parseAmount(cells[11]) if len(cells) > 11 else None,
            "endRatio": parseAmount(cells[12]) if len(cells) > 12 else None,
            "endBook": parseAmount(cells[13]) if len(cells) > 13 else None,
            "totalAssets": parseAmount(cells[14]) if len(cells) > 14 else None,
            "netIncome": parseAmount(cells[15]) if len(cells) > 15 else None,
        }
        results.append(record)

    return results


def findSubsidiarySection(df, year):
    rows = df.filter(
        (pl.col("year") == year)
        & pl.col("section_title").str.contains("타법인")
        & pl.col("report_type").str.contains("사업보고서")
        & ~pl.col("report_type").str.contains("기재정정|첨부")
    )
    if rows.height == 0:
        rows = df.filter(
            (pl.col("year") == year)
            & pl.col("section_title").str.contains("출자")
            & pl.col("report_type").str.contains("사업보고서")
            & ~pl.col("report_type").str.contains("기재정정|첨부")
        )
    if rows.height == 0:
        rows = df.filter(
            (pl.col("year") == year)
            & pl.col("section_title").str.contains("타법인")
            & pl.col("report_type").str.contains("사업보고서")
        )
    return rows


def main():
    print("=" * 100)
    print("타법인출자 파서 10종목 검증")
    print("=" * 100)

    okCount = 0
    failCount = 0

    for code in STOCKS:
        path = DATA_DIR / f"{code}.parquet"
        if not path.exists():
            print(f"\n[{code}] 파일 없음")
            continue

        df = pl.read_parquet(str(path))
        corpName = (
            df["corp_name"].unique().to_list()[0] if "corp_name" in df.columns else code
        )
        years = sorted(df["year"].unique().to_list(), reverse=True)

        found = False
        for year in years[:2]:
            rows = findSubsidiarySection(df, year)
            if rows.height == 0:
                continue

            content = rows["section_content"][0]
            parsed = parseSubsidiaryTable(content)

            if parsed:
                found = True
                okCount += 1
                print(f"\n[{code}] {corpName} ({year}): {len(parsed)}개 법인")

                listed = [r for r in parsed if r["listed"] == "상장"]
                unlisted = [r for r in parsed if r["listed"] != "상장"]
                totalBook = sum(r["endBook"] or 0 for r in parsed)

                print(f"  상장 {len(listed)}개, 비상장 {len(unlisted)}개")
                print(f"  기말 장부가 합계: {totalBook:,.0f}")

                for r in parsed[:5]:
                    book = r["endBook"] or 0
                    ratio = r["endRatio"] or 0
                    print(
                        f"    {r['name']}: {r['listed']} {ratio}% "
                        f"장부가 {book:,.0f} ({r['purpose']})"
                    )
                if len(parsed) > 5:
                    print(f"    ... 외 {len(parsed) - 5}개")
                break

        if not found:
            failCount += 1
            print(f"\n[{code}] {corpName}: 실패")

    print(f"\n{'=' * 100}")
    print(f"성공: {okCount}/10, 실패: {failCount}/10")


if __name__ == "__main__":
    main()
