import re

from dartlab.engines.docsParser.finance.summary.constants import (
    EXACT_MATCH_TOLERANCE,
    NAME_CHANGE_AMOUNT_TOLERANCE,
    NAME_CHANGE_SIMILARITY,
    RESTATEMENT_AMOUNT_TOLERANCE,
    RESTATEMENT_NAME_SIMILARITY,
)
from dartlab.engines.docsParser.finance.summary.types import BridgeResult

_QUARTER_ORDER = {"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4}


def periodToIndex(key: str) -> int:
    """period key → 정렬용 인덱스. "2024" → 2024*4+4, "2024Q1" → 2024*4+1."""
    m = re.match(r"^(\d{4})(Q[1-4])?$", key)
    if not m:
        return 0
    year = int(m.group(1))
    q = _QUARTER_ORDER.get(m.group(2), 4) if m.group(2) else 4
    return year * 4 + q


def _periodGap(cur: str, prev: str) -> int:
    """두 period key 사이의 gap. annual이면 연도차, quarterly면 분기차."""
    if not cur or not prev:
        return 0
    if "Q" not in cur and "Q" not in prev:
        try:
            return int(cur) - int(prev)
        except ValueError:
            return 0
    return periodToIndex(cur) - periodToIndex(prev)


def nameSimilarity(a: str, b: str) -> float:
    """두 계정명의 유사도 (0~1). 공통 문자 비율 기반."""
    a = a.replace("[", "").replace("]", "").replace("ㆍ", "").strip()
    b = b.replace("[", "").replace("]", "").replace("ㆍ", "").strip()
    if a == b:
        return 1.0
    if not a or not b:
        return 0.0
    common = sum(1 for c in a if c in b)
    return common / max(len(a), len(b))


def numberBridgeMatch(
    accCur: dict[str, list[float | None]],
    accPrev: dict[str, list[float | None]],
    curYear: str = "",
    prevYear: str = "",
) -> BridgeResult:
    """숫자 브릿지 매칭. 4단계: 정확→재작성→명칭변경→특수항목."""
    matched = 0
    total = 0
    usedPrev: set[str] = set()
    pairs: dict[str, str] = {}
    unmatchedCur: list[str] = []

    for nameCur, amtsCur in accCur.items():
        if len(amtsCur) < 2 or amtsCur[1] is None:
            continue
        total += 1
        prevAmt = amtsCur[1]

        candidates = []
        for namePrev, amtsPrev in accPrev.items():
            if namePrev in usedPrev:
                continue
            if len(amtsPrev) < 1 or amtsPrev[0] is None:
                continue
            if abs(prevAmt - amtsPrev[0]) < EXACT_MATCH_TOLERANCE:
                sim = nameSimilarity(nameCur, namePrev)
                candidates.append((namePrev, sim))

        if candidates:
            candidates.sort(key=lambda x: -x[1])
            bestPrev = candidates[0][0]
            matched += 1
            usedPrev.add(bestPrev)
            pairs[nameCur] = bestPrev
        else:
            unmatchedCur.append(nameCur)

    stillUnmatched: list[str] = []
    for nameCur in unmatchedCur:
        amtsCur = accCur[nameCur]
        prevAmt = amtsCur[1]
        if prevAmt == 0:
            stillUnmatched.append(nameCur)
            continue

        bestMatch = None
        bestScore = 0.0
        for namePrev, amtsPrev in accPrev.items():
            if namePrev in usedPrev:
                continue
            if len(amtsPrev) < 1 or amtsPrev[0] is None:
                continue
            curAmt = amtsPrev[0]
            if curAmt == 0:
                continue
            diff = abs(prevAmt - curAmt) / max(abs(prevAmt), abs(curAmt))
            sim = nameSimilarity(nameCur, namePrev)
            if sim >= RESTATEMENT_NAME_SIMILARITY and diff < RESTATEMENT_AMOUNT_TOLERANCE:
                score = sim * (1 - diff)
                if score > bestScore:
                    bestScore = score
                    bestMatch = namePrev

        if bestMatch:
            matched += 1
            usedPrev.add(bestMatch)
            pairs[nameCur] = bestMatch
        else:
            stillUnmatched.append(nameCur)

    for nameCur in list(stillUnmatched):
        amtsCur = accCur[nameCur]
        prevAmt = amtsCur[1]
        if prevAmt == 0:
            continue

        bestMatch = None
        bestScore = 0.0
        for namePrev, amtsPrev in accPrev.items():
            if namePrev in usedPrev:
                continue
            if len(amtsPrev) < 1 or amtsPrev[0] is None:
                continue
            curAmt = amtsPrev[0]
            if curAmt == 0:
                continue
            diff = abs(prevAmt - curAmt) / max(abs(prevAmt), abs(curAmt))
            sim = nameSimilarity(nameCur, namePrev)
            if sim >= NAME_CHANGE_SIMILARITY and diff < NAME_CHANGE_AMOUNT_TOLERANCE:
                score = sim * (1 - diff)
                if score > bestScore:
                    bestScore = score
                    bestMatch = namePrev

        if bestMatch:
            matched += 1
            usedPrev.add(bestMatch)
            pairs[nameCur] = bestMatch
            stillUnmatched.remove(nameCur)

    for nameCur in list(stillUnmatched):
        amtsCur = accCur[nameCur]

        if "주당" in nameCur and "순이익" in nameCur:
            for namePrev in accPrev:
                if namePrev in usedPrev:
                    continue
                if "주당" in namePrev and "순이익" in namePrev:
                    curType = "희석" if "희석" in nameCur else "기본"
                    prevType = "희석" if "희석" in namePrev else "기본"
                    if curType == prevType:
                        matched += 1
                        usedPrev.add(namePrev)
                        pairs[nameCur] = namePrev
                        stillUnmatched.remove(nameCur)
                        break

        elif "회사" in nameCur and "수" in nameCur:
            for namePrev in accPrev:
                if namePrev in usedPrev:
                    continue
                if "회사" in namePrev and "수" in namePrev:
                    matched += 1
                    usedPrev.add(namePrev)
                    pairs[nameCur] = namePrev
                    if nameCur in stillUnmatched:
                        stillUnmatched.remove(nameCur)
                    break

    rate = matched / total if total > 0 else 0.0
    yearGap = _periodGap(curYear, prevYear)

    return BridgeResult(
        curYear=curYear,
        prevYear=prevYear,
        rate=rate,
        matched=matched,
        total=total,
        yearGap=yearGap,
        pairs=pairs,
    )
