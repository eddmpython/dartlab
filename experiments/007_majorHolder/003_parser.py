"""
실험 ID: 003
실험명: 최대주주 파서 개발 + 10종목 테스트

목적:
- "최대주주 및 특수관계인" 테이블에서 핵심 데이터 추출
- 최대주주명, 관계, 지분율, 특수관계인 목록

가설:
1. 10개 종목 모두 최대주주 + 지분율 추출 성공

방법:
1. "VII. 주주에 관한 사항" 섹션에서 테이블 파싱
2. 헤더행 다음부터 데이터행 추출
3. 합계행까지 파싱

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


def parseMajorHolderTable(content: str) -> dict:
    """최대주주 및 특수관계인 테이블 파싱.

    Returns:
        dict with:
            holders: list of {name, relation, stockType, sharesStart, ratioStart, sharesEnd, ratioEnd}
            majorHolder: str (최대주주명)
            majorRatio: float (최대주주 기말 보통주 지분율)
            totalRatio: float (특수관계인 포함 전체 지분율)
    """
    lines = content.split("\n")
    result = {
        "holders": [],
        "majorHolder": None,
        "majorRatio": None,
        "totalRatio": None,
    }

    inTable = False
    headerSeen = False

    for line in lines:
        s = line.strip()
        if not s.startswith("|"):
            if inTable and headerSeen and result["holders"]:
                break
            continue

        cells = [c.strip() for c in s.split("|")]
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]
        if len(cells) < 3:
            continue

        txt = " ".join(cells)

        if all(c.replace("-", "") == "" for c in cells):
            continue

        if "성 명" in txt and "관 계" in txt:
            inTable = True
            continue
        if "성명" in txt and "관계" in txt and "주식" in txt:
            inTable = True
            continue

        if not inTable:
            continue

        if "기 초" in txt or "기초" in txt or "주식수" in txt and "지분율" in txt:
            headerSeen = True
            continue

        if "출자자수" in txt or "명 칭" in txt or "직위" in txt or "직책" in txt:
            break

        if "합 계" in cells[0] or "합계" in cells[0]:
            if len(cells) >= 5:
                ratioEnd = parseAmount(cells[4]) or parseAmount(cells[3])
                if ratioEnd and ratioEnd < 100:
                    result["totalRatio"] = ratioEnd
            break

        if len(cells) < 7:
            continue

        name = cells[0]
        relation = cells[1]
        stockType = cells[2]

        if not name or name in ("기 초", "기초", "주식수", "지분율"):
            continue

        sharesStart = parseAmount(cells[3])
        ratioStart = parseAmount(cells[4])
        sharesEnd = parseAmount(cells[5])
        ratioEnd = parseAmount(cells[6])

        holder = {
            "name": name,
            "relation": relation,
            "stockType": stockType,
            "sharesStart": sharesStart,
            "ratioStart": ratioStart,
            "sharesEnd": sharesEnd,
            "ratioEnd": ratioEnd,
        }
        result["holders"].append(holder)

        isMajor = "본인" in relation or "최대주주" in relation
        isCommon = "보통주" in stockType or "의결권 있는" in stockType
        if isMajor and isCommon and result["majorHolder"] is None:
            result["majorHolder"] = name
            result["majorRatio"] = ratioEnd

    return result


def main():
    print("=" * 100)
    print("최대주주 파서 10종목 테스트")
    print("=" * 100)

    totalTests = 0
    successTests = 0

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

        print(f"\n{'=' * 100}")
        print(f"[{code}] {corpName}")
        print(f"{'=' * 100}")

        for year in years[:1]:
            rows = df.filter(
                (pl.col("year") == year)
                & pl.col("section_title").str.contains("주주")
                & pl.col("report_type").str.contains("사업보고서")
                & ~pl.col("report_type").str.contains("기재정정|첨부")
            )
            if rows.height == 0:
                rows = df.filter(
                    (pl.col("year") == year)
                    & pl.col("section_title").str.contains("주주")
                    & pl.col("report_type").str.contains("사업보고서")
                )
            if rows.height == 0:
                print(f"  {year}: 주주 섹션 없음")
                continue

            for i in range(rows.height):
                title = rows["section_title"][i]
                content = rows["section_content"][i]

                if "최대주주" not in content and "주식소유" not in content:
                    continue

                totalTests += 1
                parsed = parseMajorHolderTable(content)

                if parsed["majorHolder"]:
                    successTests += 1
                    print(f"\n  {year} [{title}]")
                    print(
                        f"  최대주주: {parsed['majorHolder']} ({parsed['majorRatio']}%)"
                    )
                    if parsed["totalRatio"]:
                        print(f"  특수관계인 합계: {parsed['totalRatio']}%")
                    print(f"  특수관계인 수: {len(parsed['holders'])}명")

                    for h in parsed["holders"][:5]:
                        print(
                            f"    {h['name']}: {h['relation']}, "
                            f"{h['stockType']}, {h['ratioEnd']}%"
                        )
                    if len(parsed["holders"]) > 5:
                        print(f"    ... +{len(parsed['holders']) - 5}명")
                else:
                    print(f"\n  {year} [{title}] FAIL: 최대주주 추출 실패")

                break
            break

    print(f"\n{'=' * 100}")
    rate = successTests / totalTests * 100 if totalTests > 0 else 0
    print(f"결과: {successTests}/{totalTests} 성공 ({rate:.1f}%)")
    print(f"{'=' * 100}")


if __name__ == "__main__":
    main()
