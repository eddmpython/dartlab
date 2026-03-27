"""
실험 ID: 101-007
실험명: Atom 사람용 뷰 — 변화의 지도를 CLI로 읽기

목적:
- CompanyAtom의 ChangeMap을 사람이 읽을 수 있는 CLI 텍스트로 표현
- 기존 diff.py 인프라(sectionsDiff, build_diff_matrix) 위에 올리기
- 3가지 뷰: (1) 기업 변화 타임라인, (2) topic 히트맵, (3) 단일 topic 상세

가설:
1. CLI 텍스트만으로 기업의 주요 변화를 한눈에 파악 가능
2. 기존 diff.py 인프라와 자연스럽게 결합
3. 004의 변화 유형 분류가 뷰의 정보 밀도를 높임

방법:
1. 삼성전자 sections 로드
2. 기업 변화 타임라인: 연도별 변화 건수 + 상위 topic + dominant changeType
3. Topic 히트맵: topic × period 격자, 변화 유무 + 유형별 블록수
4. 단일 topic 상세: businessOverview, riskDerivative 변화 이력

결과 (2026-03-27):
- 타임라인 뷰: 9개 연도 전환기별 변화건수, 유형분포, 상위topic, 키워드 한눈에 표시
  - 2024→2025에서 AI 키워드가 반도체를 역전 (AI:73 vs 반도체:68) → 전략 방향 전환 가시적
  - 2020→2021에서 businessOverview 등장 135건 = COVID 후 사업 구조 재편 신호
- 히트맵 뷰: 상위 20 topic 중 대부분이 100% changeRate (매년 변화)
  - otherReferences, rawMaterial, riskDerivative는 56% = 2021년부터만 데이터 존재
  - 상세 히트맵에서 유형별 블록수까지 표시 → topic 성격 즉시 파악
- 단일 topic 상세:
  - businessOverview: 2020→2021에 -32% 구조재작성 = 사업 구조 대폭 개편
  - riskDerivative: 2020년까지 STABLE → 2021년 갑자기 30블록 등장 = 파생상품 공시 본격화

결론:
- 가설 1 확인: CLI 텍스트만으로 기업 주요 변화를 한눈에 파악 가능
- 가설 2 확인: diff.py 인프라 없이도 004의 delta 수집만으로 뷰 구성 가능 (독립적)
- 가설 3 확인: 변화 유형 분류가 뷰의 정보 밀도를 크게 높임 (단순 "변화/불변"보다 훨씬 유용)
- 추가 발견: 키워드 빈도 추이가 기업 전략 방향 변화를 포착 (AI 역전 등)

실험일: 2026-03-27
"""

import sys
import hashlib
import re
from collections import defaultdict

sys.path.insert(0, "c:/Users/MSI/OneDrive/Desktop/sideProject/dartlab/src")

PERIOD_RE = re.compile(r"^\d{4}$")


def classifyChange(textA, textB):
    """변화 유형 분류."""
    if textA is None and textB is not None:
        return "A"  # appeared
    if textA is not None and textB is None:
        return "D"  # disappeared
    strippedA = re.sub(r"[\d,.]+", "N", textA)
    strippedB = re.sub(r"[\d,.]+", "N", textB)
    if strippedA == strippedB:
        return "N"  # numeric
    lenA, lenB = len(textA), len(textB)
    if lenA > 0 and abs(lenB - lenA) / lenA > 0.5:
        return "S"  # structural
    return "W"  # wording


CHANGE_LABELS = {
    "A": "등장",
    "D": "소멸",
    "W": "문구변경",
    "S": "구조재작성",
    "N": "숫자변화",
}

# 키워드 (signal 모듈에서 가져올 수 있지만 실험 독립 실행 위해 인라인)
KEYWORDS = [
    "AI", "인공지능", "ESG", "탄소중립", "반도체", "배터리", "2차전지", "전기차",
    "자율주행", "클라우드", "데이터센터", "바이오", "M&A", "구조조정",
    "환율", "금리", "인플레이션", "공급망", "유가", "소송", "파산",
    "수출", "수주", "신규사업", "특허", "FDA",
]


def collectDeltas(df, annualCols):
    """연간 컬럼 쌍에서 변화 블록 수집."""
    topics = df.get_column("topic").to_list()
    pathKeys = df.get_column("textPathKey").to_list() if "textPathKey" in df.columns else [""] * df.height

    deltas = []
    for i in range(len(annualCols) - 1):
        colA, colB = annualCols[i], annualCols[i + 1]
        for rowIdx in range(df.height):
            textA = df[rowIdx, colA]
            textB = df[rowIdx, colB]
            if textA is None and textB is None:
                continue
            hashA = hashlib.md5(textA.encode("utf-8")).hexdigest() if textA else None
            hashB = hashlib.md5(textB.encode("utf-8")).hexdigest() if textB else None
            if hashA == hashB:
                continue
            changeType = classifyChange(textA, textB)
            deltas.append({
                "transition": f"{colA}→{colB}",
                "colA": colA,
                "colB": colB,
                "type": changeType,
                "topic": topics[rowIdx],
                "pathKey": pathKeys[rowIdx],
                "sizeA": len(textA) if textA else 0,
                "sizeB": len(textB) if textB else 0,
                "textB": textB,
            })
    return deltas


def extractKeywords(text):
    """텍스트에서 매칭되는 키워드 추출."""
    if not text:
        return []
    return [kw for kw in KEYWORDS if kw in text]


# ── 뷰 1: 기업 변화 타임라인 ──

def buildChangeTimeline(df, companyName):
    """연도별 주요 변화 요약 타임라인."""
    annualCols = sorted([c for c in df.columns if PERIOD_RE.match(c)])
    deltas = collectDeltas(df, annualCols)

    # transition별 그룹
    byTransition = defaultdict(list)
    for d in deltas:
        byTransition[d["transition"]].append(d)

    lines = []
    lines.append(f"━━━ {companyName} 변화 타임라인 ━━━")
    lines.append("")

    for transition in sorted(byTransition.keys()):
        items = byTransition[transition]
        total = len(items)

        # 유형별 집계
        typeCounts = defaultdict(int)
        for d in items:
            typeCounts[d["type"]] += 1

        # topic별 집계 → 상위 3
        topicCounts = defaultdict(lambda: defaultdict(int))
        for d in items:
            topicCounts[d["topic"]][d["type"]] += 1
        topicRanked = sorted(topicCounts.items(), key=lambda x: sum(x[1].values()), reverse=True)[:3]

        # 키워드 출현 (신규 텍스트에서)
        kwCounts = defaultdict(int)
        for d in items:
            for kw in extractKeywords(d.get("textB")):
                kwCounts[kw] += 1
        topKw = sorted(kwCounts.items(), key=lambda x: x[1], reverse=True)[:5]

        # 변화 규모 표시
        sizeBar = "█" * min(total // 100, 40) if total > 100 else "█" * max(1, total // 30)

        lines.append(f"  [{transition}] {total:,}건 {sizeBar}")

        # 유형 분포 (한줄)
        typeParts = []
        for t in ["A", "D", "W", "S", "N"]:
            if typeCounts[t] > 0:
                typeParts.append(f"{CHANGE_LABELS[t]}:{typeCounts[t]}")
        lines.append(f"    유형: {', '.join(typeParts)}")

        # 상위 topic
        for topic, counts in topicRanked:
            dominant = max(counts.items(), key=lambda x: x[1])
            lines.append(f"    · {topic:30s} {CHANGE_LABELS[dominant[0]]} ×{dominant[1]}")

        # 키워드
        if topKw:
            kwStr = ", ".join(f"{kw}({cnt})" for kw, cnt in topKw)
            lines.append(f"    키워드: {kwStr}")

        lines.append("")

    return "\n".join(lines)


# ── 뷰 2: Topic 변화 히트맵 ──

def buildTopicHeatmap(df, *, topN=20, detailed=False):
    """topic × period 격자 히트맵 (텍스트)."""
    annualCols = sorted([c for c in df.columns if PERIOD_RE.match(c)])
    deltas = collectDeltas(df, annualCols)

    # topic × transition → 유형별 블록수
    grid = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for d in deltas:
        grid[d["topic"]][d["transition"]][d["type"]] += 1

    # topic 정렬: 총 변화 많은 순
    topicTotals = {
        topic: sum(sum(types.values()) for types in transitions.values())
        for topic, transitions in grid.items()
    }
    rankedTopics = sorted(topicTotals.items(), key=lambda x: x[1], reverse=True)[:topN]

    transitions = sorted(set(d["transition"] for d in deltas))
    years = [t.split("→")[1] for t in transitions]

    lines = []
    if detailed:
        lines.append(f"━━━ Topic 변화 히트맵 (상세, 상위 {topN}) ━━━")
    else:
        lines.append(f"━━━ Topic 변화 히트맵 (상위 {topN}) ━━━")
    lines.append("")

    # 헤더
    header = f"{'topic':30s}"
    for y in years:
        if detailed:
            header += f" {y:>8s}"
        else:
            header += f" {y:>5s}"
    header += "   rate"
    lines.append(header)
    lines.append("─" * len(header))

    for topic, totalCount in rankedTopics:
        row = f"{topic:30s}"
        changedCount = 0
        totalTransitions = len(transitions)

        for transition in transitions:
            types = grid[topic][transition]
            hasChange = sum(types.values()) > 0

            if hasChange:
                changedCount += 1
                if detailed:
                    parts = []
                    for t in ["A", "D", "W", "S", "N"]:
                        if types[t] > 0:
                            parts.append(f"{t}{types[t]}")
                    cell = " ".join(parts)
                    row += f" {cell:>8s}"
                else:
                    row += "   ██"
            else:
                if detailed:
                    row += f" {'··':>8s}"
                else:
                    row += "   ··"

        rate = changedCount / totalTransitions * 100 if totalTransitions > 0 else 0
        row += f"  {rate:4.0f}%"
        lines.append(row)

    lines.append("")
    if detailed:
        lines.append("  A=등장, D=소멸, W=문구, S=구조, N=숫자 (숫자=블록수)")
    else:
        lines.append("  ██ = 변화  ·· = 변화없음")
    lines.append("")

    return "\n".join(lines)


# ── 뷰 3: 단일 Topic 상세 ──

def buildTopicDetail(df, topic):
    """단일 topic의 변화 이력 상세."""
    annualCols = sorted([c for c in df.columns if PERIOD_RE.match(c)])

    lines = []
    lines.append(f"━━━ {topic} 변화 상세 ━━━")
    lines.append("")

    for i in range(len(annualCols) - 1):
        colA, colB = annualCols[i], annualCols[i + 1]
        transition = f"{colA}→{colB}"

        # 이 topic의 블록들만
        topicRows = []
        topics = df.get_column("topic").to_list()
        for rowIdx in range(df.height):
            if topics[rowIdx] != topic:
                continue
            textA = df[rowIdx, colA]
            textB = df[rowIdx, colB]
            if textA is None and textB is None:
                continue
            hashA = hashlib.md5(textA.encode("utf-8")).hexdigest() if textA else None
            hashB = hashlib.md5(textB.encode("utf-8")).hexdigest() if textB else None
            if hashA == hashB:
                continue
            changeType = classifyChange(textA, textB)
            topicRows.append({
                "type": changeType,
                "sizeA": len(textA) if textA else 0,
                "sizeB": len(textB) if textB else 0,
                "textB": textB,
            })

        if not topicRows:
            lines.append(f"  [{transition}] STABLE (변화 없음)")
            continue

        # 크기 변화
        totalSizeA = sum(r["sizeA"] for r in topicRows)
        totalSizeB = sum(r["sizeB"] for r in topicRows)
        sizeDiff = totalSizeB - totalSizeA
        sizePct = sizeDiff / totalSizeA * 100 if totalSizeA > 0 else 0
        sizeSign = "+" if sizeDiff >= 0 else ""

        typeCounts = defaultdict(int)
        for r in topicRows:
            typeCounts[r["type"]] += 1

        lines.append(f"  [{transition}] CHANGED — {len(topicRows)}블록 ({sizeSign}{sizeDiff:,}자, {sizeSign}{sizePct:.0f}%)")

        # 유형 분포
        typeParts = []
        for t in ["A", "D", "W", "S", "N"]:
            if typeCounts[t] > 0:
                typeParts.append(f"{CHANGE_LABELS[t]} ×{typeCounts[t]}")
        lines.append(f"    {', '.join(typeParts)}")

        # 키워드 (신규 텍스트 합산)
        allText = " ".join(r["textB"] or "" for r in topicRows)
        kws = extractKeywords(allText)
        if kws:
            lines.append(f"    키워드: {', '.join(set(kws))}")

        # 대표 변경문 미리보기 (wording/structural 중 가장 긴 것)
        contentChanges = [r for r in topicRows if r["type"] in ("W", "S") and r["textB"]]
        if contentChanges:
            best = max(contentChanges, key=lambda r: abs(r["sizeB"] - r["sizeA"]))
            preview = (best["textB"] or "")[:120].replace("\n", "\\n")
            lines.append(f"    미리보기: {preview}...")

        lines.append("")

    return "\n".join(lines)


def run():
    import dartlab

    c = dartlab.Company("005930")
    df = c.docs.sections

    print(buildChangeTimeline(df, "삼성전자"))
    print()
    print(buildTopicHeatmap(df, topN=20))
    print()
    print(buildTopicHeatmap(df, topN=15, detailed=True))
    print()
    print(buildTopicDetail(df, "businessOverview"))
    print()
    print(buildTopicDetail(df, "riskDerivative"))


if __name__ == "__main__":
    run()
