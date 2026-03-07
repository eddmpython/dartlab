"""원재료 + 생산설비 최종 파서 — 10개 종목 테스트."""

import sys
import io
import re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import polars as pl
from dartlab.core.dataLoader import loadData
from dartlab.core.reportSelector import selectReport


def parseAmount(text: str) -> float | None:
    if not text or text.strip() in ("", "-", "\u3000", "\u2015", "\u2013"):
        return None
    cleaned = text.strip().replace(",", "").replace(" ", "")
    isNeg = "△" in cleaned or "▲" in cleaned or (cleaned.startswith("(") and cleaned.endswith(")"))
    cleaned = re.sub(r"[△▲\(\)]", "", cleaned)
    cleaned = re.sub(r"[^\d.]", "", cleaned)
    if not cleaned or cleaned.count(".") > 1:
        return None
    cleaned = cleaned.strip(".")
    if not cleaned:
        return None
    val = float(cleaned)
    return -val if isNeg else val


def splitCells(line: str) -> list[str]:
    """파이프로 분리, 빈 셀 유지."""
    parts = line.strip().split("|")
    if parts and parts[0].strip() == "":
        parts = parts[1:]
    if parts and parts[-1].strip() == "":
        parts = parts[:-1]
    return [p.strip() for p in parts]


def parseRawMaterials(content: str) -> list[dict] | None:
    """주요 원재료 현황 파싱."""
    lines = content.split("\n")
    inSection = False
    inTable = False
    results = []
    lastSegment = None
    headerCols = 0

    for line in lines:
        s = line.strip().replace("\xa0", " ")

        if not inSection:
            if "주요 원재료" in s and ("현황" in s or "등의 현황" in s):
                inSection = True
            continue

        if not s.startswith("|"):
            if s.startswith("※") or s.startswith("주"):
                continue
            if inTable and results:
                if re.match(r"^[나다라][\.\)]", s) or "가격" in s or "생산" in s:
                    break
            continue

        if "---" in s:
            continue

        cells = splitCells(s)
        if not cells:
            continue

        joined = " ".join(cells)

        if "단위" in joined and ("억원" in joined or "백만원" in joined):
            continue

        isHeader = ("품 목" in joined or "품목" in joined) and \
                   ("매입액" in joined or "투입액" in joined or "비율" in joined or "비중" in joined)
        if isHeader:
            inTable = True
            headerCols = len(cells)
            continue

        if not inTable:
            continue

        if "※" in cells[0] or re.match(r"^주\d*\)", cells[0]):
            break

        nonEmpty = [c for c in cells if c]
        if cells[0] in ("소 계", "소계", "합 계", "합계", "총 계", "총계"):
            continue
        if len(nonEmpty) < 3:
            continue

        segment = None
        item = None
        usage = None
        amt = None
        ratio = None
        supplier = None

        hasSegmentCol = len(cells) >= headerCols and cells[0] != ""

        if hasSegmentCol:
            offset = 0
            if "매입유형" in joined or "원재료" in cells[1] or "저장품" in cells[1]:
                offset = 2
            else:
                offset = 1

            segment = cells[0]
            lastSegment = segment
            item = cells[offset] if offset < len(cells) else None
            usage = cells[offset + 1] if offset + 1 < len(cells) else None
            amt = parseAmount(cells[offset + 2]) if offset + 2 < len(cells) else None
            ratio = parseAmount(cells[offset + 3]) if offset + 3 < len(cells) else None
            supplier = cells[offset + 4] if offset + 4 < len(cells) else None
        else:
            segment = lastSegment
            item = nonEmpty[0] if len(nonEmpty) > 0 else None
            usage = nonEmpty[1] if len(nonEmpty) > 1 else None
            amt = parseAmount(nonEmpty[2]) if len(nonEmpty) > 2 else None
            ratio = parseAmount(nonEmpty[3]) if len(nonEmpty) > 3 else None
            supplier = nonEmpty[4] if len(nonEmpty) > 4 else None

        if item and item in ("소 계", "소계", "합 계", "합계", "총 계", "총계"):
            continue

        if item and (amt is not None or ratio is not None):
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
    """유형자산 변동 테이블 파싱."""
    lines = content.split("\n")
    inTable = False
    colNames = []
    result = {}

    COL_KEYS = {
        "토지": "land",
        "건물": "buildings",
        "건물및구축물": "buildings",
        "구축물": "structures",
        "기계장치": "machinery",
        "건설중인자산": "construction",
        "기타유형자산": "other",
        "기타의유형자산": "other",
        "공구기구비품": "other",
        "공구기구비품등": "other",
        "사용권자산": "rou",
        "차량운반구": "vehicles",
        "비품": "other",
        "계": "total",
        "합계": "total",
    }

    for line in lines:
        s = line.strip().replace("\xa0", " ")

        if not s.startswith("|"):
            if inTable and result:
                if s and not s.startswith("※") and not s.startswith("(") and not s.startswith("["):
                    if "시설투자" in s or "투자" in s:
                        continue
                    break
            continue

        if "---" in s:
            continue

        cells = splitCells(s)
        if not cells:
            continue
        joined = " ".join(cells)

        if "단위" in joined and ("억원" in joined or "백만원" in joined):
            continue

        hasAssetHeaders = sum(1 for c in cells if c.replace(" ", "") in COL_KEYS) >= 3
        if hasAssetHeaders and ("합계" in joined or "합 계" in joined or "계" in cells[-1]):
            colNames = []
            for c in cells:
                clean = c.replace(" ", "")
                key = COL_KEYS.get(clean)
                colNames.append(key)
            inTable = True
            continue

        if not inTable or not colNames:
            continue

        label = "".join(cells[:2]).replace(" ", "")

        if "기말" in label and ("장부" in label or "순장부" in label):
            for ci in range(len(colNames)):
                key = colNames[ci]
                if key and ci < len(cells):
                    val = parseAmount(cells[ci])
                    if val is not None:
                        result[key] = val
            if result:
                break

        if "감가상각" in label and "누계" not in label and "포함" not in label:
            for ci in range(len(colNames)):
                if colNames[ci] == "total" and ci < len(cells):
                    val = parseAmount(cells[ci])
                    if val is not None:
                        result["depreciation"] = abs(val)

        if "취득" in label and ("일반" in label or "자본적" in label):
            for ci in range(len(colNames)):
                if colNames[ci] == "total" and ci < len(cells):
                    val = parseAmount(cells[ci])
                    if val is not None:
                        result["capex"] = val

    return result if result else None


def parseCapex(content: str) -> list[dict] | None:
    """시설투자 현황 파싱."""
    lines = content.split("\n")
    inSection = False
    inTable = False
    results = []

    for line in lines:
        s = line.strip().replace("\xa0", " ")

        if not inSection:
            if "시설투자" in s or "투자계획" in s or "투자 현황" in s:
                inSection = True
            continue

        if not s.startswith("|"):
            if inTable and results:
                break
            continue
        if "---" in s:
            continue

        cells = splitCells(s)
        joined = " ".join(cells)

        if "단위" in joined:
            continue
        if ("구 분" in joined or "구분" in joined) and ("투자" in joined or "내 용" in joined):
            inTable = True
            continue
        if not inTable:
            continue

        nonEmpty = [c for c in cells if c]
        if len(nonEmpty) < 2:
            continue

        if nonEmpty[0] in ("합 계", "합계"):
            for c in reversed(nonEmpty):
                v = parseAmount(c)
                if v is not None and v > 0:
                    results.append({"segment": "합계", "amount": v})
                    break
            break

        name = nonEmpty[0]
        amt = None
        for c in reversed(nonEmpty):
            v = parseAmount(c)
            if v is not None and v > 0:
                amt = v
                break

        if name and amt:
            results.append({"segment": name, "amount": amt})

    return results if results else None


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

rawOk = rawFail = rawNa = 0
eqOk = eqFail = eqNa = 0
capOk = capFail = capNa = 0

for code, name in STOCKS:
    print(f"\n{'='*60}")
    print(f"  {name} ({code})")
    print(f"{'='*60}")

    df = loadData(code)
    years = sorted(df["year"].unique().to_list(), reverse=True)
    report = selectReport(df, years[0], reportKind="annual")
    if report is None:
        print("  보고서 없음")
        rawNa += 1; eqNa += 1; capNa += 1
        continue

    sections = report.filter(
        pl.col("section_title").str.contains("원재료")
        | pl.col("section_title").str.contains("생산설비")
    )

    if sections.height == 0:
        print("  섹션 없음")
        rawNa += 1; eqNa += 1; capNa += 1
        continue

    rawResult = eqResult = capResult = None
    for i in range(sections.height):
        c = sections["section_content"][i]
        if rawResult is None:
            rawResult = parseRawMaterials(c)
        if eqResult is None:
            eqResult = parseEquipment(c)
        if capResult is None:
            capResult = parseCapex(c)

    print(f"\n  [원재료]")
    if rawResult:
        rawOk += 1
        for r in rawResult[:6]:
            print(f"    {r['segment']:<15} | {r['item']:<20} | {r['amount']:>15,.0f} | {r['ratio']}%" if r['amount'] else f"    {r['segment']:<15} | {r['item']:<20} | {'N/A':>15} | {r['ratio']}%")
        if len(rawResult) > 6:
            print(f"    ... +{len(rawResult)-6} more")
    else:
        rawFail += 1
        print(f"    없음")

    print(f"\n  [생산설비]")
    if eqResult:
        eqOk += 1
        for k, v in eqResult.items():
            print(f"    {k:<15}: {v:>20,.0f}")
    else:
        eqFail += 1
        print(f"    없음")

    print(f"\n  [시설투자]")
    if capResult:
        capOk += 1
        for r in capResult:
            print(f"    {r['segment']:<15}: {r['amount']:>15,.0f}")
    else:
        capFail += 1
        print(f"    없음")

print(f"\n{'='*60}")
print(f"  결과 요약 (10종목)")
print(f"{'='*60}")
print(f"  원재료:   {rawOk} 성공 / {rawFail} 없음 / {rawNa} 미해당")
print(f"  생산설비: {eqOk} 성공 / {eqFail} 없음 / {eqNa} 미해당")
print(f"  시설투자: {capOk} 성공 / {capFail} 없음 / {capNa} 미해당")
