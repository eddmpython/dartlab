"""
실험 ID: 064-025
실험명: 괄호 기반 통합 전 종목 전수 검증

목적:
- 283종목 전수에서 괄호 기반 통합의 정탐/오탐 전수 확인
- 날짜 패턴 오탐 차단 규칙 포함
- 적용 전 최종 검증

방법:
1. 283종목 전수 스캔
2. 통합된 사례 전수 수집
3. 오탐 패턴 분류

실험일: 2026-03-18
"""

import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "src"))
import polars as pl
from rapidfuzz import fuzz

from dartlab.core.dataLoader import _dataDir
from dartlab.providers.dart.company import Company

_BRACKET_RE = re.compile(r"\([^)]*\)")
# 날짜/연도/인명 패턴 — 이 패턴이 괄호 안에 있으면 통합 금지
_DATE_IN_BRACKET = re.compile(r"\d{4}[.\-/]|\d{2}[.\-/]\d{2}|후보:|제\d+기")


def _extractBrackets(name: str) -> tuple[str, list[str]]:
    brackets = _BRACKET_RE.findall(name)
    skeleton = _BRACKET_RE.sub("", name).strip()
    contents = [b[1:-1] for b in brackets]
    return skeleton, contents


def _bracketMerge(allItems: list[str], periodItemVal: dict, threshold: float = 60.0):
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

        reps: list[str] = []
        for item in items:
            _, brackets = _extractBrackets(item)
            matched = False

            # 날짜/인명 괄호가 있으면 통합 금지
            hasSensitive = any(_DATE_IN_BRACKET.search(b) for b in brackets)
            if hasSensitive:
                reps.append(item)
                merged[item] = item
                continue

            for rep in reps:
                _, repBrackets = _extractBrackets(rep)
                repHasSensitive = any(_DATE_IN_BRACKET.search(b) for b in repBrackets)
                if repHasSensitive:
                    continue
                if len(brackets) != len(repBrackets):
                    continue
                if not brackets:
                    merged[item] = rep
                    matched = True
                    break
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
        return allItems, periodItemVal, 0, {}

    newPIV: dict[str, dict[str, str]] = {}
    for item in allItems:
        rep = merged[item]
        if rep not in newPIV:
            newPIV[rep] = {}
        for p, v in periodItemVal.get(item, {}).items():
            if p not in newPIV[rep]:
                newPIV[rep][p] = v

    # 통합 맵 (원본 → 대표, 원본 != 대표인 것만)
    mergeMap = {k: v for k, v in merged.items() if k != v}
    return representatives, newPIV, len(allItems) - len(representatives), mergeMap


if __name__ == "__main__":
    dataDir = _dataDir("docs")
    files = sorted(dataDir.glob("*.parquet"))
    codes = [f.stem for f in files]

    totalMerged = 0
    totalBlocks = 0
    mergeCategories = Counter()  # 통합 유형별 카운트
    allMergeSamples = []  # (code, topic, bo, orig, rep)

    for i, code in enumerate(codes):
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
                if len(items) < 2:
                    continue
                pCols = [col for col in r.columns if col != "항목"]
                piv = {}
                for item in items:
                    row = r.filter(pl.col("항목") == item)
                    piv[item] = {}
                    for p in pCols:
                        v = row[p][0]
                        if v is not None:
                            piv[item][p] = str(v)

                _, _, merged, mergeMap = _bracketMerge(items, piv)
                if merged > 0:
                    totalMerged += merged
                    for orig, rep in mergeMap.items():
                        skelO, brO = _extractBrackets(orig)
                        skelR, brR = _extractBrackets(rep)
                        # 분류
                        if any("*" in b for b in brO) or any("*" in b for b in brR):
                            mergeCategories["주석번호(*)"] += 1
                        elif any(re.search(r"[A-Za-z]", b) for b in brO):
                            mergeCategories["영문약어"] += 1
                        else:
                            mergeCategories["기타"] += 1
                        allMergeSamples.append((code, topic, bo, orig, rep))

        if (i + 1) % 50 == 0:
            print(f"  [{i+1}/{len(codes)}]...")

    print(f"\n=== 전수 검증 결과 ===")
    print(f"종목: {len(codes)}, blocks: {totalBlocks}")
    print(f"통합된 항목: {totalMerged}건")

    print(f"\n=== 통합 유형 분류 ===")
    for cat, count in mergeCategories.most_common():
        print(f"  {cat}: {count}건")

    print(f"\n=== 통합 샘플 (전수) ===")
    for code, topic, bo, orig, rep in allMergeSamples[:30]:
        print(f"  [{code}] {topic} bo={bo}: {orig}  →  {rep}")

    # 오탐 의심 (skeleton이 같은데 괄호가 완전히 다른 경우)
    print(f"\n=== 오탐 의심 ===")
    suspicious = 0
    for code, topic, bo, orig, rep in allMergeSamples:
        _, brO = _extractBrackets(orig)
        _, brR = _extractBrackets(rep)
        if brO and brR:
            for b, rb in zip(brO, brR):
                sim = fuzz.ratio(b, rb)
                if sim < 70:
                    print(f"  [{code}] {topic}: {orig}  →  {rep} (bracket sim={sim:.0f})")
                    suspicious += 1
                    break
    print(f"오탐 의심: {suspicious}건 / {totalMerged}건")
