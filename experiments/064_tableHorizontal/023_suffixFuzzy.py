"""
실험 ID: 064-023
실험명: suffix 분리 fuzzy matching 효과 측정

목적:
- compound item(항목_헤더명)에서 suffix를 분리하여 같은 suffix끼리만 fuzzy 매칭
- 오탐 방지 + 실제 필요한 통합 달성

가설:
1. suffix 분리로 당기/전기 오탐 원천 차단
2. suffix 없는 항목끼리 base fuzzy 75%로 괄호 차이 통합 가능
3. compound item끼리는 같은 suffix일 때만 base fuzzy 매칭

방법:
1. 30종목 전수 스캔
2. suffix 분리 fuzzy vs 단순 fuzzy vs 정확매칭 비교
3. 오탐/정탐 분류

결과 (실험 후 작성):
-

결론:
-

실험일: 2026-03-17
"""

import re
import sys
from collections import defaultdict

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "src"))
import polars as pl
from rapidfuzz import fuzz

from dartlab.core.dataLoader import _dataDir
from dartlab.engines.company.dart.company import Company


def _splitCompound(item: str) -> tuple[str, str]:
    """compound item을 base + suffix로 분리."""
    idx = item.rfind("_")
    if idx > 0:
        return item[:idx], item[idx + 1:]
    return item, ""


def _suffixFuzzyMerge(allItems: list[str], periodItemVal: dict, threshold: float = 75.0):
    """suffix 분리 fuzzy matching."""
    # suffix별 그룹핑
    suffixGroups: dict[str, list[str]] = defaultdict(list)
    for item in allItems:
        _, suffix = _splitCompound(item)
        suffixGroups[suffix].append(item)

    merged: dict[str, str] = {}  # 원본 → 대표
    representatives: list[str] = []

    for suffix, items in suffixGroups.items():
        reps: list[str] = []
        for item in items:
            base, _ = _splitCompound(item)
            matched = False
            for rep in reps:
                repBase, _ = _splitCompound(rep)
                if fuzz.ratio(base, repBase) >= threshold:
                    merged[item] = rep
                    matched = True
                    break
            if not matched:
                reps.append(item)
                merged[item] = item
        representatives.extend(reps)

    if len(representatives) >= len(allItems):
        return allItems, periodItemVal, 0  # 변화 없음

    # periodItemVal 병합
    newPIV: dict[str, dict[str, str]] = {}
    for item in allItems:
        rep = merged[item]
        if rep not in newPIV:
            newPIV[rep] = {}
        for p, v in periodItemVal.get(item, {}).items():
            if p not in newPIV[rep]:
                newPIV[rep][p] = v

    mergedCount = len(allItems) - len(representatives)
    return representatives, newPIV, mergedCount


if __name__ == "__main__":
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
                # periodItemVal 재구성
                pCols = [col for col in r.columns if col != "항목"]
                piv = {}
                for item in items:
                    row = r.filter(pl.col("항목") == item)
                    piv[item] = {}
                    for p in pCols:
                        v = row[p][0]
                        if v is not None:
                            piv[item][p] = str(v)

                newItems, newPiv, merged = _suffixFuzzyMerge(items, piv, threshold=75.0)
                if merged > 0:
                    totalMerged += merged
                    if len(samples) < 10:
                        diff = set(items) - set(newItems)
                        # 어떤 항목이 어디에 통합됐는지
                        mergeMap = {}
                        for item in diff:
                            base, suffix = _splitCompound(item)
                            for rep in newItems:
                                repBase, repSuffix = _splitCompound(rep)
                                if suffix == repSuffix and fuzz.ratio(base, repBase) >= 75:
                                    mergeMap[item] = rep
                                    break
                        samples.append((code, topic, bo, merged, mergeMap))

    print(f"=== suffix 분리 fuzzy matching 결과 ===")
    print(f"30종목, {totalBlocks} blocks 스캔")
    print(f"통합된 항목: {totalMerged}건")

    # 오탐 검사: 통합된 항목 중 실제로 다른 의미인 것
    print(f"\n=== 통합 샘플 ===")
    for code, topic, bo, merged, mergeMap in samples:
        print(f"\n[{code}] {topic} bo={bo}: {merged}개 통합")
        for orig, rep in list(mergeMap.items())[:3]:
            r = fuzz.ratio(orig, rep)
            print(f"  {orig}  →  {rep}  (ratio={r:.0f})")
