"""원재료 + 생산설비 파서 개발 — 10개 종목 테스트."""

import io
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import polars as pl

from dartlab.core.dataLoader import loadData
from dartlab.core.reportSelector import selectReport


def parseAmount(text: str) -> float | None:
    if not text or text.strip() in ("", "-", "\u3000", "\u2015", "\u2013"):
        return None
    cleaned = text.strip().replace(",", "").replace(" ", "")
    cleaned = re.sub(r"[△▲\(\)]", "", cleaned)
    cleaned = re.sub(r"[^\d.]", "", cleaned)
    if not cleaned or cleaned.count(".") > 1:
        return None
    cleaned = cleaned.strip(".")
    if not cleaned:
        return None
    return float(cleaned)


def parseRawMaterials(content: str) -> list[dict] | None:
    """주요 원재료 현황 테이블 파싱.

    Returns:
        [{"segment", "item", "usage", "amount", "ratio", "supplier"}]
    """
    lines = content.split("\n")
    inSection = False
    inTable = False
    results = []
    lastSegment = None

    for line in lines:
        s = line.strip().replace("\xa0", " ")

        if not inSection:
            if "주요 원재료" in s and ("현황" in s or "등의 현황" in s):
                inSection = True
            continue

        if s and not s.startswith("|") and not s.startswith("※"):
            if inTable and results:
                if re.match(r"^[나다라][\.\)]", s) or "가격" in s or "생산" in s:
                    break
            continue

        if not s.startswith("|"):
            continue
        if "---" in s:
            continue

        cells = [c.strip() for c in s.split("|") if c.strip()]
        if not cells:
            continue

        joined = " ".join(cells)

        if "단위" in joined and ("억원" in joined or "백만원" in joined):
            continue

        isHeader = ("매입유형" in joined or "품 목" in joined or "품목" in joined) and \
                   ("매입액" in joined or "투입액" in joined or "비율" in joined)
        if isHeader:
            inTable = True
            continue

        if not inTable:
            continue

        if "※" in cells[0] or "주)" in cells[0] or "주1)" in cells[0]:
            break

        if cells[0] in ("소 계", "소계", "합 계", "합계", "총 계", "총계"):
            continue

        if len(cells) < 4:
            continue

        segment = None
        item = None
        usage = None
        amt = None
        ratio = None
        supplier = None

        if len(cells) >= 6:
            if "부문" in cells[0] or "사업" in cells[0] or lastSegment is None:
                segment = cells[0]
                lastSegment = segment
            else:
                segment = lastSegment

            if "매입유형" not in cells[0] and "원재료" not in cells[1] and "저장품" not in cells[1]:
                if "부문" in cells[0] or cells[0] == segment:
                    item = cells[1] if len(cells) > 1 else None
                    usage = cells[2] if len(cells) > 2 else None
                    amt = parseAmount(cells[3]) if len(cells) > 3 else None
                    ratio = parseAmount(cells[4]) if len(cells) > 4 else None
                    supplier = cells[5] if len(cells) > 5 else None
                else:
                    item = cells[0]
                    usage = cells[1] if len(cells) > 1 else None
                    amt = parseAmount(cells[2]) if len(cells) > 2 else None
                    ratio = parseAmount(cells[3]) if len(cells) > 3 else None
                    supplier = cells[4] if len(cells) > 4 else None
            elif "원재료" in cells[1] or "저장품" in cells[1]:
                item = cells[2] if len(cells) > 2 else None
                usage = cells[3] if len(cells) > 3 else None
                amt = parseAmount(cells[4]) if len(cells) > 4 else None
                ratio = parseAmount(cells[5]) if len(cells) > 5 else None
                supplier = cells[6] if len(cells) > 6 else None
        elif len(cells) >= 4:
            segment = lastSegment
            item = cells[0]
            usage = cells[1]
            amt = parseAmount(cells[2])
            ratio = parseAmount(cells[3])
            supplier = cells[4] if len(cells) > 4 else None

        if item and (amt or ratio):
            if item in ("기타", "기 타") and not amt:
                continue
            results.append({
                "segment": segment,
                "item": item,
                "usage": usage,
                "amount": amt,
                "ratio": ratio,
                "supplier": supplier,
            })

    return results if results else None


def parseEquipment(content: str) -> dict | None:
    """생산설비 현황 (유형자산 변동) 테이블 파싱.

    Returns:
        {"land", "buildings", "machinery", "construction", "other", "total",
         "capex": float|None, "depreciation": float|None}
    """
    lines = content.split("\n")
    inSection = False
    inTable = False
    result = {}

    COL_MAP = {
        "토지": "land",
        "토 지": "land",
        "건물": "buildings",
        "건물및구축물": "buildings",
        "건물 및 구축물": "buildings",
        "건물및 구축물": "buildings",
        "건물 및구축물": "buildings",
        "구축물": "structures",
        "기계장치": "machinery",
        "기계 장치": "machinery",
        "건설중인자산": "construction",
        "건설중인 자산": "construction",
        "건설중인자산 등": "construction",
        "합계": "total",
        "합 계": "total",
        "계": "total",
    }

    colHeaders = []
    dataRows = {}

    for line in lines:
        s = line.strip().replace("\xa0", " ")

        if not inSection:
            if ("생산설비" in s or "설비" in s) and ("현황" in s or "투자" in s):
                inSection = True
            elif "시설 및 설비" in s or "유형자산" in s:
                inSection = True
            continue

        if not s.startswith("|"):
            if inTable and colHeaders:
                if s and not s.startswith("※") and not s.startswith("("):
                    if "투자" in s or "시설투자" in s:
                        continue
                    break
            continue
        if "---" in s:
            continue

        cells = [c.strip() for c in s.split("|") if c.strip()]
        if not cells:
            continue
        joined = " ".join(cells)

        if "단위" in joined and ("억원" in joined or "백만원" in joined):
            continue

        isHeader = any(kw in joined for kw in ["토지", "토 지", "기계장치", "건물"])
        if isHeader and ("합계" in joined or "합 계" in joined or "계" in cells[-1]):
            colHeaders = cells
            inTable = True
            continue

        if not inTable or not colHeaders:
            continue

        if len(cells) < 3:
            continue

        rowLabel = cells[0].replace(" ", "")
        if "기말" in rowLabel or "기말장부" in rowLabel or "순장부금액" in rowLabel:
            for ci, header in enumerate(colHeaders):
                headerClean = header.replace(" ", "")
                for kw, key in COL_MAP.items():
                    if kw.replace(" ", "") == headerClean:
                        if ci < len(cells):
                            val = parseAmount(cells[ci])
                            if val is not None:
                                result[key] = val
                        break
            if result:
                break

        if "감가상각" in rowLabel and "누계" not in rowLabel:
            for ci, header in enumerate(colHeaders):
                headerClean = header.replace(" ", "")
                if headerClean in ("합계", "합 계", "계"):
                    if ci < len(cells):
                        val = parseAmount(cells[ci])
                        if val is not None:
                            result["depreciation"] = val
                    break

        if "일반취득" in rowLabel or "취득" == rowLabel or "자본적지출" in rowLabel:
            for ci, header in enumerate(colHeaders):
                headerClean = header.replace(" ", "")
                if headerClean in ("합계", "합 계", "계"):
                    if ci < len(cells):
                        val = parseAmount(cells[ci])
                        if val is not None:
                            result["capex"] = val
                    break

    return result if result else None


STOCKS = [
    ("005930", "삼성전자"),
    ("000660", "SK하이닉스"),
    ("035420", "NAVER"),
    ("005380", "현대차"),
    ("051910", "LG화학"),
    ("006400", "삼성SDI"),
    ("035720", "카카오"),
    ("068270", "셀트리온"),
    ("003550", "LG"),
    ("055550", "신한지주"),
]

rawOk = 0
rawFail = 0
rawNa = 0
eqOk = 0
eqFail = 0
eqNa = 0

for code, name in STOCKS:
    print(f"\n{'='*60}")
    print(f"  {name} ({code})")
    print(f"{'='*60}")

    df = loadData(code)
    years = sorted(df["year"].unique().to_list(), reverse=True)
    report = selectReport(df, years[0], reportKind="annual")
    if report is None:
        print("  보고서 없음")
        rawNa += 1
        eqNa += 1
        continue

    sections = report.filter(
        pl.col("section_title").str.contains("원재료")
        | pl.col("section_title").str.contains("생산설비")
    )

    if sections.height == 0:
        print("  섹션 없음")
        rawNa += 1
        eqNa += 1
        continue

    rawResult = None
    eqResult = None
    for i in range(sections.height):
        content = sections["section_content"][i]
        if rawResult is None:
            rawResult = parseRawMaterials(content)
        if eqResult is None:
            eqResult = parseEquipment(content)

    print(f"\n  [원재료]")
    if rawResult:
        rawOk += 1
        for r in rawResult[:8]:
            print(f"    {r['segment']} | {r['item']} | {r['amount']} | {r['ratio']}% | {r.get('supplier', '')}")
        if len(rawResult) > 8:
            print(f"    ... +{len(rawResult)-8} more")
    else:
        rawFail += 1
        print(f"    파싱 실패")

    print(f"\n  [생산설비]")
    if eqResult:
        eqOk += 1
        for k, v in eqResult.items():
            print(f"    {k}: {v:,.0f}")
    else:
        eqFail += 1
        print(f"    파싱 실패")

print(f"\n{'='*60}")
print(f"  결과 요약")
print(f"{'='*60}")
print(f"  원재료: {rawOk} 성공 / {rawFail} 실패 / {rawNa} 미해당")
print(f"  생산설비: {eqOk} 성공 / {eqFail} 실패 / {eqNa} 미해당")
