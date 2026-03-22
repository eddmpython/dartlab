"""
실험 ID: 004
실험명: 전체 종목 주식의 총수 파서 테스트

목적:
- 보유 데이터 전체 종목에 대해 파서 적용
- 성공/실패/데이터없음 통계 수집

가설:
1. "주식의 총수" 섹션 보유 종목 90% 이상 파싱 성공

방법:
1. data/docsData/ 전체 parquet 파일 순회
2. 각 종목 최신 사업보고서 주식 섹션 파싱
3. 성공/실패 분류

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
    files = sorted(DATA_DIR.glob("*.parquet"))
    print(f"전체 종목: {len(files)}개")
    print("=" * 100)

    ok = []
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
                & pl.col("section_title").str.contains("주식의 총수")
                & pl.col("report_type").str.contains("사업보고서")
                & ~pl.col("report_type").str.contains("기재정정|첨부")
            )
            if rows.height == 0:
                rows = df.filter(
                    (pl.col("year") == year)
                    & pl.col("section_title").str.contains("주식의 총수")
                    & pl.col("report_type").str.contains("사업보고서")
                )
            if rows.height == 0:
                continue

            content = rows["section_content"][0]
            parsed = parseShareCapitalTable(content)

            if parsed:
                ok.append((code, corpName, year, parsed))
                found = True
                break

        if not found:
            hasBiz = (
                df.filter(pl.col("report_type").str.contains("사업보고서")).height > 0
            )
            hasSection = df.filter(
                pl.col("section_title").str.contains("주식의 총수")
                & pl.col("report_type").str.contains("사업보고서")
            ).height > 0
            if hasSection:
                fail.append((code, corpName, "섹션 있으나 파싱 실패"))
            elif hasBiz:
                noSection.append((code, corpName))
            else:
                noBiz.append((code, corpName))

    print(f"\n성공: {len(ok)}개")
    print(f"주식의 총수 섹션 없음: {len(noSection)}개")
    print(f"사업보고서 없음: {len(noBiz)}개")
    print(f"실패: {len(fail)}개")

    total = len(ok) + len(fail)
    if total > 0:
        rate = len(ok) / total * 100
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
    for code, name, year, parsed in ok[:15]:
        outstanding = parsed.get("outstandingShares", 0)
        treasury = parsed.get("treasuryShares", 0)
        ratio = parsed.get("treasuryRatio", "N/A")
        print(
            f"  [{code}] {name} ({year}): "
            f"발행 {outstanding:,.0f} 자사주 {treasury:,.0f} ({ratio}%)"
        )


if __name__ == "__main__":
    main()
