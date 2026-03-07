"""
실험 ID: 012-003d
실험명: 최종 파서 — 버그 수정

목적:
- 003c 버그 수정:
  1. "2019년 1월 28일 기준" 비고 셀에서 날짜 숫자가 shares로 파싱
  2. "주2)", "주3)" 주석행이 주주로 파싱
  3. 소액주주 holderRatio 99.99 → 오류 없음 (올바른 값)

수정:
- 5% 주주: 셀 개수 기반 정확한 인덱스 매핑 (구분|주주명|소유주식수|지분율|비고)
- "주N)" 행 필터링

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
    """5% 이상 주주 현황 파싱.

    테이블 구조:
    | 구분 | 주주명 | 소유주식수 | 지분율(%) | 비고 |
    또는
    | 5% 이상 주주 | 삼성생명 | 513,535,800 | 8.60 | 특별계정 포함 |
    """
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
        if "지분율" in cellJoined and "소유주식수" in cellJoined and "구분" not in cellJoined:
            continue
        if "※" in cells[0] or re.match(r"^주\d*\)", cells[0]):
            break

        if "우리사주" in cellJoined:
            shares = None
            ratio = None
            for c in cells:
                v = parseAmount(c)
                if v is not None:
                    if v > 100:
                        shares = v
                    elif 0 < v <= 100:
                        ratio = v
            if shares or ratio:
                holders.append({"name": "우리사주조합", "shares": shares, "ratio": ratio})
            continue

        name = None
        shares = None
        ratio = None

        hasFiveLabel = "5% 이상" in cells[0] or "5%이상" in cells[0]

        if hasFiveLabel:
            if len(cells) >= 4:
                name = cells[1]
                shares = parseAmount(cells[2])
                ratio = parseAmount(cells[3])
        else:
            if len(cells) >= 3:
                name = cells[0]
                shares = parseAmount(cells[1])
                ratio = parseAmount(cells[2])
            elif len(cells) >= 2:
                name = cells[0]
                ratio = parseAmount(cells[1])

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
    """의결권 현황 파싱."""
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
                shares = None

                if len(cells) >= 3:
                    typeCell = cells[1]
                    if "보통주" in typeCell or "보통" in typeCell:
                        stockType = "보통주"
                    elif "우선주" in typeCell or "우선" in typeCell or "종류주" in typeCell:
                        stockType = "우선주"
                    shares = parseAmount(cells[2])
                elif len(cells) >= 2:
                    shares = parseAmount(cells[1])

                suffix = "Common" if stockType == "보통주" else "Preferred"
                result[f"{key}{suffix}"] = shares
                break

        if not matched and lastKey and len(cells) >= 2:
            typeCell = cells[0].replace(" ", "")
            shares = parseAmount(cells[1]) if len(cells) >= 2 else None
            if "우선주" in typeCell or "우선" in typeCell or "종류주" in typeCell:
                result[f"{lastKey}Preferred"] = shares

    return result if result else None


STOCKS = [
    "005930", "000660", "035420", "005380", "055550",
    "051910", "006400", "003550", "034020", "000270",
]


if __name__ == "__main__":
    for code in STOCKS:
        df = loadData(code)
        if df is None:
            continue

        corpName = df["corp_name"][0]
        years = sorted(df["year"].unique().to_list(), reverse=True)
        report = selectReport(df, years[0], reportKind="annual")
        if report is None:
            continue

        holderSections = report.filter(pl.col("section_title").str.contains("주주에 관한 사항"))
        totalSections = report.filter(pl.col("section_title").str.contains("주주총회"))

        fiveR = minR = None
        for i in range(holderSections.height):
            c = holderSections["section_content"][i]
            if fiveR is None: fiveR = parseFivePercentHolders(c)
            if minR is None: minR = parseMinority(c)

        votR = None
        for i in range(totalSections.height):
            c = totalSections["section_content"][i]
            if votR is None: votR = parseVotingRights(c)

        print(f"\n[{corpName}]")
        if fiveR:
            for h in fiveR:
                shares = f"{int(h['shares']):>15,}" if h.get("shares") else f"{'':>15}"
                ratio = f"{h['ratio']:>6.2f}%" if h.get("ratio") else f"{'':>7}"
                print(f"  5% | {h['name']:<40} {shares} {ratio}")
        if minR:
            print(f"  소 | 주주수={minR['minorityHolderCount']:>10,}/{minR['totalHolderCount']:>10,} ({minR['holderRatio']:.2f}%)"
                  f"  주식비율={minR['shareRatio']:.2f}%")
        if votR:
            ti = votR.get("totalIssuedCommon", 0) or 0
            nv = votR.get("noVotingCommon", 0) or 0
            vt = votR.get("votableCommon", 0) or 0
            print(f"  의 | 발행={int(ti):>15,} 의결권없음={int(nv):>12,} 행사가능={int(vt):>15,}")

    print("\n=== 성공률 ===")
    ok5 = okM = okV = 0
    for code in STOCKS:
        df = loadData(code)
        if df is None: continue
        years = sorted(df["year"].unique().to_list(), reverse=True)
        report = selectReport(df, years[0], reportKind="annual")
        if report is None: continue
        hs = report.filter(pl.col("section_title").str.contains("주주에 관한 사항"))
        ts = report.filter(pl.col("section_title").str.contains("주주총회"))
        f5 = m = v = None
        for i in range(hs.height):
            c = hs["section_content"][i]
            if f5 is None: f5 = parseFivePercentHolders(c)
            if m is None: m = parseMinority(c)
        for i in range(ts.height):
            c = ts["section_content"][i]
            if v is None: v = parseVotingRights(c)
        if f5: ok5 += 1
        if m: okM += 1
        if v: okV += 1
    print(f"  5%이상: {ok5}/10 | 소액주주: {okM}/10 | 의결권: {okV}/10")
