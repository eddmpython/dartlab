"""
실험 ID: 004
실험명: 전체 종목 타법인출자 파서 테스트

목적:
- 보유 데이터 전체 종목에 대해 타법인출자 파서 적용
- 성공/실패/데이터없음 통계 수집

가설:
1. 사업보고서 보유 종목 90% 이상 파싱 성공

방법:
1. data/docsData/ 전체 parquet 파일 순회
2. 각 종목 최신 사업보고서 타법인출자 섹션 파싱
3. 성공/실패 분류

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


def _hasEmptyTable(content: str) -> bool:
    lines = content.split("\n")
    hasHeader = False
    for line in lines:
        s = line.strip()
        if not s.startswith("|"):
            if "해당사항 없음" in s or "해당사항없음" in s:
                return True
            continue
        txt = s
        if "법인명" in txt or "법 인 명" in txt:
            hasHeader = True
    return hasHeader


def main():
    files = sorted(DATA_DIR.glob("*.parquet"))
    print(f"전체 종목: {len(files)}개")
    print("=" * 100)

    ok = []
    noInvestment = []
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
            if rows.height == 0:
                continue

            for ri in range(rows.height):
                content = rows["section_content"][ri]
                parsed = parseSubsidiaryTable(content)
                if parsed:
                    ok.append((code, corpName, year, len(parsed)))
                    found = True
                    break

                if _hasEmptyTable(content):
                    noInvestment.append((code, corpName))
                    found = True
                    break

            if found:
                break

        if not found:
            hasBiz = (
                df.filter(pl.col("report_type").str.contains("사업보고서")).height > 0
            )
            hasSection = df.filter(
                pl.col("section_title").str.contains("타법인|출자")
                & pl.col("report_type").str.contains("사업보고서")
            ).height > 0
            if hasSection:
                fail.append((code, corpName, "섹션 있으나 파싱 실패"))
            elif hasBiz:
                noSection.append((code, corpName))
            else:
                noBiz.append((code, corpName))

    print(f"\n성공: {len(ok)}개")
    print(f"타법인출자 없음 (빈 테이블): {len(noInvestment)}개")
    print(f"타법인출자 섹션 없음: {len(noSection)}개")
    print(f"사업보고서 없음: {len(noBiz)}개")
    print(f"실패: {len(fail)}개")

    total = len(ok) + len(noInvestment) + len(fail)
    if total > 0:
        rate = (len(ok) + len(noInvestment)) / total * 100
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
    for code, name, year, nSubs in ok[:15]:
        print(f"  [{code}] {name} ({year}): {nSubs}개 자회사/투자")

    if noSection:
        print(f"\n{'=' * 100}")
        print(f"타법인출자 섹션 없음 ({len(noSection)}개)")
        print(f"{'=' * 100}")
        for code, name in noSection[:20]:
            print(f"  [{code}] {name}")


if __name__ == "__main__":
    main()
