"""
실험 ID: 012-004
실험명: 전체 종목 테스트 — 5% 이상 주주 + 소액주주 + 의결권

목적:
- 003d 파서를 전체 데이터셋에 적용
- 성공/실패율 측정, 실패 원인 분석

가설:
1. 5% 이상 주주: 90%+ 성공 (사업보고서 보유 종목 기준)
2. 소액주주: 90%+ 성공
3. 의결권: 90%+ 성공

방법:
1. data/docsData 전체 종목 순회
2. 최신 사업보고서에서 3개 테이블 파싱
3. 성공/실패/미해당 분류

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

from dartlab.core.dataLoader import extractCorpName, loadData
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
    lines = content.split("\n")
    inSection = False
    holders = []

    for line in lines:
        s = line.strip().replace("\xa0", " ")

        if not inSection:
            if "5% 이상 주주" in s or "5%이상 주주" in s or "5%이상주주" in s:
                inSection = True
                if not s.startswith("|"):
                    continue
            else:
                continue

        if "소액주주" in s:
            break

        if not s.startswith("|"):
            if s.startswith("※") or re.match(r"^주\d*\)", s):
                continue
            if holders and s:
                break
            continue

        if "---" in s:
            continue

        cells = [c.strip() for c in s.split("|") if c.strip()]
        if not cells:
            continue

        cellJoined = " ".join(cells)

        if "기준일" in cellJoined or "단위" in cellJoined:
            continue
        if ("구분" in cells[0] or "구 분" in cells[0]) and ("주주명" in cellJoined or "소유" in cellJoined):
            continue
        if "지분율" in cellJoined and "소유주식수" in cellJoined:
            continue
        if "※" in cells[0] or re.match(r"^주\d*\)", cells[0]):
            break

        if "우리사주" in cellJoined:
            shares = ratio = None
            for c in cells:
                v = parseAmount(c)
                if v is not None:
                    if v > 100: shares = v
                    elif 0 < v <= 100: ratio = v
            if shares or ratio:
                holders.append({"name": "우리사주조합", "shares": shares, "ratio": ratio})
            continue

        hasFiveLabel = "5% 이상" in cells[0] or "5%이상" in cells[0]

        if hasFiveLabel:
            if len(cells) >= 4:
                name = cells[1]
                shares = parseAmount(cells[2])
                ratio = parseAmount(cells[3])
                if name and (shares or ratio):
                    holders.append({"name": name, "shares": shares, "ratio": ratio})
        else:
            if len(cells) >= 3:
                name = cells[0]
                shares = parseAmount(cells[1])
                ratio = parseAmount(cells[2])
                if name and (shares or ratio):
                    holders.append({"name": name, "shares": shares, "ratio": ratio})

    return holders if holders else None


def parseMinority(content: str) -> dict | None:
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

        if "소액주주수" in cellJoined or "구 분" in cellJoined:
            continue

        if "소액주주" not in cellJoined:
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
    lines = content.split("\n")
    inSection = False
    inTable = False
    result = {}

    ITEM_MAP = [
        ("발행주식총수", "totalIssued"),
        ("의결권없는", "noVoting"),
        ("의결권 없는", "noVoting"),
        ("정관에 의하여", "excludedByArticle"),
        ("기타 법률에 의하여", "restrictedByLaw"),
        ("의결권이 부활된", "restored"),
        ("의결권을 행사할 수 있는", "votable"),
    ]

    lastKey = None

    for line in lines:
        s = line.strip().replace("\xa0", " ")

        if not inSection:
            if "의결권 현황" in s or "의결권현황" in s:
                inSection = True
            continue

        if not s.startswith("|"):
            if inTable and result:
                if s and not s.startswith("※") and not s.startswith("(주"):
                    break
            continue

        if "---" in s:
            continue

        cells = [c.strip() for c in s.split("|") if c.strip()]
        if not cells:
            continue

        if "구 분" in cells[0] or "구분" in cells[0]:
            inTable = True
            continue

        if not inTable:
            continue

        if "※" in cells[0]:
            break

        matched = False
        for keyword, key in ITEM_MAP:
            if keyword in cells[0]:
                lastKey = key
                matched = True

                stockType = "보통주"
                if len(cells) >= 3:
                    typeCell = cells[1]
                    if "우선주" in typeCell or "우선" in typeCell or "종류주" in typeCell:
                        stockType = "우선주"
                    shares = parseAmount(cells[2])
                elif len(cells) >= 2:
                    shares = parseAmount(cells[1])
                else:
                    shares = None

                suffix = "Common" if stockType == "보통주" else "Preferred"
                result[f"{key}{suffix}"] = shares
                break

        if not matched and lastKey and len(cells) >= 2:
            typeCell = cells[0].replace(" ", "")
            shares = parseAmount(cells[1]) if len(cells) >= 2 else None
            if "우선주" in typeCell or "우선" in typeCell or "종류주" in typeCell:
                result[f"{lastKey}Preferred"] = shares

    return result if result else None


if __name__ == "__main__":
    DATA_DIR = ROOT / "data" / "docsData"
    stocks = sorted([p.stem for p in DATA_DIR.glob("*.parquet")])

    print(f"전체 종목: {len(stocks)}개\n")

    ok5 = ok_min = ok_vote = 0
    noReport = 0
    noSection5 = noSectionMin = noSectionVote = 0
    fail5 = failMin = failVote = 0
    failList5 = []
    failListMin = []
    failListVote = []

    for code in stocks:
        df = loadData(code)
        if df is None:
            noReport += 1
            continue

        corpName = extractCorpName(df) or code
        years = sorted(df["year"].unique().to_list(), reverse=True)
        report = selectReport(df, years[0], reportKind="annual")
        if report is None:
            noReport += 1
            continue

        holderSections = report.filter(pl.col("section_title").str.contains("주주에 관한 사항"))
        totalSections = report.filter(pl.col("section_title").str.contains("주주총회"))

        f5 = minR = None
        has5Section = hasMinSection = False
        for i in range(holderSections.height):
            c = holderSections["section_content"][i]
            if "5% 이상" in c or "5%이상" in c:
                has5Section = True
            if "소액주주" in c:
                hasMinSection = True
            if f5 is None: f5 = parseFivePercentHolders(c)
            if minR is None: minR = parseMinority(c)

        hasVoteSection = False
        votR = None
        for i in range(totalSections.height):
            c = totalSections["section_content"][i]
            if "의결권 현황" in c or "의결권현황" in c:
                hasVoteSection = True
            if votR is None: votR = parseVotingRights(c)

        if f5:
            ok5 += 1
        elif has5Section:
            fail5 += 1
            failList5.append(f"{corpName}({code})")
        else:
            noSection5 += 1

        if minR:
            ok_min += 1
        elif hasMinSection:
            failMin += 1
            failListMin.append(f"{corpName}({code})")
        else:
            noSectionMin += 1

        if votR:
            ok_vote += 1
        elif hasVoteSection:
            failVote += 1
            failListVote.append(f"{corpName}({code})")
        else:
            noSectionVote += 1

    total = len(stocks)
    print("=" * 60)
    print(f"{'항목':<15} {'성공':>6} {'실패':>6} {'미해당':>6} {'보고서없음':>8} {'성공률':>8}")
    print("-" * 60)

    withSection5 = ok5 + fail5
    withSectionMin = ok_min + failMin
    withSectionVote = ok_vote + failVote

    rate5 = f"{ok5/withSection5*100:.1f}%" if withSection5 > 0 else "-"
    rateMin = f"{ok_min/withSectionMin*100:.1f}%" if withSectionMin > 0 else "-"
    rateVote = f"{ok_vote/withSectionVote*100:.1f}%" if withSectionVote > 0 else "-"

    print(f"{'5%이상주주':<15} {ok5:>6} {fail5:>6} {noSection5:>6} {noReport:>8} {rate5:>8}")
    print(f"{'소액주주':<15} {ok_min:>6} {failMin:>6} {noSectionMin:>6} {noReport:>8} {rateMin:>8}")
    print(f"{'의결권':<15} {ok_vote:>6} {failVote:>6} {noSectionVote:>6} {noReport:>8} {rateVote:>8}")

    if failList5:
        print(f"\n5% 실패 ({len(failList5)}개): {', '.join(failList5[:15])}")
    if failListMin:
        print(f"소액주주 실패 ({len(failListMin)}개): {', '.join(failListMin[:15])}")
    if failListVote:
        print(f"의결권 실패 ({len(failListVote)}개): {', '.join(failListVote[:15])}")
