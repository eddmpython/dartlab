"""유형자산 변동표 파서 실험 v2.

핵심 전략:
1. findNumberedSection으로 유형자산 섹션 추출
2. 당기/전기 블록 분리
3. 각 블록에서 자산 카테고리 헤더 + 기초~기말 변동행 추출
4. 총장부금액 테이블(세로 나열)은 건너뜀
"""

import re
import sys

sys.path.insert(0, "src")

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.notesExtractor import extractNotesContent, findNumberedSection
from dartlab.core.reportSelector import selectReport
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
    "사업결합을 통한 취득": "사업결합",
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
    """섹션을 당기/전기 블록으로 분리.
    Returns list of (period_name, block_text).
    """
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

    복합 블록(취득원가/감가상각누계액/순장부금액 등)에서
    여러 서브테이블을 발견하면 모두 반환.

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
                # 첫 헤더
                headerCategories = [c.strip() for c in cells if c.strip()]
                if headerCategories and headerCategories[0] == "구분":
                    headerCategories = headerCategories[1:]
            elif foundStart and any(r["label"] == "기말" for r in dataRows):
                # 기초→기말 완료 후 새 서브테이블 헤더
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
            # 그 외(다단 헤더 2번째 줄 등)는 무시
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
            # 기초를 다시 만나면 이전 서브테이블 저장 후 리셋
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

    # 마지막 서브테이블 저장
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
    """전치 변동표 파싱. 변동항목이 헤더, 자산 카테고리가 행 라벨.

    KB금융, SK이노베이션, SK, 삼성바이오로직스 포맷.
    헤더: | 구분 | 기초 | 취득 | 처분 | 감가상각 | ... | 기말 |
    행:   | 토지 | 값   | 값   | 값   | 값       | ... | 값   |

    고려아연 포맷 (다단 헤더).
    헤더: | | | | | 기초금액 | 취득금액 | ... | 기말금액 |
    행:   | 장부금액 | 취득원가 | 유형자산 | 토지 | 값 | 값 | ... |
    행:   | 건물 | 값 | 값 | ... |
    """
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
    """기말 행이 없으면 기초 + 변동항목 합산으로 계산."""
    labels = [r["label"] for r in parsed["rows"]]

    END_ALIASES = ("장부금액", "장부금액 합계", "순장부금액", "총장부금액", "기말금액")
    for row in parsed["rows"]:
        if row["label"] in END_ALIASES:
            row["label"] = "기말"

    labels = [r["label"] for r in parsed["rows"]]
    if "기말" in labels or "기초" not in labels:
        return parsed

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
    return parsed


def findMovementTables(section: str):
    """유형자산 주석에서 변동표를 찾아 파싱."""
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
    for period in ("당기", "전기"):
        candidates = [p for p in allParsed if p["period"] == period]
        if not candidates:
            continue
        # score=-1 (음수값 블록) 제외
        good = [c for c in candidates if _blockScore(c) >= 0]
        if not good:
            continue
        best = max(good, key=_blockScore)
        best["rows"] = _deduplicateRows(best["rows"])
        best = _computeEnd(best)
        results.append(best)

    return results


def getTotalValue(row, categories):
    for cat in categories:
        if "합계" in cat or "합 계" in cat:
            return row["values"].get(cat)
    return None


TARGETS = [
    ("005930", "삼성전자"),
    ("000660", "SK하이닉스"),
    ("035420", "NAVER"),
    ("055550", "신한지주"),
    ("006400", "삼성SDI"),
    ("051910", "LG화학"),
    ("005380", "현대자동차"),
    ("000270", "기아"),
    ("035720", "카카오"),
    ("105560", "KB금융"),
    ("068270", "셀트리온"),
    ("003550", "LG"),
    ("207940", "삼성바이오로직스"),
    ("012330", "현대모비스"),
    ("066570", "LG전자"),
    ("096770", "SK이노베이션"),
    ("034730", "SK"),
    ("316140", "우리금융지주"),
    ("003490", "대한항공"),
]


def getSection(code):
    df = loadData(code)
    corpName = extractCorpName(df)
    years = sorted(df["year"].unique().to_list(), reverse=True)
    for year in years[:2]:
        report = selectReport(df, year, reportKind="annual")
        if report is None:
            continue
        notes = extractNotesContent(report)
        if not notes:
            continue
        section = findNumberedSection(notes, "유형자산")
        if section:
            return corpName, year, section
    return corpName, None, None


if __name__ == "__main__":
    print("=" * 80)
    print("유형자산 변동표 파서 v2")
    print("=" * 80)

    success = 0
    fail = 0
    failList = []

    for code, name in TARGETS:
        corpName, year, section = getSection(code)
        print(f"\n{'─' * 60}")
        print(f"[{code}] {corpName}")

        if section is None:
            print("  → 유형자산 주석 없음")
            fail += 1
            failList.append(f"{code} {name}: 주석 없음")
            continue

        movements = findMovementTables(section)
        if not movements:
            print(f"  → {year}년: 변동표 파싱 실패")
            fail += 1
            failList.append(f"{code} {name}: 파싱 실패")
            continue

        success += 1
        for mv in movements:
            cats = mv["categories"]
            print(f"  [{mv['period']}] 카테고리 {len(cats)}개: {cats[:6]}{'...' if len(cats) > 6 else ''}")
            for row in mv["rows"]:
                total = getTotalValue(row, cats)
                if total is not None:
                    print(f"    {row['label']:<16s} → 합계: {total:>18,.0f}")
                else:
                    lastVal = None
                    for cat in reversed(cats):
                        v = row["values"].get(cat)
                        if v is not None:
                            lastVal = v
                            break
                    if lastVal is not None:
                        print(f"    {row['label']:<16s} → 마지막열: {lastVal:>15,.0f}")
                    else:
                        print(f"    {row['label']:<16s} → (값 없음)")

    print(f"\n{'=' * 80}")
    print(f"성공: {success}/{len(TARGETS)}, 실패: {fail}/{len(TARGETS)}")
    if failList:
        print("실패 목록:")
        for f in failList:
            print(f"  - {f}")
