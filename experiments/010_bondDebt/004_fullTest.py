"""
실험 ID: 004
실험명: 전체 종목 채무증권 파서 테스트

목적:
- 보유 데이터 전체 종목에 대해 채무증권 파서 적용
- 성공/실패/데이터없음 통계 수집

가설:
1. 증권발행 섹션 보유 종목의 대부분에서 파싱 가능

방법:
1. data/docsData/ 전체 parquet 파일 순회
2. 각 종목 최신 사업보고서 증권발행 섹션 파싱

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


def _hasEmptyBondSection(content: str) -> bool:
    if "해당사항 없음" in content or "해당사항없음" in content:
        return True
    lines = content.split("\n")
    for line in lines:
        s = line.strip()
        if "발행회사" in s and "증권종류" in s:
            return True
    return False


def main():
    files = sorted(DATA_DIR.glob("*.parquet"))
    print(f"전체 종목: {len(files)}개")
    print("=" * 100)

    ok = []
    noBond = []
    noSection = []
    noBiz = []
    fail = []

    for path in files:
        code = path.stem
        df = pl.read_parquet(str(path))
        corpName = (
            df["corp_name"].unique().to_list()[0] if "corp_name" in df.columns else code
        )
        years = sorted(df["year"].unique().to_list(), reverse=True)

        found = False
        for year in years[:3]:
            rows = df.filter(
                (pl.col("year") == year)
                & pl.col("section_title").str.contains("증권의 발행")
                & pl.col("report_type").str.contains("사업보고서")
                & ~pl.col("report_type").str.contains("기재정정|첨부")
            )
            if rows.height == 0:
                rows = df.filter(
                    (pl.col("year") == year)
                    & pl.col("section_title").str.contains("증권의 발행")
                    & pl.col("report_type").str.contains("사업보고서")
                )
            if rows.height == 0:
                continue

            content = rows["section_content"][0]
            parsed = parseBondTable(content)

            if parsed:
                totalAmount = sum(r["amount"] or 0 for r in parsed)
                ok.append((code, corpName, year, len(parsed), totalAmount))
                found = True
                break

            if _hasEmptyBondSection(content):
                noBond.append((code, corpName))
                found = True
                break

        if not found:
            hasBiz = (
                df.filter(pl.col("report_type").str.contains("사업보고서")).height > 0
            )
            hasSection = df.filter(
                pl.col("section_title").str.contains("증권의 발행")
                & pl.col("report_type").str.contains("사업보고서")
            ).height > 0
            if hasSection:
                fail.append((code, corpName, "섹션 있으나 파싱 실패"))
            elif hasBiz:
                noSection.append((code, corpName))
            else:
                noBiz.append((code, corpName))

    print(f"\n성공: {len(ok)}개")
    print(f"채무증권 없음 (빈 테이블): {len(noBond)}개")
    print(f"증권발행 섹션 없음: {len(noSection)}개")
    print(f"사업보고서 없음: {len(noBiz)}개")
    print(f"실패: {len(fail)}개")

    total = len(ok) + len(noBond) + len(fail)
    if total > 0:
        rate = (len(ok) + len(noBond)) / total * 100
        print(f"\n성공률 (섹션 보유 기준): {rate:.1f}%")

    if fail:
        print(f"\n{'=' * 100}")
        print("실패 목록")
        print(f"{'=' * 100}")
        for code, name, reason in fail:
            print(f"  [{code}] {name}: {reason}")

    print(f"\n{'=' * 100}")
    print("성공 종목 샘플 (상위 15개)")
    print(f"{'=' * 100}")
    for code, name, year, nBonds, totalAmount in ok[:15]:
        print(f"  [{code}] {name} ({year}): {nBonds}건, 총액 {totalAmount:,.0f}")


if __name__ == "__main__":
    main()
