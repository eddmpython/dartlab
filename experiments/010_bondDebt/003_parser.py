"""
실험 ID: 003
실험명: 채무증권 발행실적 파서 + 10종목 검증

목적:
- 10셀 구조 채무증권 발행실적 파싱
- 발행회사/종류/금액/이자율/만기/상환여부 추출

가설:
1. 10셀 표준 구조로 파싱 가능

방법:
1. 헤더 "발행회사" + "증권종류" 탐지 → 데이터 행 추출
2. 합계 행에서 총액 추출

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
    "005930", "000660", "035420", "005380", "055550",
    "003550", "034020", "006400", "001200", "000720",
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


def parseBondTable(content: str) -> list[dict]:
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

        if len(cells) < 8:
            continue

        txt = " ".join(cells)
        if all(c.replace("-", "") == "" for c in cells):
            continue

        if "발행회사" in txt and "증권종류" in txt:
            inTable = True
            continue

        if not inTable:
            continue

        name = cells[0]
        if name in ("합 계", "합계", "계"):
            break

        if len(cells) < 10:
            continue

        if not name:
            continue

        record = {
            "issuer": name,
            "bondType": cells[1],
            "method": cells[2],
            "issueDate": cells[3],
            "amount": parseAmount(cells[4]),
            "interestRate": cells[5],
            "rating": cells[6],
            "maturityDate": cells[7],
            "redeemed": cells[8],
            "underwriter": cells[9] if len(cells) > 9 else None,
        }
        results.append(record)

    return results


def main():
    print("=" * 100)
    print("채무증권 발행실적 파서 10종목 검증")
    print("=" * 100)

    okCount = 0
    noData = 0

    for code in STOCKS:
        path = DATA_DIR / f"{code}.parquet"
        if not path.exists():
            continue

        df = pl.read_parquet(str(path))
        corpName = (
            df["corp_name"].unique().to_list()[0] if "corp_name" in df.columns else code
        )
        years = sorted(df["year"].unique().to_list(), reverse=True)

        found = False
        for year in years[:2]:
            rows = df.filter(
                (pl.col("year") == year)
                & pl.col("section_title").str.contains("증권의 발행")
                & pl.col("report_type").str.contains("사업보고서")
                & ~pl.col("report_type").str.contains("기재정정|첨부")
            )
            if rows.height == 0:
                continue

            content = rows["section_content"][0]
            parsed = parseBondTable(content)

            if parsed:
                found = True
                okCount += 1
                totalAmount = sum(r["amount"] or 0 for r in parsed)
                unredeemed = [r for r in parsed if "미상환" in (r["redeemed"] or "")]
                print(f"\n[{code}] {corpName} ({year}): {len(parsed)}건, 총액 {totalAmount:,.0f}, 미상환 {len(unredeemed)}건")
                for r in parsed[:3]:
                    amt = r["amount"] or 0
                    print(f"  {r['issuer']}: {r['bondType']} {amt:,.0f} {r['interestRate']} ~{r['maturityDate']} ({r['redeemed']})")
                if len(parsed) > 3:
                    print(f"  ... 외 {len(parsed) - 3}건")
                break

        if not found:
            noData += 1
            print(f"\n[{code}] {corpName}: 채무증권 데이터 없음")

    print(f"\n{'=' * 100}")
    print(f"성공: {okCount}/{len(STOCKS)}, 데이터 없음: {noData}/{len(STOCKS)}")


if __name__ == "__main__":
    main()
