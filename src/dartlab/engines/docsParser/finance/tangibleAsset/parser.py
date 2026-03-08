"""유형자산 변동표 파서.

핵심 전략:
1. 당기/전기 블록 분리
2. 각 블록에서 자산 카테고리 헤더 + 기초~기말 변동행 추출
3. 복합 블록(취득원가/감가상각/순장부금액)에서 최적 서브테이블 선택
"""

import re

from dartlab.core.tableParser import detectUnit, parseAmount

LABEL_MAP = {
    "기초 유형자산": "기초",
    "기초장부금액": "기초",
    "기초 순장부금액": "기초",
    "기초장부가액": "기초",
    "기초 장부금액": "기초",
    "기초": "기초",
    "기말 유형자산": "기말",
    "기말장부금액": "기말",
    "기말 순장부금액": "기말",
    "기말장부가액": "기말",
    "기말 장부금액": "기말",
    "기말": "기말",
    "일반취득 및 자본적지출, 유형자산": "취득",
    "일반취득 및 자본적지출": "취득",
    "사업결합을 통한 취득 이외의 증가, 유형자산": "취득",
    "사업결합을 통한 취득 이외의 증가": "취득",
    "취득": "취득",
    "취득/대체": "취득",
    "취득(*1)": "취득",
    "사업결합을 통한 취득, 유형자산": "사업결합",
    "사업결합을 통한 취득": "사업결합",
    "사업결합": "사업결합",
    "감가상각비, 유형자산": "감가상각",
    "감가상각비": "감가상각",
    "감가상각(*2)": "감가상각",
    "감가상각": "감가상각",
    "유형자산의 처분 및 폐기": "처분",
    "처분 및 폐기": "처분",
    "처분, 유형자산": "처분",
    "처분": "처분",
    "처분(*1)": "처분",
    "처분/대체": "처분",
    "당기손익으로 인식된 손상, 유형자산": "손상",
    "당기손익으로 인식된 손상": "손상",
    "손상": "손상",
    "손상/손상환입": "손상",
    "손상차손환입": "손상환입",
    "자산손상차손": "손상",
    "매각예정으로의 분류를 통한 감소, 유형자산": "매각예정",
    "매각예정으로의 분류를 통한 감소": "매각예정",
    "매각예정비유동자산 대체": "매각예정",
    "매각예정자산으로 분류": "매각예정",
    "매각예정자산(으로)부터 대체": "매각예정",
    "매각예정자산(으로)부터 대체(*3)": "매각예정",
    "기타 변동에 따른 증가(감소), 유형자산": "기타",
    "기타 변동에 따른 증가(감소)": "기타",
    "기타": "기타",
    "대체": "대체",
    "대체(*1)": "대체",
    "외화환산차이": "환율",
    "환율변동 등": "환율",
    "환율조정 효과": "환율",
    "투자부동산(으로)부터 대체": "투자부동산대체",
    "무형자산(으로)부터 대체": "무형자산대체",
    "운용리스자산(으로)부터 대체": "리스대체",
    "기초금액": "기초",
    "기말금액": "기말",
    "취득금액": "취득",
    "처분금액": "처분",
    "상각": "감가상각",
    "연결범위변동": "기타",
    "기타증감액": "기타",
    "기타(*)": "기타",
    "기타(*1)": "기타",
    "기타(*2)": "기타",
    "중단영업": "기타",
}

MOVEMENT_MARKERS = [
    "기초", "기말", "취득", "감가상각", "처분", "손상",
    "사업결합", "대체", "환율", "외화", "매각예정", "폐기",
    "순장부", "장부금액", "장부가액",
]

DESCRIPTION_MARKERS = [
    "기술", "설명", "사건", "상황", "참조", "주석",
]

_END_ALIASES = ("장부금액", "장부금액 합계", "순장부금액", "총장부금액", "기말금액")


def splitCells(line: str) -> list[str]:
    parts = line.split("|")
    if parts and parts[0].strip() == "":
        parts = parts[1:]
    if parts and parts[-1].strip() == "":
        parts = parts[:-1]
    return [p.strip() for p in parts]


def isAssetCategory(text: str) -> bool:
    keywords = [
        "토지", "건물", "구축물", "기계장치", "차량", "공구",
        "비품", "건설중", "사용권", "합계", "합 계", "엔진",
        "항공기", "미착", "사무용", "생산시설", "업무용",
        "기타유형", "기타의유형", "기타 유형", "임차점포",
    ]
    return any(kw in text for kw in keywords)


def isMovementRow(label: str) -> bool:
    collapsed = label.replace(" ", "")
    return any(kw in collapsed for kw in MOVEMENT_MARKERS)


def isDescriptionRow(cells: list[str]) -> bool:
    text = " ".join(cells)
    return any(kw in text for kw in DESCRIPTION_MARKERS) and len(text) > 100


def normalizeLabel(label: str) -> str:
    label = label.strip()
    label = re.sub(r",\s*유형자산$", "", label)
    label = re.sub(r"\s+", " ", label)

    if label in LABEL_MAP:
        return LABEL_MAP[label]

    for raw, std in LABEL_MAP.items():
        if raw in label:
            return std

    collapsed = label.replace(" ", "")
    if collapsed in LABEL_MAP:
        return LABEL_MAP[collapsed]

    for raw, std in LABEL_MAP.items():
        if raw in collapsed:
            return std

    return label


def splitPeriodBlocks(section: str) -> list[tuple[str, str]]:
    """섹션을 당기/전기 블록으로 분리."""
    lines = section.split("\n")
    blocks = []
    currentPeriod = None
    blockLines = []

    for line in lines:
        s = line.strip()

        periodMatch = None
        if s.startswith("|"):
            cells = splitCells(s)
            cellText = " ".join(cells).strip()
            cellCleaned = cellText.replace(" ", "")
            if re.match(r"^(당기|전기)\s*$", cellText):
                periodMatch = cellText.strip()
            elif re.match(r"^\(?당기(말)?\)?(\(단위|$)|^<당기(말)?>\s*(\(단위|$)", cellCleaned):
                periodMatch = "당기"
            elif re.match(r"^\(?전기(말)?\)?(\(단위|$)|^<전기(말)?>\s*(\(단위|$)", cellCleaned):
                periodMatch = "전기"
            elif re.match(r"^제\d+\(당\)기", cellCleaned):
                periodMatch = "당기"
            elif re.match(r"^제\d+\(전\)기", cellCleaned):
                periodMatch = "전기"
            elif len(cells) >= 2 and "단위" in cells[1]:
                label = cells[0].strip()
                labelClean = label.replace(" ", "")
                if re.match(r"^(당기|전기)$", labelClean):
                    periodMatch = labelClean
                elif re.match(r"^\(?당기(말)?\)?$", labelClean):
                    periodMatch = "당기"
                elif re.match(r"^\(?전기(말)?\)?$", labelClean):
                    periodMatch = "전기"
                elif re.match(r"^<당기(말)?>$", labelClean):
                    periodMatch = "당기"
                elif re.match(r"^<전기(말)?>$", labelClean):
                    periodMatch = "전기"
                elif re.match(r"^제\d+\(당\)기", labelClean):
                    periodMatch = "당기"
                elif re.match(r"^제\d+\(전\)기", labelClean):
                    periodMatch = "전기"
            else:
                nonEmpty = [c.strip() for c in cells if c.strip()]
                if len(nonEmpty) >= 1:
                    for ne in nonEmpty[:2]:
                        cleaned = ne.replace(" ", "")
                        if re.match(r"^\(?당기(말)?\)?$|^<당기(말)?>$", cleaned):
                            periodMatch = "당기"
                            break
                        if re.match(r"^\(?전기(말)?\)?$|^<전기(말)?>$", cleaned):
                            periodMatch = "전기"
                            break
                        if re.match(r"^제\s*\d+\s*\(당\)\s*기", cleaned):
                            periodMatch = "당기"
                            break
                        if re.match(r"^제\s*\d+\s*\(전\)\s*기", cleaned):
                            periodMatch = "전기"
                            break
        else:
            cleaned = s.replace(" ", "")
            if re.match(r"^[①②③④⑤]?\s*제\s*\d+\s*\(당\)\s*기", cleaned):
                periodMatch = "당기"
            elif re.match(r"^[①②③④⑤]?\s*제\s*\d+\s*\(전\)\s*기", cleaned):
                periodMatch = "전기"
            elif cleaned in ("당기", "①당기"):
                periodMatch = "당기"
            elif cleaned in ("전기", "②전기"):
                periodMatch = "전기"
            elif re.match(r"^당기말$|^당기말\s", cleaned):
                periodMatch = "당기"
            elif re.match(r"^전기말$|^전기말\s", cleaned):
                periodMatch = "전기"
            elif re.match(r"^\d+\)\s*당기", cleaned):
                periodMatch = "당기"
            elif re.match(r"^\d+\)\s*전기", cleaned):
                periodMatch = "전기"
            elif re.match(r"^\(?당기\)?$|^\(?당기말\)?$", cleaned):
                periodMatch = "당기"
            elif re.match(r"^\(?전기\)?$|^\(?전기말\)?$", cleaned):
                periodMatch = "전기"
            elif re.match(r"^<당기>$|^<당기말>$", cleaned):
                periodMatch = "당기"
            elif re.match(r"^<전기>$|^<전기말>$", cleaned):
                periodMatch = "전기"
            elif re.match(r"^[가나다라][\.\)]\s*당기", cleaned):
                periodMatch = "당기"
            elif re.match(r"^[가나다라][\.\)]\s*전기", cleaned):
                periodMatch = "전기"
            elif re.match(r"^\(\d+\)\s*당기", cleaned):
                periodMatch = "당기"
            elif re.match(r"^\(\d+\)\s*전기", cleaned):
                periodMatch = "전기"
            elif re.match(r"^-\s*당기", cleaned):
                periodMatch = "당기"
            elif re.match(r"^-\s*전기", cleaned):
                periodMatch = "전기"

        if periodMatch:
            if currentPeriod and blockLines:
                blocks.append((currentPeriod, "\n".join(blockLines)))
            currentPeriod = periodMatch
            blockLines = [line]
        else:
            blockLines.append(line)

    if currentPeriod and blockLines:
        blocks.append((currentPeriod, "\n".join(blockLines)))

    return blocks


def parseMovementBlock(block: str, period: str):
    """한 기간 블록에서 변동표 파싱.

    복합 블록에서 여러 서브테이블을 발견하면 모두 반환.
    Returns list of parsed dicts, or None.
    """
    lines = block.split("\n")
    unit = detectUnit(block)

    headerCategories = None
    dataRows = []
    foundStart = False
    allResults = []

    for line in lines:
        s = line.strip()
        if not s.startswith("|"):
            continue
        if "---" in s:
            continue

        cells = splitCells(s)
        if not cells:
            continue

        cellText = " ".join(cells)
        if "단위" in cellText:
            continue
        if all(c in ("", " ") for c in cells):
            continue

        if isDescriptionRow(cells):
            continue

        assetCount = sum(1 for c in cells if isAssetCategory(c))
        if assetCount >= 3:
            if headerCategories is None:
                headerCategories = [c.strip() for c in cells if c.strip()]
                if headerCategories and headerCategories[0] == "구분":
                    headerCategories = headerCategories[1:]
            elif foundStart and any(r["label"] == "기말" for r in dataRows):
                allResults.append({
                    "period": period,
                    "unit": unit,
                    "categories": headerCategories,
                    "rows": dataRows,
                })
                headerCategories = [c.strip() for c in cells if c.strip()]
                if headerCategories and headerCategories[0] == "구분":
                    headerCategories = headerCategories[1:]
                dataRows = []
                foundStart = False
            continue

        if headerCategories is None:
            continue

        label = cells[0].strip() if cells else ""
        labelColIdx = 0

        if not label and len(cells) > 1:
            label = cells[1].strip()
            labelColIdx = 1
        elif label and len(cells) > 1 and not isMovementRow(label):
            alt = cells[1].strip()
            if isMovementRow(alt):
                label = alt
                labelColIdx = 1

        if not label:
            continue

        normLabel = normalizeLabel(label)

        if normLabel == "기초":
            if dataRows and foundStart:
                hasStartPrev = any(r["label"] == "기초" for r in dataRows)
                if hasStartPrev:
                    allResults.append({
                        "period": period,
                        "unit": unit,
                        "categories": headerCategories,
                        "rows": dataRows,
                    })
                dataRows = []
            foundStart = True

        if not foundStart:
            continue

        if not isMovementRow(normLabel):
            continue

        valueCells = cells[labelColIdx + 1:]

        values = {}
        valIdx = 0
        for cat in headerCategories:
            if valIdx < len(valueCells):
                val = parseAmount(valueCells[valIdx])
                if val is not None and unit != 1.0:
                    val = val * unit
                values[cat] = val
            else:
                values[cat] = None
            valIdx += 1

        dataRows.append({"label": normLabel, "values": values})

    if dataRows and headerCategories:
        hasStart = any(r["label"] == "기초" for r in dataRows)
        if hasStart:
            allResults.append({
                "period": period,
                "unit": unit,
                "categories": headerCategories,
                "rows": dataRows,
            })

    return allResults if allResults else None


def parseTransposedBlock(block: str, period: str):
    """전치 변동표 파싱. 변동항목이 헤더, 자산 카테고리가 행 라벨."""
    lines = block.split("\n")
    unit = detectUnit(block)

    movementHeaders = None
    mvStartIdx = 0
    assetRows = []

    for line in lines:
        s = line.strip()
        if not s.startswith("|"):
            continue
        if "---" in s:
            continue

        cells = splitCells(s)
        if not cells:
            continue

        cellText = " ".join(cells)
        if "단위" in cellText:
            continue
        if all(c in ("", " ") for c in cells):
            continue

        movementCount = sum(1 for c in cells if isMovementRow(c))
        if movementCount >= 3 and movementHeaders is None:
            for idx, c in enumerate(cells):
                if isMovementRow(c):
                    mvStartIdx = idx
                    break
            movementHeaders = cells[mvStartIdx:]
            continue

        if isDescriptionRow(cells):
            continue

        if movementHeaders is None:
            continue

        label = None
        labelIdx = None
        for idx in range(min(len(cells), mvStartIdx + 1)):
            c = cells[idx].strip()
            if c and isAssetCategory(c):
                label = c
                labelIdx = idx
                break

        if not label:
            c0 = cells[0].strip()
            if c0 and c0 not in ("구분", "구 분", "장부금액"):
                if "합계" in c0 or "합 계" in c0:
                    label = c0
                    labelIdx = 0
            if not label:
                continue

        if "(*" in label or "(주" in label:
            continue

        if any(kw in label for kw in DESCRIPTION_MARKERS):
            continue

        numMv = len(movementHeaders)
        valStart = labelIdx + 1
        valueCells = cells[valStart:]

        if len(valueCells) > numMv:
            firstNumIdx = None
            for vi, vc in enumerate(valueCells):
                if parseAmount(vc) is not None:
                    firstNumIdx = vi
                    break
            if firstNumIdx is not None and firstNumIdx > 0:
                valueCells = valueCells[firstNumIdx:]

        values = {}
        for j, header in enumerate(movementHeaders):
            normHeader = normalizeLabel(header)
            if j < len(valueCells):
                val = parseAmount(valueCells[j])
                if val is not None and unit != 1.0:
                    val = val * unit
                values[normHeader] = val
            else:
                values[normHeader] = None

        hasAnyValue = any(v is not None for v in values.values())
        if not hasAnyValue:
            continue

        assetRows.append({"category": label, "values": values})

    if not assetRows or not movementHeaders:
        return None

    movementLabels = [normalizeLabel(h) for h in movementHeaders]

    seen = set()
    uniqueRows = []
    for r in assetRows:
        if r["category"] not in seen:
            seen.add(r["category"])
            uniqueRows.append(r)

    categories = [r["category"] for r in uniqueRows]
    rows = []
    for ml in movementLabels:
        vals = {}
        for r in uniqueRows:
            vals[r["category"]] = r["values"].get(ml)
        rows.append({"label": ml, "values": vals})

    return {
        "period": period,
        "unit": unit,
        "categories": categories,
        "rows": rows,
    }


def _blockScore(parsed):
    """블록 품질 점수. 높을수록 메인 변동표일 가능성 높음."""
    labels = [r["label"] for r in parsed["rows"]]
    hasStart = "기초" in labels
    hasEnd = "기말" in labels
    movementCount = sum(
        1 for lb in labels
        if lb in ("취득", "처분", "감가상각", "대체", "손상", "사업결합", "환율", "매각예정", "기타")
    )
    catCount = len(parsed["categories"])

    startRow = next((r for r in parsed["rows"] if r["label"] == "기초"), None)
    if startRow:
        nonZero = [v for v in startRow["values"].values() if v is not None and v != 0]
        negCount = sum(1 for v in nonZero if v < 0)
        if len(nonZero) > 0 and negCount > len(nonZero) / 2:
            return -1

    score = 0
    if hasStart and hasEnd:
        score += 1000
    elif hasStart:
        score += 500
    score += movementCount * 10
    score += catCount
    return score


def _deduplicateRows(rows):
    """중복 라벨 제거 — 첫 번째만 유지."""
    seen = set()
    result = []
    for row in rows:
        if row["label"] not in seen:
            seen.add(row["label"])
            result.append(row)
    return result


def _computeEnd(parsed):
    """기말 행이 없으면 기초 + 변동항목 합산으로 계산.

    Returns (parsed, computed) — computed=True면 기말이 계산으로 생성됨.
    """
    for row in parsed["rows"]:
        if row["label"] in _END_ALIASES:
            row["label"] = "기말"

    labels = [r["label"] for r in parsed["rows"]]
    if "기말" in labels or "기초" not in labels:
        return parsed, False

    cats = parsed["categories"]
    endValues = {}
    for cat in cats:
        total = 0.0
        allNone = True
        for row in parsed["rows"]:
            val = row["values"].get(cat)
            if val is not None:
                total += val
                allNone = False
        endValues[cat] = None if allNone else total

    parsed["rows"].append({"label": "기말", "values": endValues})
    return parsed, True


def findMovementTables(section: str):
    """유형자산 주석에서 변동표를 찾아 파싱.

    Returns list of parsed dicts (period, unit, categories, rows)
    and metadata dict with reliability info.
    """
    blocks = splitPeriodBlocks(section)

    if not blocks:
        blocks = [("당기", section)]

    allParsed = []
    for period, block in blocks:
        parsedList = parseMovementBlock(block, period)
        if parsedList:
            allParsed.extend(parsedList)
            continue
        parsed = parseTransposedBlock(block, period)
        if parsed:
            allParsed.append(parsed)

    results = []
    warnings = []
    for period in ("당기", "전기"):
        candidates = [p for p in allParsed if p["period"] == period]
        if not candidates:
            continue
        good = [c for c in candidates if _blockScore(c) >= 0]
        if not good:
            continue
        best = max(good, key=_blockScore)
        best["rows"] = _deduplicateRows(best["rows"])
        best, computed = _computeEnd(best)
        if computed:
            warnings.append("기말 행이 계산으로 생성됨 (기초+변동 합산)")
        results.append(best)

    return results, warnings


def getTotalValue(row, categories):
    """합계 카테고리의 값을 반환."""
    for cat in categories:
        if "합계" in cat or "합 계" in cat:
            return row["values"].get(cat)
    return None
