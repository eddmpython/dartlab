"""
실험 ID: 012-003
실험명: 5% 이상 주주 + 소액주주 + 의결권 현황 파서

목적:
- 002에서 확인한 3개 테이블의 파서 개발
- 10개 종목에서 검증

가설:
1. 5% 이상 주주: "구분 | 주주명 | 소유주식수 | 지분율" 헤더로 파싱 가능
2. 소액주주: "소액주주 | 주주수 | 전체주주수 | ..." 단일행 테이블
3. 의결권: "구분 | 주식의 종류 | 주식수" 헤더, A~F 항목별 추출

방법:
1. 각 테이블별 파싱 함수 작성
2. 10개 종목 검증

결과:
(아래 실행 결과 참조)

실험일: 2026-03-07
"""

import io
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import polars as pl

from dartlab.core.dataLoader import loadData
from dartlab.core.reportSelector import selectReport


def parseAmount(text):
    if not text or text.strip() in ("", "-", "\u3000", "\u2015", "\u2013"):
        return None
    cleaned = text.strip().replace(",", "").replace(" ", "")
    cleaned = re.sub(r"[^\d.\-]", "", cleaned)
    if not cleaned or cleaned in ("-", "."):
        return None
    if cleaned.count(".") > 1:
        return None
    return float(cleaned)


def parseFivePercentHolders(content: str) -> list[dict] | None:
    """5% 이상 주주 현황 파싱."""
    lines = content.split("\n")
    inSection = False
    inTable = False
    holders = []

    for line in lines:
        s = line.strip().replace("\xa0", " ")

        if not inSection:
            if "5% 이상 주주" in s or "5%이상 주주" in s or "5%이상주주" in s:
                inSection = True
            continue

        if not s.startswith("|"):
            if inTable and holders:
                break
            continue

        if "---" in s:
            continue

        cells = [c.strip() for c in s.split("|") if c.strip()]
        if not cells:
            continue

        if "구분" in cells[0] or "주주명" in " ".join(cells) or "기준일" in " ".join(cells):
            inTable = True
            continue

        if "지분율" in " ".join(cells) or "소유주식수" in " ".join(cells):
            continue

        if not inTable:
            if "5% 이상" in " ".join(cells) or "5%이상" in " ".join(cells):
                inTable = True
                cellsJoined = " ".join(cells)
                if any(c.replace(",", "").replace(" ", "").isdigit() for c in cells[1:]):
                    pass
                else:
                    continue

        if not inTable:
            continue

        if "※" in cells[0] or "(주" in cells[0] or "주1" in cells[0]:
            break

        cellJoined = "".join(cells)
        if "우리사주" in cellJoined:
            name = "우리사주조합"
            for c in cells:
                v = parseAmount(c)
                if v is not None and v > 0:
                    shares = None
                    ratio = None
                    for cc in cells:
                        vv = parseAmount(cc)
                        if vv is not None and vv > 100:
                            shares = vv
                        elif vv is not None and 0 < vv < 100:
                            ratio = vv
                    holders.append({"name": name, "shares": shares, "ratio": ratio})
                    break
            continue

        name = None
        shares = None
        ratio = None

        if "5% 이상" in cells[0] or "5%이상" in cells[0]:
            if len(cells) >= 4:
                name = cells[1]
                shares = parseAmount(cells[2])
                ratio = parseAmount(cells[3])
        elif len(cells) >= 3:
            name = cells[0]
            for ci in range(1, len(cells)):
                v = parseAmount(cells[ci])
                if v is None:
                    continue
                if v > 100:
                    shares = v
                elif 0 < v <= 100 and ratio is None:
                    ratio = v

        if name and (shares or ratio):
            holders.append({"name": name, "shares": shares, "ratio": ratio})

    return holders if holders else None


def parseMinority(content: str) -> dict | None:
    """소액주주 현황 파싱."""
    lines = content.split("\n")
    inSection = False

    for line in lines:
        s = line.strip().replace("\xa0", " ")

        if not inSection:
            if "소액주주" in s:
                inSection = True
            continue

        if not s.startswith("|"):
            continue
        if "---" in s:
            continue

        cells = [c.strip() for c in s.split("|") if c.strip()]
        cellJoined = " ".join(cells)

        if "소액주주" not in cellJoined:
            continue

        if "소액주주수" in cellJoined or "구 분" in cellJoined:
            continue

        numbers = []
        for c in cells:
            v = parseAmount(c)
            if v is not None:
                numbers.append(v)

        if len(numbers) >= 6:
            return {
                "minorityHolderCount": int(numbers[0]),
                "totalHolderCount": int(numbers[1]),
                "holderRatio": numbers[2],
                "minorityShares": int(numbers[3]),
                "totalShares": int(numbers[4]),
                "shareRatio": numbers[5],
            }

    return None


def parseVotingRights(content: str) -> dict | None:
    """의결권 현황 파싱."""
    lines = content.split("\n")
    inSection = False
    inTable = False

    result = {}
    ITEM_MAP = {
        "발행주식총수": "totalIssued",
        "의결권없는": "noVoting",
        "의결권 없는": "noVoting",
        "정관에 의하여": "excludedByArticle",
        "기타 법률에 의하여": "restrictedByLaw",
        "의결권이 부활된": "restored",
        "의결권을 행사할 수 있는": "votable",
    }

    for line in lines:
        s = line.strip().replace("\xa0", " ")

        if not inSection:
            if "의결권 현황" in s or "의결권현황" in s:
                inSection = True
            continue

        if not s.startswith("|"):
            if inTable and result:
                break
            continue

        if "---" in s:
            continue

        cells = [c.strip() for c in s.split("|") if c.strip()]
        if not cells:
            continue

        cellJoined = " ".join(cells)

        if "구 분" in cells[0] or "구분" in cells[0]:
            inTable = True
            continue

        if not inTable:
            continue

        if "※" in cells[0]:
            break

        for keyword, key in ITEM_MAP.items():
            if keyword in cells[0]:
                stockType = None
                shares = None

                if len(cells) >= 3:
                    if "보통주" in cells[1] or "보통" in cells[1]:
                        stockType = "보통주"
                        shares = parseAmount(cells[2])
                    elif cells[1].replace(",", "").replace(" ", "").replace("-", "").isdigit() or cells[1] == "-":
                        stockType = "보통주"
                        shares = parseAmount(cells[1])
                    else:
                        stockType = cells[1]
                        shares = parseAmount(cells[2])
                elif len(cells) >= 2:
                    shares = parseAmount(cells[1])

                if stockType == "보통주" or stockType is None:
                    commonKey = f"{key}Common"
                    if commonKey not in result:
                        result[commonKey] = shares
                elif "우선" in (stockType or ""):
                    preferredKey = f"{key}Preferred"
                    if preferredKey not in result:
                        result[preferredKey] = shares
                break
        else:
            if len(cells) >= 2:
                firstCell = cells[0].replace(" ", "")
                if "보통주" in firstCell or "보통" in firstCell:
                    v = parseAmount(cells[1]) if len(cells) >= 2 else None
                    for keyword, key in ITEM_MAP.items():
                        commonKey = f"{key}Common"
                        if commonKey in result and f"{key}Common_extra" not in result:
                            pass
                elif "우선주" in firstCell or "우선" in firstCell or "종류주" in firstCell:
                    v = parseAmount(cells[1]) if len(cells) >= 2 else None
                    lastKey = None
                    for keyword, key in ITEM_MAP.items():
                        preferredKey = f"{key}Preferred"
                        if preferredKey not in result:
                            lastKey = preferredKey
                    if lastKey:
                        result[lastKey] = v

    return result if result else None


STOCKS = [
    "005930", "000660", "035420", "005380", "055550",
    "051910", "006400", "003550", "034020", "000270",
]


if __name__ == "__main__":
    for code in STOCKS:
        df = loadData(code)
        if df is None:
            print(f"[{code}] 데이터 없음")
            continue

        corpName = df["corp_name"][0] if "corp_name" in df.columns else code
        years = sorted(df["year"].unique().to_list(), reverse=True)
        report = selectReport(df, years[0], reportKind="annual")
        if report is None:
            continue

        holderSections = report.filter(pl.col("section_title").str.contains("주주에 관한 사항"))
        totalSections = report.filter(pl.col("section_title").str.contains("주주총회"))

        print(f"\n{'='*60}")
        print(f"{corpName} ({code})")
        print(f"{'='*60}")

        fiveResult = None
        minResult = None
        for i in range(holderSections.height):
            content = holderSections["section_content"][i]
            if fiveResult is None:
                fiveResult = parseFivePercentHolders(content)
            if minResult is None:
                minResult = parseMinority(content)

        votingResult = None
        for i in range(totalSections.height):
            content = totalSections["section_content"][i]
            if votingResult is None:
                votingResult = parseVotingRights(content)

        print("\n[5% 이상 주주]")
        if fiveResult:
            for h in fiveResult:
                print(f"  {h['name']}: {h.get('shares', '?'):>15} 주 ({h.get('ratio', '?')}%)")
        else:
            print("  파싱 실패")

        print("\n[소액주주]")
        if minResult:
            print(f"  소액주주수: {minResult['minorityHolderCount']:,}명 / 전체 {minResult['totalHolderCount']:,}명 ({minResult['holderRatio']:.2f}%)")
            print(f"  소액주식수: {minResult['minorityShares']:,}주 / 전체 {minResult['totalShares']:,}주 ({minResult['shareRatio']:.2f}%)")
        else:
            print("  파싱 실패")

        print("\n[의결권]")
        if votingResult:
            for k, v in votingResult.items():
                label = k.replace("Common", "(보통주)").replace("Preferred", "(우선주)")
                print(f"  {label}: {int(v):,}" if v is not None else f"  {label}: -")
        else:
            print("  파싱 실패")

    print("\n\n=== 성공률 요약 ===")
    okFive = okMin = okVote = 0
    for code in STOCKS:
        df = loadData(code)
        if df is None:
            continue
        years = sorted(df["year"].unique().to_list(), reverse=True)
        report = selectReport(df, years[0], reportKind="annual")
        if report is None:
            continue

        holderSections = report.filter(pl.col("section_title").str.contains("주주에 관한 사항"))
        totalSections = report.filter(pl.col("section_title").str.contains("주주총회"))

        fiveR = None
        minR = None
        for i in range(holderSections.height):
            content = holderSections["section_content"][i]
            if fiveR is None:
                fiveR = parseFivePercentHolders(content)
            if minR is None:
                minR = parseMinority(content)

        votR = None
        for i in range(totalSections.height):
            content = totalSections["section_content"][i]
            if votR is None:
                votR = parseVotingRights(content)

        if fiveR:
            okFive += 1
        if minR:
            okMin += 1
        if votR:
            okVote += 1

    total = len(STOCKS)
    print(f"  5% 이상 주주: {okFive}/{total}")
    print(f"  소액주주: {okMin}/{total}")
    print(f"  의결권: {okVote}/{total}")
