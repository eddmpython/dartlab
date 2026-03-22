"""
실험 ID: 064-024
실험명: 괄호 내용 기반 항목 통합

목적:
- fuzzy ratio가 아니라 "괄호 밖 skeleton 일치 + 괄호 안 유사도"로 통합
- 오탐 방지 (연결≠별도, 사외이사≠사내이사)
- 정탐 달성 (SYS.LSI≈SystemLSI)

가설:
1. skeleton(괄호 제거)이 같은 항목끼리만 후보
2. 괄호 안 텍스트끼리 유사도 비교 → 모두 유사해야 통합
3. "(연결)" vs "(별도)"는 유사도 낮아서 차단
4. "(메모리,SYS.LSI)" vs "(메모리,SystemLSI)"는 유사도 높아서 통합

방법:
1. 30종목 스캔, 괄호 기반 통합 적용
2. 통합된 사례 수집 + 오탐 검사

결과 (실험 후 작성):
-

결론:
-

실험일: 2026-03-18
"""

import sys, re
from collections import defaultdict
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "src"))
import polars as pl
from rapidfuzz import fuzz
from dartlab.engines.company.dart.company import Company
from dartlab.core.dataLoader import _dataDir


_BRACKET_RE = re.compile(r"\([^)]*\)")


def _extractBrackets(name: str) -> tuple[str, list[str]]:
    """항목명에서 skeleton(괄호 제거)과 괄호 내용 리스트 추출."""
    brackets = _BRACKET_RE.findall(name)
    skeleton = _BRACKET_RE.sub("", name).strip()
    # 괄호 안 내용만 (괄호 기호 제거)
    contents = [b[1:-1] for b in brackets]
    return skeleton, contents


def _bracketMerge(allItems: list[str], periodItemVal: dict, threshold: float = 60.0):
    """괄호 내용 기반 항목 통합.

    1. skeleton이 같은 항목끼리 후보 그룹
    2. 괄호 내용이 모두 유사(threshold 이상)하면 통합
    3. 괄호 내용이 다르면 통합 금지
    """
    # skeleton별 그룹핑
    skelGroups: dict[str, list[str]] = defaultdict(list)
    for item in allItems:
        skel, _ = _extractBrackets(item)
        skelGroups[skel].append(item)

    merged: dict[str, str] = {}
    representatives: list[str] = []

    for skel, items in skelGroups.items():
        if len(items) == 1:
            representatives.append(items[0])
            merged[items[0]] = items[0]
            continue

        # 같은 skeleton 내에서 괄호 내용 유사도로 클러스터링
        reps: list[str] = []
        for item in items:
            _, brackets = _extractBrackets(item)
            matched = False
            for rep in reps:
                _, repBrackets = _extractBrackets(rep)
                # 괄호 수가 다르면 통합 금지
                if len(brackets) != len(repBrackets):
                    continue
                # 괄호가 없으면 skeleton만으로 통합 (완전 일치)
                if not brackets:
                    merged[item] = rep
                    matched = True
                    break
                # 모든 괄호 내용이 유사해야 통합
                allSimilar = all(
                    fuzz.ratio(b, rb) >= threshold
                    for b, rb in zip(brackets, repBrackets)
                )
                if allSimilar:
                    merged[item] = rep
                    matched = True
                    break
            if not matched:
                reps.append(item)
                merged[item] = item
        representatives.extend(reps)

    if len(representatives) >= len(allItems):
        return allItems, periodItemVal, 0

    # periodItemVal 병합
    newPIV: dict[str, dict[str, str]] = {}
    for item in allItems:
        rep = merged[item]
        if rep not in newPIV:
            newPIV[rep] = {}
        for p, v in periodItemVal.get(item, {}).items():
            if p not in newPIV[rep]:
                newPIV[rep][p] = v

    return representatives, newPIV, len(allItems) - len(representatives)


if __name__ == "__main__":
    # 먼저 핵심 케이스 테스트
    print("=== 핵심 케이스 테스트 ===")
    cases = [
        ("DS부문(메모리,SYS.LSI)", "DS부문(메모리,SystemLSI)"),
        ("(연결)당기순이익(백만원)", "(별도)당기순이익(백만원)"),
        ("(주)디엔케이코퍼레이션", "(주)디앤케이코퍼레이션"),
        ("사외이사(감사위원회위원제외)", "등기이사(사외이사,감사위원회위원제외)"),
        ("보령제약", "녹십자"),
        ("주당액면가액(원)", "주당액면가액(원)"),  # 동일
    ]
    for a, b in cases:
        skelA, brA = _extractBrackets(a)
        skelB, brB = _extractBrackets(b)
        skelMatch = skelA == skelB
        if skelMatch and len(brA) == len(brB) and brA:
            brSim = [fuzz.ratio(x, y) for x, y in zip(brA, brB)]
            allSim = all(s >= 60 for s in brSim)
            print(f"  skel='{skelA}' == '{skelB}': {skelMatch}")
            print(f"  brackets: {brA} vs {brB} → sim={brSim} → merge={allSim}")
        else:
            print(f"  skel='{skelA}' vs '{skelB}': match={skelMatch}, br={brA} vs {brB}")
        print(f"  {a}  ≈  {b}  → {'통합' if skelMatch and len(brA) == len(brB) else '분리'}")
        print()

    # 30종목 전수 스캔
    print("\n=== 30종목 전수 스캔 ===")
    dataDir = _dataDir("docs")
    files = sorted(dataDir.glob("*.parquet"))[:30]

    totalMerged = 0
    totalBlocks = 0
    samples = []

    for f in files:
        code = f.stem
        try:
            c = Company(code)
        except Exception:
            continue
        sec = c.sections
        if sec is None:
            continue

        topics = sec["topic"].unique().to_list()
        for topic in topics:
            idx = c.show(topic)
            if idx is None or not isinstance(idx, pl.DataFrame) or "block" not in idx.columns:
                continue
            tbl = idx.filter(pl.col("type") == "table")
            for bo in tbl["block"].to_list()[:5]:
                r = c.show(topic, bo)
                if r is None or "항목" not in r.columns:
                    continue
                totalBlocks += 1
                items = r["항목"].to_list()
                pCols = [col for col in r.columns if col != "항목"]
                piv = {}
                for item in items:
                    row = r.filter(pl.col("항목") == item)
                    piv[item] = {}
                    for p in pCols:
                        v = row[p][0]
                        if v is not None:
                            piv[item][p] = str(v)

                newItems, newPiv, merged = _bracketMerge(items, piv)
                if merged > 0:
                    totalMerged += merged
                    if len(samples) < 15:
                        diff = set(items) - set(newItems)
                        mergeMap = {}
                        for item in diff:
                            skel, br = _extractBrackets(item)
                            for rep in newItems:
                                repSkel, repBr = _extractBrackets(rep)
                                if skel == repSkel and len(br) == len(repBr):
                                    if not br or all(fuzz.ratio(x, y) >= 60 for x, y in zip(br, repBr)):
                                        mergeMap[item] = rep
                                        break
                        samples.append((code, topic, bo, merged, mergeMap))

    print(f"{totalBlocks} blocks 스캔, {totalMerged}건 통합")
    print(f"\n=== 통합 샘플 ===")
    for code, topic, bo, merged, mergeMap in samples:
        print(f"\n[{code}] {topic} bo={bo}: {merged}개 통합")
        for orig, rep in list(mergeMap.items())[:3]:
            print(f"  {orig}  →  {rep}")
