"""원재료 + 생산설비 개선 파서 — 10개 종목 테스트."""

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


# ── 원재료 파서 ──────────────────────────────────────────

def _findHeaderIndices(headerCells: list[str]) -> dict:
    """헤더 셀에서 각 컬럼의 인덱스를 찾는다."""
    idx = {}
    for i, c in enumerate(headerCells):
        clean = c.replace(" ", "")
        if "사업부문" in clean or clean == "부문" or "부 문" in c:
            idx["segment"] = i
        elif "매입유형" in clean:
            if "segment" in idx:
                idx["subType"] = i
            else:
                idx["segment"] = i  # 매입유형이 첫 컬럼이면 segment
        elif clean in ("구분", "구 분") or "구분" == clean:
            if "segment" in idx:
                idx["subType"] = i
        elif "품목" in clean or "품 목" in c or "원재료명" in clean or "원부재료" in clean:
            idx["item"] = i
        elif "주요원재료" in clean:
            idx["item"] = i
        elif "용도" in clean:
            idx["usage"] = i
        elif "매입액" in clean or "투입액" in clean or "매입금액" in clean:
            idx["amount"] = i
        elif "비율" in clean or "비중" in clean:
            idx["ratio"] = i
        elif "비고" in clean or "매입처" in clean or "구매처" in clean:
            idx["supplier"] = i
    return idx


def parseRawMaterials(content: str) -> list[dict] | None:
    """주요 원재료 현황 파싱 — 헤더 직접 감지 방식."""
    lines = content.split("\n")
    inTable = False
    results = []
    lastSegment = None
    headerIdx = {}
    headerCols = 0

    for line in lines:
        s = line.strip().replace("\xa0", " ")

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

        if "단위" in joined and ("억원" in joined or "백만원" in joined or "천원" in joined or "원)" in joined):
            continue

        # 헤더 감지: 매입액/투입액 + 품목/부문 조합, 또는 매입유형 + 품목 조합
        hasAmtKw = "매입액" in joined or "투입액" in joined or "매입금액" in joined
        hasItemKw = "품 목" in joined or "품목" in joined or "원재료" in joined or \
                    "원부재료" in joined or "부문" in joined
        hasTypeKw = "매입유형" in joined
        hasRatioKw = "비율" in joined or "비중" in joined
        isHeader = (hasAmtKw and (hasItemKw or hasRatioKw)) or \
                   (hasTypeKw and hasItemKw)
        if isHeader:
            inTable = True
            headerCols = len(cells)
            headerIdx = _findHeaderIndices(cells)
            # 연도별 구조: amount 인덱스가 없으면 마지막 숫자 컬럼을 찾음
            if "amount" not in headerIdx:
                # 첫 번째 "제N기" 또는 "2024년" 패턴 찾기
                for ci, c in enumerate(cells):
                    if re.match(r"^(제\d+|20\d{2})", c.replace(" ", "")):
                        headerIdx["amount"] = ci
                        break
            continue

        if not inTable:
            continue

        if "※" in cells[0] or re.match(r"^주\d*\)", cells[0]):
            break

        nonEmpty = [c for c in cells if c]
        # 합계/소계 스킵
        first = cells[0].replace(" ", "")
        if first in ("소계", "합계", "총계", "부문계"):
            continue
        if len(nonEmpty) < 2:
            continue

        segment = None
        item = None
        usage = None
        amt = None
        ratio = None
        supplier = None

        # 헤더 인덱스 기반 매핑
        if headerIdx and "amount" in headerIdx:
            amtIdx = headerIdx["amount"]
            segIdx = headerIdx.get("segment")
            itemIdx = headerIdx.get("item")
            usageIdx = headerIdx.get("usage")
            ratioIdx = headerIdx.get("ratio")
            suppIdx = headerIdx.get("supplier")

            # shifted 감지: segment 컬럼 존재하는 테이블에서 부문이 생략된 행
            # 판단 기준: ratio 위치에 %가 포함된 텍스트가 없거나, amount 위치에 숫자 없음
            shifted = False
            if segIdx is not None and segIdx < len(cells) and cells[segIdx]:
                if ratioIdx is not None and ratioIdx < len(cells):
                    ratioText = cells[ratioIdx]
                    amtText = cells[amtIdx] if amtIdx < len(cells) else ""
                    # 정상 행: ratio 위치에 % 포함 또는 숫자, amount에도 숫자
                    amtVal = parseAmount(amtText)
                    ratioVal = parseAmount(ratioText)
                    if amtVal is not None and ("%" in ratioText or ratioVal is not None):
                        shifted = False  # 정상
                    elif amtVal is None:
                        shifted = True
                    elif "%" not in ratioText and ratioVal is None:
                        shifted = True
                elif amtIdx < len(cells):
                    if parseAmount(cells[amtIdx]) is None:
                        shifted = True

            if shifted:
                # segment 없이 왼쪽으로 밀린 행 — shift 크기를 동적 감지
                # amount 자리에 큰 숫자가 올 셀 위치를 찾아서 역산
                segment = lastSegment
                shift = 0
                for tryShift in range(1, amtIdx + 1):
                    testIdx = amtIdx - tryShift
                    if testIdx < len(cells):
                        testVal = parseAmount(cells[testIdx])
                        if testVal is not None and testVal > 100:
                            shift = tryShift
                            break
                if shift == 0:
                    shift = 1  # fallback

                si = lambda idx, s=shift: idx - s if idx is not None and idx - s >= 0 else None
                if si(itemIdx) is not None and si(itemIdx) < len(cells):
                    item = cells[si(itemIdx)]
                if si(usageIdx) is not None and si(usageIdx) < len(cells):
                    usage = cells[si(usageIdx)]
                if si(amtIdx) is not None and si(amtIdx) < len(cells):
                    amtText = cells[si(amtIdx)]
                    m2 = re.match(r"^([\d,]+)\s*\(([\d.]+)%?\)", amtText)
                    if m2:
                        amt = parseAmount(m2.group(1))
                        ratio = parseAmount(m2.group(2))
                    else:
                        amt = parseAmount(amtText)
                if si(ratioIdx) is not None and si(ratioIdx) < len(cells) and ratio is None:
                    ratio = parseAmount(cells[si(ratioIdx)])
                if si(suppIdx) is not None and si(suppIdx) < len(cells):
                    supplier = cells[si(suppIdx)]
            else:
                # 정상 행
                if segIdx is not None and segIdx < len(cells) and cells[segIdx]:
                    segment = cells[segIdx]
                    lastSegment = segment
                else:
                    segment = lastSegment

                if itemIdx is not None and itemIdx < len(cells):
                    item = cells[itemIdx]
                if usageIdx is not None and usageIdx < len(cells):
                    usage = cells[usageIdx]
                if amtIdx < len(cells):
                    amtText = cells[amtIdx]
                    # "매입액(비율)" 합쳐진 셀: "1,483,067 (43.8%)"
                    m = re.match(r"^([\d,]+)\s*\(([\d.]+)%?\)", amtText)
                    if m:
                        amt = parseAmount(m.group(1))
                        ratio = parseAmount(m.group(2))
                    else:
                        amt = parseAmount(amtText)
                if ratioIdx is not None and ratioIdx < len(cells) and ratio is None:
                    ratio = parseAmount(cells[ratioIdx])
                if suppIdx is not None and suppIdx < len(cells):
                    supplier = cells[suppIdx]
        else:
            # fallback: nonEmpty 기반
            segment = lastSegment
            item = nonEmpty[0] if len(nonEmpty) > 0 else None
            usage = nonEmpty[1] if len(nonEmpty) > 1 else None
            amt = parseAmount(nonEmpty[2]) if len(nonEmpty) > 2 else None
            ratio = parseAmount(nonEmpty[3]) if len(nonEmpty) > 3 else None
            supplier = nonEmpty[4] if len(nonEmpty) > 4 else None

        if item and item.replace(" ", "") in ("소계", "합계", "총계", "부문계"):
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


# ── 생산설비 파서 ──────────────────────────────────────────

COL_KEYS = {
    "토지": "land",
    "토 지": "land",
    "건물": "buildings",
    "건물및구축물": "buildings",
    "건물 및 구축물": "buildings",
    "건물및 구축물": "buildings",
    "구축물": "structures",
    "기계장치": "machinery",
    "건설중인자산": "construction",
    "건설중인자산등": "construction",
    "건설중인 자산": "construction",
    "기타유형자산": "other",
    "기타의유형자산": "other",
    "공구기구비품": "other",
    "공구기구비품등": "other",
    "공구와기구": "other",
    "공기구": "other",
    "사용권자산": "rou",
    "차량운반구": "vehicles",
    "비품": "fixtures",
    "미착기계": "undelivered",
    "계": "total",
    "합계": "total",
    "합 계": "total",
}

def _normalizeColKey(text: str) -> str | None:
    """컬럼명을 정규화된 키로 변환."""
    clean = text.strip().replace(" ", "")
    # 직접 매칭
    if clean in COL_KEYS:
        return COL_KEYS[clean]
    # 공백 포함 원본으로도 시도
    if text.strip() in COL_KEYS:
        return COL_KEYS[text.strip()]
    return None


def parseEquipment(content: str) -> dict | None:
    """유형자산 변동 테이블 파싱 — 기말장부금액/기말 순장부금액/기말 행."""
    lines = content.split("\n")
    inTable = False
    colNames: list[str | None] = []
    result = {}
    firstColIsLabel = False  # 헤더에 "구 분"/"계정과목"이 없고 바로 토지 시작

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

        if "단위" in joined and ("억원" in joined or "백만원" in joined or "천원" in joined):
            continue

        # 헤더 감지: 자산 컬럼이 3개 이상이고 합계/계가 있음
        assetCount = sum(1 for c in cells if _normalizeColKey(c) is not None)
        hasTotal = any(_normalizeColKey(c) == "total" for c in cells)

        if assetCount >= 3 and hasTotal:
            # 새 테이블 시작 — 이전 결과가 있으면 덮어쓸 수 있으므로 초기화
            colNames = []
            firstColIsLabel = False

            # 첫 셀이 "구 분"/"계정과목"/"과목" 등이면 행 라벨 컬럼
            firstClean = cells[0].replace(" ", "")
            if firstClean in ("구분", "계정과목", "과목"):
                firstColIsLabel = True
                colNames.append(None)
                for c in cells[1:]:
                    colNames.append(_normalizeColKey(c))
            elif _normalizeColKey(cells[0]) is not None:
                # 첫 셀부터 자산명 시작 (LG화학/카카오 패턴)
                # 행 라벨은 별도 첫 셀로 들어옴
                firstColIsLabel = True  # 데이터 행의 첫 셀이 라벨
                colNames.append(None)   # 라벨 슬롯
                for c in cells:
                    colNames.append(_normalizeColKey(c))
            else:
                # 기타 패턴
                for c in cells:
                    colNames.append(_normalizeColKey(c))

            inTable = True
            result = {}  # 각 테이블마다 초기화
            continue

        if not inTable or not colNames:
            continue

        # 행 라벨 추출 — 첫 2셀을 합치되, 두번째 셀이 숫자면 첫 셀만 사용
        label = cells[0].replace(" ", "")
        if len(cells) > 1 and parseAmount(cells[1]) is None:
            label += cells[1].replace(" ", "")

        # 기말장부금액 / 기말 순장부금액 / 기말 / 기말금액
        isEndRow = False
        if "기말" in label:
            if "장부" in label or "순장부" in label:
                isEndRow = True
            elif "취득" in label or "원가" in label:
                # "기말 취득원가" 등은 기말 행이 아님
                isEndRow = False
            elif label.replace("기말", "").replace("금액", "") == "":
                # "기말" 또는 "기말금액"만 있는 경우
                isEndRow = True

        if isEndRow:
            for ci in range(len(colNames)):
                key = colNames[ci]
                if key and ci < len(cells):
                    val = parseAmount(cells[ci])
                    if val is not None:
                        if key in result:
                            # 이미 값이 있으면 더 큰 값 우선 (합계가 부분보다 클 것)
                            pass
                        else:
                            result[key] = val
            if result:
                # 감가상각비/CAPEX도 같은 테이블에서 찾기 위해 break 안 함
                # 하지만 다음 테이블 시작 시 초기화되므로 break
                break

        # 감가상각(비) — "누계" 아닌 당기 감가상각비
        if "감가상각" in label and "누계" not in label and "포함" not in label and "원가" not in label:
            for ci in range(len(colNames)):
                if colNames[ci] == "total" and ci < len(cells):
                    val = parseAmount(cells[ci])
                    if val is not None:
                        result["depreciation"] = abs(val)

        # CAPEX
        if "취득" in label and ("일반" in label or "자본적" in label):
            for ci in range(len(colNames)):
                if colNames[ci] == "total" and ci < len(cells):
                    val = parseAmount(cells[ci])
                    if val is not None:
                        result["capex"] = val

    return result if result else None


# ── 시설투자 파서 ──────────────────────────────────────────

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

        if nonEmpty[0].replace(" ", "") in ("합계", "총계"):
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


# ── 테스트 ──────────────────────────────────────────

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
            ratioStr = f"{r['ratio']}%" if r['ratio'] is not None else "N/A"
            if r['amount'] is not None:
                print(f"    {(r['segment'] or ''):<15} | {r['item']:<20} | {r['amount']:>15,.0f} | {ratioStr}")
            else:
                print(f"    {(r['segment'] or ''):<15} | {r['item']:<20} | {'N/A':>15} | {ratioStr}")
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
