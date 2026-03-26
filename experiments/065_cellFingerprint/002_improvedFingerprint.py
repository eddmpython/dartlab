"""실험 ID: 065-002
실험명: 개선된 핑거프린트 — S(특수)를 N/E로 재분류 + 열 정렬 정규화

목적:
- 001에서 발견된 문제점 개선:
  1. "-" 같은 특수문자가 S로 분류되어 숫자 열과 불일치 (실제로는 "값 없음 = 숫자 0과 동치")
  2. 컬럼 추가/삭제 시 위치 기반 비교가 깨짐
  3. 실제 데이터에서 같은 구조가 "다른 구조"로 오판되는 케이스 해결

가설:
1. "-"를 N (숫자의 placeholder)로 재분류하면 sparse 테이블 판별 개선
2. 열 타입 분포를 정렬하여 비교하면 (위치 무관) 컬럼 순서 변경에 강건
3. 열 타입 "프로필" (T열 수, N열 수, D열 수)로 비교하면 더 정확

방법:
1. classifyCell 개선: "-" → "N" (숫자 placeholder), 빈 문자열만 "E"
2. 열 프로필 비교: [T열수, N열수, D열수] 벡터 기반 유사도
3. 001에서 실패한 케이스 재검증
4. 실제 삼성전자 데이터로 재검증

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

# ── 개선된 셀 타입 분류기 ──

_NUM_RE = re.compile(
    r"^[△\-\(]?\s*[\d,]+(?:\.\d+)?\s*\)?(?:\s*%)?$"
)
_DATE_RE = re.compile(
    r"^\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2}$"
    r"|^\d{4}[.\-/]\d{1,2}$"
    r"|^\d{4}년\s*\d{1,2}월"
)
# "-", "–", "—" 같은 것은 숫자/값 placeholder (0 또는 N/A 의미)
_PLACEHOLDER_RE = re.compile(r"^[\-–—]+$")
_NOTE_RE = re.compile(r"^[※☞△▲▽▼~]")


def classifyCell(cell: str) -> str:
    """개선된 셀 타입 분류.

    N: 숫자 (1,234 / -3.5% / △500) 또는 값 placeholder (-)
    T: 텍스트
    D: 날짜
    E: 빈 셀
    """
    s = cell.strip()
    if not s:
        return "E"
    if _PLACEHOLDER_RE.match(s):
        return "N"  # "-"는 숫자 자리의 placeholder
    if _DATE_RE.match(s):
        return "D"
    if _NUM_RE.match(s):
        return "N"
    if _NOTE_RE.match(s) and len(s) <= 3:
        return "N"  # ※, △ 단독은 주석/부호 → 숫자 영역
    return "T"


def _parseMdTable(md: str) -> tuple[list[str], list[list[str]]]:
    """마크다운 테이블 → (헤더, 데이터행)."""
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
    """개선된 테이블 핑거프린트.

    핵심 개선:
    1. "-"를 N으로 분류 → sparse 테이블도 정확히 매칭
    2. 열 프로필: [T열수, N열수, D열수, E열수] 벡터
    3. 시그니처: 열별 주요 타입 (E 무시, N 우선)
    """

    def __init__(self, md: str):
        headers, rows = _parseMdTable(md)
        self.headers = headers
        self.numRows = len(rows)
        self.numCols = len(headers)

        # 열별 타입 분포
        self.colDistributions: list[Counter] = []
        self.colTypes: list[str] = []

        for ci in range(self.numCols):
            counter: Counter = Counter()
            for row in rows:
                cell = row[ci] if ci < len(row) else ""
                counter[classifyCell(cell)] += 1
            self.colDistributions.append(counter)

            # 주요 타입 결정: E 무시, 나머지 중 최빈
            nonEmpty = {k: v for k, v in counter.items() if k != "E"}
            if nonEmpty:
                self.colTypes.append(max(nonEmpty, key=lambda k: nonEmpty[k]))
            elif counter:
                self.colTypes.append("E")
            else:
                self.colTypes.append("E")

        self.signature = "".join(self.colTypes)

        # 열 프로필: 각 타입의 열 수
        typeCounts = Counter(self.colTypes)
        self.profile = {
            "T": typeCounts.get("T", 0),
            "N": typeCounts.get("N", 0),
            "D": typeCounts.get("D", 0),
            "E": typeCounts.get("E", 0),
        }

    def __repr__(self) -> str:
        return f"FP(sig={self.signature}, shape={self.numRows}x{self.numCols})"


def fingerprintSimilarity(fp1: TableFingerprint, fp2: TableFingerprint) -> float:
    """개선된 유사도 — 3가지 전략 결합.

    1. 시그니처 매칭: 정확히 같으면 1.0
    2. 열 프로필 코사인 유사도: [T열수, N열수, D열수] 벡터 비교
    3. 위치별 타입 매칭: 공통 열에서 타입 일치 비율
    """
    # 전략 1: 시그니처가 정확히 같으면 → 1.0
    if fp1.signature == fp2.signature:
        return 1.0

    # 전략 2: 열 프로필 코사인 유사도 (위치 무관)
    types = ["T", "N", "D"]
    v1 = [fp1.profile[t] for t in types]
    v2 = [fp2.profile[t] for t in types]
    dot = sum(a * b for a, b in zip(v1, v2))
    mag1 = sum(a ** 2 for a in v1) ** 0.5
    mag2 = sum(a ** 2 for a in v2) ** 0.5
    profileSim = dot / (mag1 * mag2) if (mag1 > 0 and mag2 > 0) else 0.0

    # 전략 3: 위치별 타입 매칭 (공통 열)
    minCols = min(fp1.numCols, fp2.numCols)
    maxCols = max(fp1.numCols, fp2.numCols)
    if maxCols == 0:
        return 1.0

    matchCount = 0
    for ci in range(minCols):
        if ci < len(fp1.colTypes) and ci < len(fp2.colTypes):
            if fp1.colTypes[ci] == fp2.colTypes[ci]:
                matchCount += 1

    positionSim = matchCount / maxCols

    # 최종: 프로필 유사도와 위치 유사도의 가중 평균
    return 0.4 * profileSim + 0.6 * positionSim


def test_001_failures():
    """001에서 실패한 케이스 재검증."""
    print("=" * 70)
    print("001 실패 케이스 재검증 (개선된 분류기)")
    print("=" * 70)

    # 테스트 1: 컬럼 추가 (3열→4열, "-" 값)
    t2024 = """| 구분 | 인원수 | 승인금액 |
| --- | --- | --- |
| 등기이사 | 5 | 46,500 |
| 사외이사 | 3 | - |"""

    t2025 = """| 구 분 | 인원수 | 주주총회 승인금액 | 비고 |
| --- | --- | --- | --- |
| 등기이사 | 5 | - | - |
| 사외이사 | 3 | - | - |"""

    fp1 = TableFingerprint(t2024)
    fp2 = TableFingerprint(t2025)
    sim = fingerprintSimilarity(fp1, fp2)
    print(f"\n  [테스트 1: 컬럼 추가 (3→4열)]")
    print(f"    2024: {fp1}  프로필={fp1.profile}")
    print(f"    2025: {fp2}  프로필={fp2.profile}")
    print(f"    유사도: {sim:.4f}  (001: 0.6768)")
    print(f"    판정: {'같은 구조' if sim >= 0.7 else '다른 구조'}")

    # 테스트 8: sparse vs dense
    t_dense = """| 구분 | 2024 | 2023 | 2022 |
| --- | --- | --- | --- |
| 매출액 | 100 | 90 | 80 |
| 영업이익 | 30 | 25 | 20 |"""

    t_sparse = """| 구분 | 2024 | 2023 | 2022 |
| --- | --- | --- | --- |
| 매출액 | 100 | - | - |
| 영업이익 | - | 25 | - |
| 기타 | - | - | - |"""

    fp_dense = TableFingerprint(t_dense)
    fp_sparse = TableFingerprint(t_sparse)
    sim8 = fingerprintSimilarity(fp_dense, fp_sparse)
    print(f"\n  [테스트 8: sparse vs dense]")
    print(f"    Dense: {fp_dense}  sig={fp_dense.signature}")
    print(f"    Sparse: {fp_sparse}  sig={fp_sparse.signature}")
    print(f"    유사도: {sim8:.4f}  (001: 0.4736)")
    print(f"    판정: {'같은 구조' if sim8 >= 0.7 else '다른 구조'}")

    # 보수 vs 변동 (다른 구조 — 여전히 잘 구분되는지)
    t_comp = """| 구분 | 인원수 | 보수총액 | 1인당 평균보수액 |
| --- | --- | --- | --- |
| 등기이사 | 5 | 46,500 | 9,300 |
| 사외이사 | 3 | 1,050 | 350 |"""

    t_chg = """| 변동일 | 성명 | 직위 | 변동사유 |
| --- | --- | --- | --- |
| 2024.03.15 | 홍길동 | 사내이사 | 신규선임 |
| 2024.03.15 | 김철수 | 사외이사 | 사임 |"""

    fp_comp = TableFingerprint(t_comp)
    fp_chg = TableFingerprint(t_chg)
    sim_diff = fingerprintSimilarity(fp_comp, fp_chg)
    print(f"\n  [보수 vs 변동 (다른 구조)]")
    print(f"    보수: {fp_comp}  sig={fp_comp.signature}")
    print(f"    변동: {fp_chg}  sig={fp_chg.signature}")
    print(f"    유사도: {sim_diff:.4f}  (001: 0.0000)")
    print(f"    판정: {'같은 구조' if sim_diff >= 0.7 else '다른 구조'}")


def test_real_data():
    """실제 삼성전자 데이터 — 이전에 "다른 구조"로 나온 것들 재검증."""
    print()
    print("=" * 70)
    print("실제 삼성전자 데이터 재검증")
    print("=" * 70)

    sys.path.insert(0, "C:/Users/MSI/OneDrive/Desktop/sideProject/dartlab/src")
    try:
        from dartlab import Company
        c = Company("삼성전자")
        secs = c.docs.sections
        if secs is None:
            print("  sections 로드 실패")
            return

        tableRows = secs.filter(secs["blockType"] == "table")
        periodCols = [col for col in secs.columns if re.match(r"\d{4}", col)]

        topics = tableRows["topic"].unique().to_list()
        sameCount = 0
        diffCount = 0
        results = []

        for topic in topics[:80]:
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
                for j in range(i + 1, len(periods)):
                    sim = fingerprintSimilarity(fingerprints[periods[i]], fingerprints[periods[j]])
                    pairSims.append(sim)

            avgSim = sum(pairSims) / len(pairSims) if pairSims else 0
            isSame = avgSim >= 0.7
            if isSame:
                sameCount += 1
            else:
                diffCount += 1

            results.append((topic, avgSim, isSame, len(fingerprints)))

        print(f"\n  핑거프린트 결과 (상위 80 topics):")
        print(f"    같은 구조 판정: {sameCount}")
        print(f"    다른 구조 판정: {diffCount}")

        # 다른 구조로 나온 것들 상세
        diffs = [r for r in results if not r[2]]
        if diffs:
            print(f"\n  다른 구조로 판정된 topic ({len(diffs)}개):")
            for topic, sim, _, nPeriods in diffs:
                print(f"    - {topic}: sim={sim:.3f}  ({nPeriods} periods)")

        # 001 대비 개선 확인
        print(f"\n  001 결과: 같은 31, 다른 6 (50 topics)")
        print(f"  002 결과: 같은 {sameCount}, 다른 {diffCount} (80 topics)")

        # 경계선 케이스 (0.6~0.8)
        borderline = [r for r in results if 0.6 <= r[1] < 0.8]
        if borderline:
            print(f"\n  경계선 케이스 (0.6~0.8):")
            for topic, sim, isSame, nPeriods in borderline:
                print(f"    - {topic}: sim={sim:.3f}  판정={'같음' if isSame else '다름'}  ({nPeriods} periods)")

    except Exception as e:
        print(f"  오류: {e}")
        import traceback
        traceback.print_exc()


def test_combined_strategy():
    """헤더 텍스트 + 핑거프린트 결합 전략 시뮬레이션."""
    print()
    print("=" * 70)
    print("결합 전략: 헤더 텍스트 + 핑거프린트")
    print("=" * 70)

    cases = [
        ("같은 테이블, 헤더 다름",
         "| 구분 | 인원수 | 보수총액 |\n| --- | --- | --- |\n| 등기이사 | 5 | 46,500 |",
         "| 직위 | 인원(명) | 총보수(백만원) |\n| --- | --- | --- |\n| 사내이사 | 3 | 25,000 |",
         True),
        ("같은 테이블, 컬럼 추가",
         "| 구분 | 인원수 | 보수 |\n| --- | --- | --- |\n| 등기이사 | 5 | 46,500 |",
         "| 구분 | 인원수 | 보수 | 비고 |\n| --- | --- | --- | --- |\n| 등기이사 | 5 | 46,500 | - |",
         True),
        ("다른 테이블, 같은 컬럼수",
         "| 구분 | 인원수 | 보수총액 |\n| --- | --- | --- |\n| 등기이사 | 5 | 46,500 |",
         "| 변동일 | 성명 | 변동사유 |\n| --- | --- | --- |\n| 2024.03.15 | 홍길동 | 신규선임 |",
         False),
        ("다른 테이블, 같은 헤더",
         "| 구분 | 내용 | 비고 |\n| --- | --- | --- |\n| 매출 | 100,000 | 증가 |",
         "| 구분 | 내용 | 비고 |\n| --- | --- | --- |\n| 사업 | 반도체 | 정관 |",
         False),
    ]

    sys.path.insert(0, "C:/Users/MSI/OneDrive/Desktop/sideProject/dartlab/src")
    from dartlab.providers.dart.docs.sections.tableParser import _normalizeHeader

    print("\n  결합 판별 규칙:")
    print("    헤더 매칭 AND 핑거프린트 ≥ 0.5 → 같은 구조")
    print("    헤더 미매칭 BUT 핑거프린트 ≥ 0.8 → 같은 구조 (보완)")
    print("    핑거프린트 < 0.5 → 다른 구조 (거부)")

    correct = 0
    for label, md1, md2, expected in cases:
        fp1 = TableFingerprint(md1)
        fp2 = TableFingerprint(md2)
        fpSim = fingerprintSimilarity(fp1, fp2)

        h1 = _normalizeHeader(fp1.headers)
        h2 = _normalizeHeader(fp2.headers)
        headerMatch = h1 == h2

        # 결합 판별
        if headerMatch and fpSim >= 0.5:
            predicted = True
        elif not headerMatch and fpSim >= 0.8:
            predicted = True
        elif fpSim < 0.5:
            predicted = False
        else:
            predicted = headerMatch  # 애매한 경우 헤더 우선

        isCorrect = predicted == expected
        correct += isCorrect

        print(f"\n  [{label}]")
        print(f"    헤더매칭={headerMatch}, 핑거프린트={fpSim:.3f}")
        print(f"    판정={predicted}, 정답={expected}, {'정확' if isCorrect else '오류'}")

    print(f"\n  정확도: {correct}/{len(cases)} ({correct/len(cases)*100:.0f}%)")


if __name__ == "__main__":
    test_001_failures()
    test_real_data()
    test_combined_strategy()
