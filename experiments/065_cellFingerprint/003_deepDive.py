"""실험 ID: 065-003
실험명: 다른 구조 판정 심층 분석 + 다종목 대규모 검증

목적:
- boardOfDirectors/companyHistory/executivePay가 왜 "다른 구조"로 나오는지 확인
- 이들이 정말 수평화 부적합한지 (이력형인지) 확인
- 다종목(10개)으로 핑거프린트 정확도 대규모 검증

가설:
1. boardOfDirectors/companyHistory는 실제 이력형 → "다른 구조" 판정이 정확
2. executivePay는 기간별 컬럼 변화 → 핑거프린트 개선 여지
3. 핑거프린트 기반 구조 판별이 10종목에서도 일관되게 동작

방법:
1. 삼성전자의 해당 topic들을 기간별로 직접 출력하여 확인
2. 10종목에서 핑거프린트 통계 수집

결과 (실험 후 작성):
- 아래 출력 참조

결론:
- 아래 출력 참조

실험일: 2026-03-18
"""

from __future__ import annotations

import re
import sys
from collections import Counter

sys.path.insert(0, "C:/Users/MSI/OneDrive/Desktop/sideProject/dartlab/src")

_NUM_RE = re.compile(r"^[△\-\(]?\s*[\d,]+(?:\.\d+)?\s*\)?(?:\s*%)?$")
_DATE_RE = re.compile(
    r"^\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2}$"
    r"|^\d{4}[.\-/]\d{1,2}$"
    r"|^\d{4}년\s*\d{1,2}월"
)
_PLACEHOLDER_RE = re.compile(r"^[\-–—]+$")
_NOTE_RE = re.compile(r"^[※☞△▲▽▼~]")


def classifyCell(cell: str) -> str:
    s = cell.strip()
    if not s:
        return "E"
    if _PLACEHOLDER_RE.match(s):
        return "N"
    if _DATE_RE.match(s):
        return "D"
    if _NUM_RE.match(s):
        return "N"
    if _NOTE_RE.match(s) and len(s) <= 3:
        return "N"
    return "T"


def _parseMdTable(md: str) -> tuple[list[str], list[list[str]]]:
    lines = [l.strip() for l in md.strip().split("\n") if l.strip()]
    headers: list[str] = []
    rows: list[list[str]] = []
    pastSep = False
    for line in lines:
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        isSep = all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip())
        if isSep:
            pastSep = True
            continue
        if not pastSep:
            headers = cells
        else:
            rows.append(cells)
    return headers, rows


class TableFingerprint:
    def __init__(self, md: str):
        headers, rows = _parseMdTable(md)
        self.headers = headers
        self.numRows = len(rows)
        self.numCols = len(headers)
        self.colDistributions: list[Counter] = []
        self.colTypes: list[str] = []

        for ci in range(self.numCols):
            counter: Counter = Counter()
            for row in rows:
                cell = row[ci] if ci < len(row) else ""
                counter[classifyCell(cell)] += 1
            self.colDistributions.append(counter)
            nonEmpty = {k: v for k, v in counter.items() if k != "E"}
            if nonEmpty:
                self.colTypes.append(max(nonEmpty, key=lambda k: nonEmpty[k]))
            else:
                self.colTypes.append("E")

        self.signature = "".join(self.colTypes)
        typeCounts = Counter(self.colTypes)
        self.profile = {
            "T": typeCounts.get("T", 0),
            "N": typeCounts.get("N", 0),
            "D": typeCounts.get("D", 0),
        }

    def __repr__(self):
        return f"FP(sig={self.signature}, {self.numRows}x{self.numCols})"


def fingerprintSimilarity(fp1, fp2):
    if fp1.signature == fp2.signature:
        return 1.0
    types = ["T", "N", "D"]
    v1 = [fp1.profile[t] for t in types]
    v2 = [fp2.profile[t] for t in types]
    dot = sum(a * b for a, b in zip(v1, v2))
    mag1 = sum(a ** 2 for a in v1) ** 0.5
    mag2 = sum(a ** 2 for a in v2) ** 0.5
    profileSim = dot / (mag1 * mag2) if (mag1 > 0 and mag2 > 0) else 0.0

    minCols = min(fp1.numCols, fp2.numCols)
    maxCols = max(fp1.numCols, fp2.numCols)
    if maxCols == 0:
        return 1.0
    matchCount = sum(1 for ci in range(minCols)
                     if ci < len(fp1.colTypes) and ci < len(fp2.colTypes)
                     and fp1.colTypes[ci] == fp2.colTypes[ci])
    positionSim = matchCount / maxCols
    return 0.4 * profileSim + 0.6 * positionSim


def deepDiveTopics():
    """삼성전자의 "다른 구조" 판정 topic 심층 분석."""
    print("=" * 70)
    print("심층 분석: boardOfDirectors / companyHistory / executivePay")
    print("=" * 70)

    from dartlab import Company
    c = Company("삼성전자")
    secs = c.docs.sections

    tableRows = secs.filter(secs["blockType"] == "table")
    periodCols = [col for col in secs.columns if re.match(r"\d{4}", col)]

    for topic in ["boardOfDirectors", "companyHistory", "executivePay"]:
        print(f"\n{'─' * 50}")
        print(f"  Topic: {topic}")
        print(f"{'─' * 50}")

        topicRows = tableRows.filter(tableRows["topic"] == topic)
        if topicRows.is_empty():
            print("    데이터 없음")
            continue

        # 기간별 핑거프린트 및 헤더 수집
        fpByPeriod = {}
        for p in periodCols[-6:]:  # 최근 6개 기간
            if p not in topicRows.columns:
                continue
            vals = topicRows[p].to_list()
            nonNull = [v for v in vals if v is not None]
            if not nonNull:
                continue
            md = str(nonNull[0])
            if not md.strip().startswith("|"):
                continue
            try:
                fp = TableFingerprint(md)
                fpByPeriod[p] = fp
                # 처음 100자만 출력
                snippet = md[:120].replace("\n", " | ")
                print(f"    {p}: {fp}  헤더={fp.headers}")
                print(f"      → {snippet}...")
            except Exception as e:
                print(f"    {p}: 파싱 실패 ({e})")

        # 인접 기간 유사도
        periods = list(fpByPeriod.keys())
        if len(periods) >= 2:
            print(f"\n    인접 기간 유사도:")
            for i in range(len(periods) - 1):
                sim = fingerprintSimilarity(fpByPeriod[periods[i]], fpByPeriod[periods[i + 1]])
                s1, s2 = fpByPeriod[periods[i]].signature, fpByPeriod[periods[i + 1]].signature
                print(f"      {periods[i]} ↔ {periods[i + 1]}: {sim:.3f}  ({s1} vs {s2})")


def multiCompanyTest():
    """10종목 대규모 검증."""
    print()
    print("=" * 70)
    print("다종목 검증 (10종목)")
    print("=" * 70)

    from dartlab import Company

    companies = [
        "삼성전자", "SK하이닉스", "현대자동차", "NAVER", "카카오",
        "LG에너지솔루션", "삼성바이오로직스", "포스코홀딩스", "셀트리온", "KB금융",
    ]

    totalSame = 0
    totalDiff = 0
    totalTopics = 0
    allDiffs: list[tuple[str, str, float]] = []

    for name in companies:
        try:
            c = Company(name)
            secs = c.docs.sections
            if secs is None:
                print(f"  {name}: sections 없음")
                continue

            tableRows = secs.filter(secs["blockType"] == "table")
            periodCols = [col for col in secs.columns if re.match(r"\d{4}", col)]
            topics = tableRows["topic"].unique().to_list()

            compSame = 0
            compDiff = 0

            for topic in topics:
                topicRows = tableRows.filter(tableRows["topic"] == topic)
                fingerprints = {}
                for p in periodCols:
                    if p not in topicRows.columns:
                        continue
                    vals = topicRows[p].to_list()
                    nonNull = [v for v in vals if v is not None]
                    if not nonNull:
                        continue
                    md = str(nonNull[0])
                    if md.strip() and md.strip().startswith("|"):
                        try:
                            fp = TableFingerprint(md)
                            if fp.numCols > 0:
                                fingerprints[p] = fp
                        except Exception:
                            pass

                if len(fingerprints) < 2:
                    continue

                periods = list(fingerprints.keys())
                pairSims = []
                for i in range(len(periods)):
                    for j in range(i + 1, min(i + 3, len(periods))):
                        sim = fingerprintSimilarity(fingerprints[periods[i]], fingerprints[periods[j]])
                        pairSims.append(sim)

                avgSim = sum(pairSims) / len(pairSims) if pairSims else 0
                if avgSim >= 0.7:
                    compSame += 1
                else:
                    compDiff += 1
                    allDiffs.append((name, topic, avgSim))

            totalSame += compSame
            totalDiff += compDiff
            total = compSame + compDiff
            totalTopics += total
            pct = compSame / total * 100 if total else 0
            print(f"  {name}: 같은 {compSame}, 다른 {compDiff} ({total} topics, {pct:.0f}% 같음)")

        except Exception as e:
            print(f"  {name}: 오류 ({e})")

    print(f"\n  전체: 같은 {totalSame}, 다른 {totalDiff} ({totalTopics} topics)")
    samePct = totalSame / totalTopics * 100 if totalTopics else 0
    print(f"  같은 구조 비율: {samePct:.1f}%")

    if allDiffs:
        print(f"\n  다른 구조 판정 ({len(allDiffs)}개):")
        # topic별 빈도
        topicFreq: Counter = Counter()
        for _, topic, _ in allDiffs:
            topicFreq[topic] += 1
        for topic, freq in topicFreq.most_common(15):
            avgSim = sum(s for _, t, s in allDiffs if t == topic) / freq
            print(f"    - {topic}: {freq}개 종목, 평균 sim={avgSim:.3f}")


if __name__ == "__main__":
    deepDiveTopics()
    multiCompanyTest()
