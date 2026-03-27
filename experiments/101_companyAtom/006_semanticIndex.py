"""
실험 ID: 101-006
실험명: Semantic Index — embedding 없이 의미 좌표계로 변화 블록 탐색

목적:
- topic × changeType × magnitude 3차원 좌표 + 키워드로 변화 블록의 의미 위치를 표현
- 자연어 쿼리를 좌표 필터로 변환하여 시뮬레이션
- embedding 없이도 변화 블록의 80%+ 가 의미적으로 구분 가능한지 검증

가설:
1. 3차원 좌표(topic, changeType, magnitude)만으로 변화 블록의 80%+ 가 유의미하게 구분
2. 키워드 매칭으로 자연어 쿼리의 70%+ 를 좌표 필터로 변환 가능
3. 전체 변화 블록 중 키워드 1개 이상 매칭 비율이 30%+

방법:
1. 삼성전자 sections에서 delta 수집 (004 재사용)
2. 각 delta에 3차원 좌표 + 키워드 + 금액 엔티티 부여
3. 좌표 분포 통계: 3차원 셀 밀도
4. 4개 쿼리 시뮬레이션

결과 (2026-03-27):
- 3차원 좌표 분포: 382 고유 셀 (22,060 블록 대비 1.7%) → 같은 좌표에 수십~수백 블록이 몰림
- 3D+키워드: 1,561 고유 셀 (7.1%) → 키워드 추가해도 구분력 부족
- 키워드 커버리지: 18.1% (가설 30%+ 미달) — 공시 텍스트의 82%에 탐지 키워드 없음
- 금액 엔티티: 9.7%
- 쿼리 시뮬레이션:
  - "매출이 크게 변한 블록": 2건 (너무 적음 — topic 필터가 좁음)
  - "새로 등장한 리스크": 554건 (잘 동작)
  - "전략 전환 신호": 275건 (잘 동작)
  - "AI 관련 변화": 490건, 연도별 증가 추세 명확 (41→75건)
- 핵심 발견: structural은 전부 high (정의상), appeared/disappeared의 75%가 low (짧은 텍스트)

결론:
- 가설 1 기각: 3차원 좌표만으로는 1.7% 구분력 — 같은 셀에 블록이 과밀
  - 이유: topic 45개 × 5 changeType × 3 magnitude = 이론적 최대 675셀, 실제 382셀
  - 22,060 블록에 비해 좌표 공간이 절대적으로 부족
- 가설 2 부분 성립: 쿼리 2,3,4는 잘 동작하나 쿼리 1(숫자 변화)은 필터가 너무 좁음
- 가설 3 기각: 키워드 커버리지 18.1% (30% 미만) — 공시 텍스트는 키워드 사전으로 커버 불가
- 의미: **좌표계는 "탐색 진입점"으로는 유효하나 "고유 식별자"로는 부족**
  - 쿼리 수준에서는 잘 동작 (수백 건 필터링은 사용 가능)
  - 블록 레벨 구분에는 textPathKey나 blockOrder 같은 구조적 축이 추가 필요
  - embedding이 필요한 영역은 "같은 좌표 내에서 유사 블록 클러스터링"

실험일: 2026-03-27
"""

import sys
import hashlib
import re
from collections import defaultdict
from dataclasses import dataclass, field

sys.path.insert(0, "c:/Users/MSI/OneDrive/Desktop/sideProject/dartlab/src")

PERIOD_RE = re.compile(r"^\d{4}$")
MONEY_RE = re.compile(r"(\d[\d,.]*)\s*(조|억|만|백만|천만)(?:원|달러)?")

# signal 모듈의 KEYWORDS 구조 재현 (실험 독립 실행)
KEYWORDS = {
    "트렌드": [
        "AI", "인공지능", "ESG", "탄소중립", "수소", "전기차", "자율주행",
        "메타버스", "블록체인", "클라우드", "데이터센터", "로봇", "2차전지",
        "배터리", "반도체", "바이오", "디지털전환", "플랫폼",
    ],
    "리스크": [
        "환율", "금리", "인플레이션", "경기침체", "공급망", "원자재", "유가",
        "지정학", "규제", "소송", "유동성", "파산", "구조조정", "감사의견",
    ],
    "기회": [
        "수출", "수주", "신규사업", "M&A", "시장점유율", "해외진출",
        "신약", "FDA", "특허",
    ],
}

ALL_KEYWORDS = {kw: cat for cat, kws in KEYWORDS.items() for kw in kws}


def classifyChange(textA, textB):
    """변화 유형."""
    if textA is None and textB is not None:
        return "appeared"
    if textA is not None and textB is None:
        return "disappeared"
    strippedA = re.sub(r"[\d,.]+", "N", textA)
    strippedB = re.sub(r"[\d,.]+", "N", textB)
    if strippedA == strippedB:
        return "numeric"
    lenA, lenB = len(textA), len(textB)
    if lenA > 0 and abs(lenB - lenA) / lenA > 0.5:
        return "structural"
    return "wording"


def classifyMagnitude(changeType, textA, textB):
    """변화 크기: low / medium / high."""
    if changeType == "structural":
        return "high"
    if changeType in ("appeared", "disappeared"):
        text = textB if changeType == "appeared" else textA
        size = len(text) if text else 0
        if size < 200:
            return "low"
        elif size > 1000:
            return "high"
        return "medium"
    if changeType == "numeric":
        # 숫자 추출 시도
        numsA = [float(m.replace(",", "")) for m in re.findall(r"\d[\d,]*\.?\d+", textA or "") if m.strip()]
        numsB = [float(m.replace(",", "")) for m in re.findall(r"\d[\d,]*\.?\d+", textB or "") if m.strip()]
        if numsA and numsB:
            maxChangeRate = max(
                abs(b - a) / max(abs(a), 1) for a, b in zip(numsA[:5], numsB[:5])
            )
            if maxChangeRate > 0.3:
                return "high"
            elif maxChangeRate > 0.1:
                return "medium"
            return "low"
        return "medium"
    # wording
    lenA = len(textA) if textA else 0
    lenB = len(textB) if textB else 0
    changeRate = abs(lenB - lenA) / max(lenA, 1)
    if changeRate > 0.3:
        return "high"
    elif changeRate > 0.1:
        return "medium"
    return "low"


def extractKeywords(text):
    """키워드 매칭."""
    if not text:
        return {}
    result = {}
    for kw, cat in ALL_KEYWORDS.items():
        if kw in text:
            result[kw] = cat
    return result


def extractMoneyEntities(text):
    """금액 엔티티 추출."""
    if not text:
        return []
    return [f"{m[0]}{m[1]}원" for m in MONEY_RE.findall(text)]


@dataclass
class SemanticCoord:
    """변화 블록의 의미 좌표."""

    topic: str
    changeType: str
    magnitude: str
    keywords: dict  # {keyword: category}
    kwCategories: set
    entities: list
    transition: str
    textPreview: str


def buildSemanticIndex(df):
    """sections에서 Semantic Index 구축."""
    annualCols = sorted([c for c in df.columns if PERIOD_RE.match(c)])
    topics = df.get_column("topic").to_list()

    index = []
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
            magnitude = classifyMagnitude(changeType, textA, textB)
            # 키워드는 신규/변경 텍스트에서 추출
            targetText = textB if textB else textA
            kws = extractKeywords(targetText)
            entities = extractMoneyEntities(targetText)
            preview = (targetText or "")[:100].replace("\n", "\\n")

            index.append(SemanticCoord(
                topic=topics[rowIdx],
                changeType=changeType,
                magnitude=magnitude,
                keywords=kws,
                kwCategories=set(kws.values()),
                entities=entities,
                transition=f"{colA}→{colB}",
                textPreview=preview,
            ))

    return index


def queryIndex(index, *, topics=None, changeTypes=None, magnitudes=None,
               kwContains=None, kwCategories=None):
    """좌표 기반 필터 쿼리."""
    results = index
    if topics:
        results = [c for c in results if c.topic in topics]
    if changeTypes:
        results = [c for c in results if c.changeType in changeTypes]
    if magnitudes:
        results = [c for c in results if c.magnitude in magnitudes]
    if kwContains:
        results = [c for c in results if any(kw in c.keywords for kw in kwContains)]
    if kwCategories:
        results = [c for c in results if c.kwCategories & set(kwCategories)]
    return results


def run():
    import dartlab

    c = dartlab.Company("005930")
    df = c.docs.sections
    index = buildSemanticIndex(df)

    print(f"━━━ Semantic Index 구축 완료: {len(index)} 변화 블록 ━━━")
    print()

    # 1. 3차원 좌표 분포
    print("=" * 70)
    print("1. 3차원 좌표 분포")
    print("=" * 70)

    # changeType × magnitude 크로스탭
    crossTab = defaultdict(lambda: defaultdict(int))
    for coord in index:
        crossTab[coord.changeType][coord.magnitude] += 1

    print(f"\n  {'changeType':15s} {'low':>8s} {'medium':>8s} {'high':>8s} {'합계':>8s}")
    print("  " + "─" * 47)
    for ct in ["appeared", "disappeared", "wording", "structural", "numeric"]:
        low = crossTab[ct]["low"]
        med = crossTab[ct]["medium"]
        high = crossTab[ct]["high"]
        total = low + med + high
        print(f"  {ct:15s} {low:>8d} {med:>8d} {high:>8d} {total:>8d}")

    # topic × changeType (상위 10 topic)
    topicCounts = defaultdict(int)
    for coord in index:
        topicCounts[coord.topic] += 1
    topTopics = sorted(topicCounts.items(), key=lambda x: x[1], reverse=True)[:10]

    print(f"\n  상위 10 topic × changeType:")
    print(f"  {'topic':25s} {'appeared':>9s} {'disapp.':>9s} {'wording':>9s} {'struct.':>9s} {'numeric':>9s}")
    print("  " + "─" * 72)

    for topic, _ in topTopics:
        counts = defaultdict(int)
        for coord in index:
            if coord.topic == topic:
                counts[coord.changeType] += 1
        print(f"  {topic:25s} {counts['appeared']:>9d} {counts['disappeared']:>9d} "
              f"{counts['wording']:>9d} {counts['structural']:>9d} {counts['numeric']:>9d}")
    print()

    # 2. 키워드 커버리지
    print("=" * 70)
    print("2. 키워드 커버리지")
    print("=" * 70)
    withKw = sum(1 for coord in index if coord.keywords)
    withEntity = sum(1 for coord in index if coord.entities)
    print(f"  키워드 1개+ 매칭: {withKw} / {len(index)} ({withKw/len(index)*100:.1f}%)")
    print(f"  금액 엔티티 추출: {withEntity} / {len(index)} ({withEntity/len(index)*100:.1f}%)")

    # 카테고리별 커버리지
    catCounts = defaultdict(int)
    for coord in index:
        for cat in coord.kwCategories:
            catCounts[cat] += 1
    for cat in ["트렌드", "리스크", "기회"]:
        cnt = catCounts.get(cat, 0)
        print(f"  {cat}: {cnt} 블록 ({cnt/len(index)*100:.1f}%)")

    # 가장 빈번한 키워드
    kwFreq = defaultdict(int)
    for coord in index:
        for kw in coord.keywords:
            kwFreq[kw] += 1
    print(f"\n  키워드 빈도 TOP 10:")
    for kw, cnt in sorted(kwFreq.items(), key=lambda x: x[1], reverse=True)[:10]:
        cat = ALL_KEYWORDS[kw]
        bar = "█" * (cnt // 50)
        print(f"    {kw:15s} [{cat:4s}] {cnt:5d} {bar}")
    print()

    # 3. 고유 좌표 셀 수 (구분력)
    print("=" * 70)
    print("3. 좌표 구분력")
    print("=" * 70)
    uniqueCells3d = set()
    uniqueCells3dKw = set()
    for coord in index:
        uniqueCells3d.add((coord.topic, coord.changeType, coord.magnitude))
        topKw = tuple(sorted(coord.keywords.keys())[:3])
        uniqueCells3dKw.add((coord.topic, coord.changeType, coord.magnitude, topKw))

    print(f"  3차원(topic×type×mag) 고유 셀: {len(uniqueCells3d)}")
    print(f"  3차원+키워드 고유 셀:           {len(uniqueCells3dKw)}")
    print(f"  전체 블록 대비 고유 셀 비율:    {len(uniqueCells3d)/len(index)*100:.1f}% (3D) / "
          f"{len(uniqueCells3dKw)/len(index)*100:.1f}% (3D+KW)")
    print()

    # 4. 쿼리 시뮬레이션
    print("=" * 70)
    print("4. 쿼리 시뮬레이션")
    print("=" * 70)

    queries = [
        {
            "name": "매출이 크게 변한 블록",
            "desc": "topic∈(productService,salesOrder,mdna) + numeric + high + 매출키워드",
            "params": {
                "topics": {"productService", "salesOrder", "mdna", "fsSummary"},
                "changeTypes": {"numeric"},
                "magnitudes": {"high", "medium"},
                "kwContains": {"매출", "수출", "수주", "시장점유율"},
            },
        },
        {
            "name": "새로 등장한 리스크",
            "desc": "appeared + risk topic + 리스크 카테고리",
            "params": {
                "changeTypes": {"appeared"},
                "kwCategories": {"리스크"},
            },
        },
        {
            "name": "전략 전환 신호",
            "desc": "structural + high + businessOverview/mdna",
            "params": {
                "topics": {"businessOverview", "mdna", "companyOverview"},
                "changeTypes": {"structural"},
                "magnitudes": {"high"},
            },
        },
        {
            "name": "AI 관련 변화",
            "desc": "keywords contains AI/인공지능",
            "params": {
                "kwContains": {"AI", "인공지능"},
            },
        },
    ]

    for q in queries:
        results = queryIndex(index, **q["params"])
        print(f"\n  Q: {q['name']}")
        print(f"     {q['desc']}")
        print(f"     매칭: {len(results)}건")

        if results:
            # 연도별 분포
            yearDist = defaultdict(int)
            for r in results:
                yearDist[r.transition] += 1
            yearStr = ", ".join(f"{t}:{c}" for t, c in sorted(yearDist.items()))
            print(f"     연도별: {yearStr}")

            # 대표 예시 3개
            for r in results[:3]:
                print(f"     [{r.transition}] {r.topic} / {r.changeType}:{r.magnitude}")
                if r.keywords:
                    print(f"       키워드: {', '.join(r.keywords.keys())}")
                if r.entities:
                    print(f"       금액: {', '.join(r.entities[:3])}")
                preview = r.textPreview[:80]
                print(f"       미리보기: {preview}...")

    print()

    # 5. 종합
    print("=" * 70)
    print("5. 종합 평가")
    print("=" * 70)
    print(f"  총 변화 블록: {len(index)}")
    print(f"  3D 고유 셀: {len(uniqueCells3d)} ({len(uniqueCells3d)/len(index)*100:.1f}%)")
    print(f"  3D+KW 고유 셀: {len(uniqueCells3dKw)} ({len(uniqueCells3dKw)/len(index)*100:.1f}%)")
    print(f"  키워드 커버리지: {withKw/len(index)*100:.1f}%")
    print(f"  금액 엔티티 커버리지: {withEntity/len(index)*100:.1f}%")
    print()
    distinguishable = len(uniqueCells3dKw) / len(index) * 100
    print(f"  구분력: {distinguishable:.1f}% (가설: 80%+)")
    print(f"  → {'성립' if distinguishable >= 80 else '미달 — 추가 축 필요'}")


if __name__ == "__main__":
    run()
