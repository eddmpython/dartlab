"""
실험 ID: 003
실험명: 주식의 총수 파서 개발 + 10종목 검증

목적:
- "주식의 총수" 테이블에서 발행주식/자기주식/유통주식 추출
- Ⅰ~Ⅶ 번호 체계 파싱

가설:
1. 5셀 구조 (구분, 보통주, 우선주, 합계, 비고) 표준

방법:
1. 파서 구현: Ⅰ~Ⅶ 키워드 매칭 → 보통주/우선주/합계 추출
2. 10개 종목 적용

결과:

결론:

실험일: 2026-03-07
"""
import io
import re
import sys
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
    "006400",
    "003550",
    "034020",
]


def parseAmount(text: str) -> float | None:
    if not text or text.strip() in ("", "-", "\u3000", "\u2015", "\u2013"):
        return None
    cleaned = text.strip()
    cleaned = cleaned.replace(",", "").replace(" ", "")
    cleaned = re.sub(r"[^\d.]", "", cleaned)
    if not cleaned:
        return None
    if cleaned.count(".") > 1:
        return None
    cleaned = cleaned.strip(".")
    if not cleaned:
        return None
    return float(cleaned)


FIELD_MAP = {
    "발행할 주식의 총수": "authorizedShares",
    "현재까지 발행한 주식의 총수": "issuedShares",
    "현재까지 감소한 주식의 총수": "retiredShares",
    "발행주식의 총수": "outstandingShares",
    "자기주식수": "treasuryShares",
    "유통주식수": "floatingShares",
    "자기주식 보유비율": "treasuryRatio",
}


def parseShareCapitalTable(content: str) -> dict | None:
    lines = content.split("\n")
    result = {}

    for line in lines:
        s = line.strip()
        if not s.startswith("|"):
            continue

        cells = [c.strip() for c in s.split("|")]
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]

        if len(cells) < 3:
            continue

        txt = " ".join(cells[:2])
        for keyword, field in FIELD_MAP.items():
            if keyword in txt:
                for ci in range(1, len(cells)):
                    v = parseAmount(cells[ci])
                    if v is not None:
                        result[field] = v
                        break
                break

    if not result.get("outstandingShares"):
        return None
    return result


def main():
    print("=" * 100)
    print("주식의 총수 파서 10종목 검증")
    print("=" * 100)

    okCount = 0
    failCount = 0

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
                & pl.col("section_title").str.contains("주식의 총수")
                & pl.col("report_type").str.contains("사업보고서")
                & ~pl.col("report_type").str.contains("기재정정|첨부")
            )
            if rows.height == 0:
                continue

            content = rows["section_content"][0]
            parsed = parseShareCapitalTable(content)

            if parsed:
                found = True
                okCount += 1
                print(f"\n[{code}] {corpName} ({year}):")
                for k, v in parsed.items():
                    if k == "treasuryRatio":
                        print(f"  {k}: {v}%")
                    else:
                        print(f"  {k}: {v:,.0f}")
                break

        if not found:
            failCount += 1
            print(f"\n[{code}] {corpName}: 실패")

    print(f"\n{'=' * 100}")
    print(f"성공: {okCount}/{len(STOCKS)}, 실패: {failCount}/{len(STOCKS)}")


if __name__ == "__main__":
    main()
