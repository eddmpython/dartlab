"""
실험 ID: 004
실험명: 전체 종목 배당 파서 테스트

목적:
- 보유 데이터 전체 종목에 대해 배당 파서 적용
- 성공/실패/무배당 통계 수집
- 시계열 구성 가능성 확인

가설:
1. 전체 종목 90% 이상 파싱 성공

방법:
1. data/docsData/ 전체 parquet 파일 순회
2. 각 종목 최신 사업보고서 배당 섹션 파싱
3. 성공/실패/무배당/데이터없음 분류
4. 실패 케이스 상세 기록

결과:

결론:

실험일: 2026-03-06
"""
import re
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import polars as pl

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "docsData"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def parseAmount(text: str) -> float | None:
    if not text or text.strip() in ("", "-", "　", "―", "–"):
        return None
    cleaned = text.strip()
    isNegative = "△" in cleaned or "(" in cleaned
    cleaned = cleaned.replace("△", "").replace(",", "").replace(" ", "")
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


def parseDividendTable(content: str) -> dict:
    lines = content.split("\n")
    tableRows = []
    inMainTable = False

    for line in lines:
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.split("|")]
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]
        if not cells:
            continue
        if all(c.replace("-", "") == "" for c in cells):
            continue

        cellText = " ".join(cells)
        if "배당지표" in cellText or "단위" in cellText:
            inMainTable = True
            continue
        if "배당 이력" in cellText or "배당이력" in cellText:
            break
        if not inMainTable and "구" in cellText and "분" in cellText and "당기" in cellText:
            inMainTable = True
        if inMainTable or any(kw in cellText for kw in ["주당액면가액", "당기순이익", "현금배당금", "배당성향", "배당수익률"]):
            inMainTable = True
            tableRows.append(cells)

    result = {
        "netIncome": [],
        "eps": [],
        "totalDividend": [],
        "payoutRatio": [],
        "dividendYieldCommon": [],
        "dpsCommon": [],
        "dpsPreferred": [],
    }

    prevLabel = ""
    for row in tableRows:
        if len(row) < 3:
            continue

        label = row[0].strip()
        if not label:
            label = prevLabel

        stockType = ""
        values = row[1:]
        if len(row) >= 4:
            second = row[1].strip()
            if second in ("보통주", "우선주", "종류주", "1우선주(주1)", "1우선주"):
                stockType = "우선주" if "우선" in second else ("종류주" if "종류" in second else "보통주")
                values = row[2:]
            elif label in ("보통주", "우선주", "종류주", "1우선주(주1)", "1우선주"):
                stockType = "우선주" if "우선" in label else ("종류주" if "종류" in label else "보통주")
                label = prevLabel
                values = row[1:]

        amounts = [parseAmount(v) for v in values[:3]]
        while len(amounts) < 3:
            amounts.append(None)

        if "당기순이익" in label and "연결" in label:
            result["netIncome"] = amounts
        elif "당기순이익" in label and (not result["netIncome"] or all(a is None for a in result["netIncome"])):
            result["netIncome"] = amounts
        elif "주당순이익" in label:
            result["eps"] = amounts
        elif "현금배당금총액" in label:
            result["totalDividend"] = amounts
        elif "현금배당성향" in label:
            result["payoutRatio"] = amounts
        elif "현금배당수익률" in label:
            if stockType == "우선주" or label == "우선주":
                pass
            elif stockType == "종류주" and all(a is None for a in amounts):
                pass
            else:
                result["dividendYieldCommon"] = amounts
        elif "주당" in label and "현금배당금" in label:
            if stockType == "우선주" or label == "우선주":
                result["dpsPreferred"] = amounts
            elif stockType == "종류주" and all(a is None for a in amounts):
                pass
            else:
                result["dpsCommon"] = amounts

        if label and label not in ("보통주", "우선주", "종류주"):
            prevLabel = label

    return result


def main():
    files = sorted(DATA_DIR.glob("*.parquet"))

    print(f"전체 종목: {len(files)}개")
    print("=" * 100)

    ok = []
    noDividend = []
    noSection = []
    fail = []

    for path in files:
        code = path.stem
        df = pl.read_parquet(str(path))
        corpName = df["corp_name"].unique().to_list()[0] if "corp_name" in df.columns else code
        years = sorted(df["year"].unique().to_list(), reverse=True)

        found = False
        for year in years[:3]:
            rows = df.filter(
                (pl.col("year") == year)
                & pl.col("section_title").str.contains("배당")
                & pl.col("report_type").str.contains("사업보고서")
            )
            if rows.height == 0:
                continue

            content = rows["section_content"][0]
            parsed = parseDividendTable(content)

            hasDps = any(v is not None for v in parsed["dpsCommon"])
            hasYield = any(v is not None for v in parsed["dividendYieldCommon"])
            hasIncome = any(v is not None for v in parsed["netIncome"])
            hasTotalDiv = any(v is not None for v in parsed["totalDividend"])

            if hasDps or hasYield:
                ok.append((code, corpName, year))
                found = True
                break
            elif hasIncome and not hasTotalDiv:
                noDividend.append((code, corpName, year))
                found = True
                break
            elif hasIncome:
                fail.append((code, corpName, year, "순이익 있으나 DPS/수익률 없음"))
                found = True
                break
            elif not hasIncome and not hasDps:
                noDividend.append((code, corpName, year))
                found = True
                break

        if not found:
            divBiz = df.filter(
                pl.col("section_title").str.contains("배당")
                & pl.col("report_type").str.contains("사업보고서")
            )
            if divBiz.height > 0:
                fail.append((code, corpName, "", "사업보고서 배당 섹션 파싱 실패"))
            else:
                noSection.append((code, corpName))

    print(f"\n성공: {len(ok)}개")
    print(f"무배당: {len(noDividend)}개")
    print(f"배당 섹션 없음: {len(noSection)}개")
    print(f"실패: {len(fail)}개")

    total = len(ok) + len(noDividend) + len(fail)
    if total > 0:
        rate = (len(ok) + len(noDividend)) / total * 100
        print(f"\n성공률 (배당 섹션 있는 종목 기준): {rate:.1f}%")

    if fail:
        print(f"\n{'=' * 100}")
        print("실패 목록")
        print(f"{'=' * 100}")
        for code, name, year, reason in fail:
            print(f"  [{code}] {name} ({year}): {reason}")

    if noSection:
        print(f"\n{'=' * 100}")
        print(f"배당 섹션 없는 종목 ({len(noSection)}개)")
        print(f"{'=' * 100}")
        for code, name in noSection[:20]:
            print(f"  [{code}] {name}")
        if len(noSection) > 20:
            print(f"  ... +{len(noSection) - 20}개")

    print(f"\n{'=' * 100}")
    print("성공 종목 샘플 (처음 10개)")
    print(f"{'=' * 100}")
    for code, name, year in ok[:10]:
        print(f"  [{code}] {name} ({year})")


if __name__ == "__main__":
    main()
