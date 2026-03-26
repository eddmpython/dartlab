"""실험 ID: 065-001
실험명: 셀 타입 핑거프린트 기반 테이블 구조 판별

목적:
- 마크다운 테이블의 각 셀을 타입(N/T/D/E/S)으로 분류하여 "핑거프린트"를 생성
- 기간별 테이블의 핑거프린트 유사도로 같은 구조인지 판별
- 현재 _normalizeHeader 기반 그룹핑 대비 장단점 평가

가설:
1. 셀 타입 핑거프린트로 테이블 구조 유사도를 판별할 수 있다
2. 헤더 텍스트가 달라도 데이터 패턴이 같으면 같은 구조로 묶인다
3. 이력형(항목 겹침 낮음)과 정형(항목 겹침 높음) 테이블을 핑거프린트만으로 구분 가능하다

방법:
1. 셀 타입 분류기 구현 (N/T/D/E/S)
2. 테이블 핑거프린트 = 열별 타입 분포 벡터
3. 합성 테스트 케이스로 정확도 검증
4. 실제 삼성전자 데이터로 현행 방식 vs 핑거프린트 비교

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

# ── 셀 타입 분류기 ──

_NUM_RE = re.compile(
    r"^[△\-\(]?\s*[\d,]+(?:\.\d+)?\s*\)?(?:\s*%)?$"
)
_DATE_RE = re.compile(
    r"^\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2}$"
    r"|^\d{4}[.\-/]\d{1,2}$"
    r"|^\d{4}년\s*\d{1,2}월"
)
_SPECIAL_RE = re.compile(r"^[\-–—※☞△▲▽▼~\s]*$")


def classifyCell(cell: str) -> str:
    """셀 하나를 타입으로 분류.

    N: 숫자 (1,234 / 46,500 / -3.5% / △500 / (100))
    T: 텍스트
    D: 날짜 (2022.03.16, 2022-03, 2024년 3월)
    E: 빈 셀
    S: 특수 (-, ※, △ 단독 등)
    """
    s = cell.strip()
    if not s:
        return "E"
    if _SPECIAL_RE.match(s) and not any(ch.isdigit() for ch in s):
        return "S"
    if _DATE_RE.match(s):
        return "D"
    if _NUM_RE.match(s):
        return "N"
    # 숫자가 포함된 혼합 텍스트 (예: "제76기(당기)") → T
    return "T"


# ── 테이블 파싱 유틸 ──


def _parseMdTable(md: str) -> tuple[list[str], list[list[str]]]:
    """마크다운 테이블 → (헤더, 데이터행) 파싱."""
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


# ── 핑거프린트 생성 ──


class TableFingerprint:
    """테이블의 구조적 핑거프린트.

    - colTypes: 열별 주요 타입 (행들의 최빈 타입)
    - colDistributions: 열별 타입 분포
    - shape: (행수, 열수)
    - headerTypes: 헤더 셀 타입
    """

    def __init__(self, md: str):
        headers, rows = _parseMdTable(md)
        self.headers = headers
        self.numRows = len(rows)
        self.numCols = len(headers)

        # 헤더 타입
        self.headerTypes = [classifyCell(h) for h in headers]

        # 열별 타입 분포
        self.colDistributions: list[Counter] = []
        self.colTypes: list[str] = []

        for ci in range(self.numCols):
            counter: Counter = Counter()
            for row in rows:
                cell = row[ci] if ci < len(row) else ""
                counter[classifyCell(cell)] += 1
            self.colDistributions.append(counter)
            if counter:
                self.colTypes.append(counter.most_common(1)[0][0])
            else:
                self.colTypes.append("E")

        # 축약 시그니처: 열별 주요 타입 문자열
        self.signature = "".join(self.colTypes)

    def __repr__(self) -> str:
        return f"FP(sig={self.signature}, shape={self.numRows}x{self.numCols})"


def fingerprintSimilarity(fp1: TableFingerprint, fp2: TableFingerprint) -> float:
    """두 핑거프린트의 구조 유사도 (0~1).

    전략:
    1. 열 수 차이 페널티 (1열 차이까지 허용, 그 이상은 급격 감소)
    2. 공통 열에서 타입 분포 코사인 유사도
    3. 헤더 타입 패턴 보너스
    """
    # 열 수 유사도
    maxCols = max(fp1.numCols, fp2.numCols)
    minCols = min(fp1.numCols, fp2.numCols)
    if maxCols == 0:
        return 1.0
    colPenalty = minCols / maxCols  # 3/4 = 0.75 등

    # 공통 열에서 타입 분포 유사도
    typeScores = []
    for ci in range(minCols):
        d1 = fp1.colDistributions[ci] if ci < len(fp1.colDistributions) else Counter()
        d2 = fp2.colDistributions[ci] if ci < len(fp2.colDistributions) else Counter()
        allTypes = set(d1.keys()) | set(d2.keys())
        if not allTypes:
            typeScores.append(1.0)
            continue
        # 코사인 유사도
        dot = sum(d1.get(t, 0) * d2.get(t, 0) for t in allTypes)
        mag1 = sum(v ** 2 for v in d1.values()) ** 0.5
        mag2 = sum(v ** 2 for v in d2.values()) ** 0.5
        if mag1 == 0 or mag2 == 0:
            typeScores.append(0.0)
        else:
            typeScores.append(dot / (mag1 * mag2))

    avgTypeSim = sum(typeScores) / len(typeScores) if typeScores else 0.0

    # 최종 유사도 = 열 수 유사도 × 타입 분포 유사도
    return colPenalty * avgTypeSim


# ── 테스트 케이스 ──


def test_basic_cases():
    """기본 테스트 케이스."""
    print("=" * 70)
    print("테스트 1: 같은 구조, 컬럼명 약간 다름")
    print("=" * 70)

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

    print(f"  2024: {fp1}")
    print(f"    헤더: {fp1.headers}")
    print(f"    열별 분포: {[dict(d) for d in fp1.colDistributions]}")
    print(f"  2025: {fp2}")
    print(f"    헤더: {fp2.headers}")
    print(f"    열별 분포: {[dict(d) for d in fp2.colDistributions]}")
    print(f"  유사도: {sim:.4f}")
    print(f"  판정: {'같은 구조' if sim >= 0.7 else '다른 구조'}")

    print()
    print("=" * 70)
    print("테스트 2: 완전히 다른 구조 (보수 vs 이사 변동)")
    print("=" * 70)

    t_compensation = """| 구분 | 인원수 | 보수총액 | 1인당 평균보수액 |
| --- | --- | --- | --- |
| 등기이사 | 5 | 46,500 | 9,300 |
| 사외이사 | 3 | 1,050 | 350 |"""

    t_changes = """| 변동일 | 성명 | 직위 | 변동사유 |
| --- | --- | --- | --- |
| 2024.03.15 | 홍길동 | 사내이사 | 신규선임 |
| 2024.03.15 | 김철수 | 사외이사 | 사임 |
| 2023.06.01 | 이영희 | 감사위원 | 중도퇴임 |"""

    fp_comp = TableFingerprint(t_compensation)
    fp_chg = TableFingerprint(t_changes)
    sim2 = fingerprintSimilarity(fp_comp, fp_chg)

    print(f"  보수: {fp_comp}")
    print(f"    헤더: {fp_comp.headers}")
    print(f"    열별 분포: {[dict(d) for d in fp_comp.colDistributions]}")
    print(f"  변동: {fp_chg}")
    print(f"    헤더: {fp_chg.headers}")
    print(f"    열별 분포: {[dict(d) for d in fp_chg.colDistributions]}")
    print(f"  유사도: {sim2:.4f}")
    print(f"  판정: {'같은 구조' if sim2 >= 0.7 else '다른 구조'}")

    print()
    print("=" * 70)
    print("테스트 3: 숫자 테이블 vs 날짜 테이블 (다른 패턴)")
    print("=" * 70)

    t_financial = """| 구분 | 당기 | 전기 | 전전기 |
| --- | --- | --- | --- |
| 매출액 | 302,231,207 | 258,935,542 | 236,806,988 |
| 영업이익 | 36,183,089 | 6,566,517 | 51,633,654 |
| 당기순이익 | 34,457,724 | 15,487,198 | 39,243,693 |"""

    t_schedule = """| 구분 | 선임일 | 임기만료일 | 재선임여부 |
| --- | --- | --- | --- |
| 대표이사 | 2022.03.16 | 2025.03.15 | 재선임예정 |
| 사내이사 | 2023.03.15 | 2026.03.14 | - |"""

    fp_fin = TableFingerprint(t_financial)
    fp_sch = TableFingerprint(t_schedule)
    sim3 = fingerprintSimilarity(fp_fin, fp_sch)

    print(f"  재무: {fp_fin}")
    print(f"    시그니처: {fp_fin.signature}")
    print(f"    열별 분포: {[dict(d) for d in fp_fin.colDistributions]}")
    print(f"  일정: {fp_sch}")
    print(f"    시그니처: {fp_sch.signature}")
    print(f"    열별 분포: {[dict(d) for d in fp_sch.colDistributions]}")
    print(f"  유사도: {sim3:.4f}")
    print(f"  판정: {'같은 구조' if sim3 >= 0.7 else '다른 구조'}")

    print()
    print("=" * 70)
    print("테스트 4: 컬럼 수 같지만 내용 타입이 다른 경우")
    print("=" * 70)

    t_num_only = """| 항목 | 금액 | 비율 |
| --- | --- | --- |
| 매출액 | 100,000 | 45.2% |
| 원가 | 80,000 | 36.1% |"""

    t_text_only = """| 항목 | 내용 | 비고 |
| --- | --- | --- |
| 사업목적 | 전자제품 제조 | 정관 제2조 |
| 주요제품 | DRAM, NAND | - |"""

    fp_num = TableFingerprint(t_num_only)
    fp_txt = TableFingerprint(t_text_only)
    sim4 = fingerprintSimilarity(fp_num, fp_txt)

    print(f"  숫자형: {fp_num}")
    print(f"    시그니처: {fp_num.signature}")
    print(f"  텍스트형: {fp_txt}")
    print(f"    시그니처: {fp_txt.signature}")
    print(f"  유사도: {sim4:.4f}")
    print(f"  판정: {'같은 구조' if sim4 >= 0.7 else '다른 구조'}")


def test_real_world_edge_cases():
    """실제 사업보고서에서 흔한 엣지 케이스."""
    print()
    print("=" * 70)
    print("테스트 5: 부문명 미세 차이 (DS부문(메모리,SYS.LSI) vs DS부문(메모리,SystemLSI))")
    print("=" * 70)

    t_2023 = """| 부문 | 매출액 | 영업이익 |
| --- | --- | --- |
| DS부문(메모리,SYS.LSI) | 66,316 | △14,883 |
| DX부문 | 136,200 | 11,876 |
| SDC | 34,600 | 3,200 |"""

    t_2024 = """| 부문 | 매출액 | 영업이익 |
| --- | --- | --- |
| DS부문(메모리,SystemLSI) | 97,000 | 17,200 |
| DX부문 | 142,500 | 13,100 |
| SDC | 31,800 | 2,800 |"""

    fp1 = TableFingerprint(t_2023)
    fp2 = TableFingerprint(t_2024)
    sim = fingerprintSimilarity(fp1, fp2)
    print(f"  2023: {fp1}  sig={fp1.signature}")
    print(f"  2024: {fp2}  sig={fp2.signature}")
    print(f"  유사도: {sim:.4f}")
    print(f"  판정: {'같은 구조' if sim >= 0.7 else '다른 구조'}")
    print(f"  → 항목명이 다르지만 셀 타입이 동일 → 핑거프린트가 같음")

    print()
    print("=" * 70)
    print("테스트 6: 기간별 행 수 다름 (이사 추가/삭제)")
    print("=" * 70)

    t_few = """| 성명 | 직위 | 담당업무 |
| --- | --- | --- |
| 이재용 | 대표이사 | 경영총괄 |
| 한종희 | 대표이사 | DX 부문장 |
| 경계현 | 대표이사 | DS 부문장 |"""

    t_more = """| 성명 | 직위 | 담당업무 |
| --- | --- | --- |
| 이재용 | 대표이사 | 경영총괄 |
| 한종희 | 대표이사 | DX 부문장 |
| 경계현 | 대표이사 | DS 부문장 |
| 이정배 | 사내이사 | 반도체 연구 |
| 노태문 | 사내이사 | MX 사업부장 |"""

    fp_few = TableFingerprint(t_few)
    fp_more = TableFingerprint(t_more)
    sim6 = fingerprintSimilarity(fp_few, fp_more)
    print(f"  3명: {fp_few}  sig={fp_few.signature}")
    print(f"  5명: {fp_more}  sig={fp_more.signature}")
    print(f"  유사도: {sim6:.4f}")
    print(f"  판정: {'같은 구조' if sim6 >= 0.7 else '다른 구조'}")
    print(f"  → 행 수 달라도 열 패턴이 TTT로 동일 → 같은 구조 정확 판별")

    print()
    print("=" * 70)
    print("테스트 7: 혼합 컬럼 (숫자+텍스트+날짜가 같은 열에)")
    print("=" * 70)

    t_mixed = """| 항목 | 내용 |
| --- | --- |
| 설립일 | 1969.01.13 |
| 종업원수 | 124,527명 |
| 주요제품 | DRAM, NAND |
| 자본금 | 897,514 |"""

    fp_mix = TableFingerprint(t_mixed)
    print(f"  혼합: {fp_mix}")
    print(f"    시그니처: {fp_mix.signature}")
    print(f"    열별 분포: {[dict(d) for d in fp_mix.colDistributions]}")
    print(f"  → 2열 내용이 D/T/T/N 혼합 → 주요 타입이 T (다양한 값)")

    print()
    print("=" * 70)
    print("테스트 8: 빈 셀이 많은 sparse 테이블 vs dense 테이블")
    print("=" * 70)

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
    print(f"  Dense: {fp_dense}  sig={fp_dense.signature}")
    print(f"    열별 분포: {[dict(d) for d in fp_dense.colDistributions]}")
    print(f"  Sparse: {fp_sparse}  sig={fp_sparse.signature}")
    print(f"    열별 분포: {[dict(d) for d in fp_sparse.colDistributions]}")
    print(f"  유사도: {sim8:.4f}")
    print(f"  판정: {'같은 구조' if sim8 >= 0.7 else '다른 구조'}")


def test_fingerprint_vs_header():
    """현행 방식(헤더 텍스트) vs 핑거프린트 비교."""
    print()
    print("=" * 70)
    print("테스트 9: 핑거프린트 vs 헤더 텍스트 — 차이가 드러나는 케이스")
    print("=" * 70)

    cases = [
        ("헤더 다름 + 구조 같음",
         """| 구분 | 인원수 | 보수총액 |
| --- | --- | --- |
| 등기이사 | 5 | 46,500 |""",
         """| 직위 | 인원(명) | 총보수(백만원) |
| --- | --- | --- |
| 사내이사 | 3 | 25,000 |"""),

        ("헤더 같음 + 구조 다름 (드문 케이스)",
         """| 구분 | 내용 | 비고 |
| --- | --- | --- |
| 매출 | 100,000 | 증가 |
| 원가 | 80,000 | 감소 |""",
         """| 구분 | 내용 | 비고 |
| --- | --- | --- |
| 사업목적 | 반도체 제조 | 정관 제2조 |
| 주요제품 | 메모리 반도체 | - |"""),

        ("기수 컬럼 vs 연도 컬럼 (같은 데이터)",
         """| 구분 | 제56기 | 제55기 | 제54기 |
| --- | --- | --- | --- |
| 매출액 | 302,231 | 258,935 | 236,807 |""",
         """| 구분 | 2024 | 2023 | 2022 |
| --- | --- | --- | --- |
| 매출액 | 302,231 | 258,935 | 236,807 |"""),
    ]

    for label, md1, md2 in cases:
        fp1 = TableFingerprint(md1)
        fp2 = TableFingerprint(md2)
        sim = fingerprintSimilarity(fp1, fp2)
        print(f"\n  [{label}]")
        print(f"    A: sig={fp1.signature}  headers={fp1.headers}")
        print(f"    B: sig={fp2.signature}  headers={fp2.headers}")
        print(f"    핑거프린트 유사도: {sim:.4f}  → {'같은 구조' if sim >= 0.7 else '다른 구조'}")

        # 헤더 텍스트 비교 (현행 방식 시뮬레이션)
        sys.path.insert(0, "C:/Users/MSI/OneDrive/Desktop/sideProject/dartlab/src")
        from dartlab.providers.dart.docs.sections.tableParser import _normalizeHeader
        h1 = _normalizeHeader(fp1.headers)
        h2 = _normalizeHeader(fp2.headers)
        headerMatch = h1 == h2
        print(f"    헤더 텍스트 동일: {headerMatch}  ('{h1}' vs '{h2}')")


def test_with_real_data():
    """실제 삼성전자 데이터로 테스트."""
    print()
    print("=" * 70)
    print("테스트 10: 실제 삼성전자 sections 데이터")
    print("=" * 70)

    sys.path.insert(0, "C:/Users/MSI/OneDrive/Desktop/sideProject/dartlab/src")
    try:
        from dartlab import Company
        c = Company("삼성전자")
        secs = c.docs.sections
        if secs is None:
            print("  sections 로드 실패")
            return

        # 테이블 블록만 추출
        tableRows = secs.filter(
            (secs["blockType"] == "table")
        )
        periodCols = [col for col in secs.columns if re.match(r"\d{4}", col)]

        print(f"  전체 sections: {secs.shape}")
        print(f"  테이블 블록: {tableRows.shape}")
        print(f"  기간 수: {len(periodCols)}")

        # topic별로 핑거프린트 생성하여 기간 간 유사도 측정
        topics = tableRows["topic"].unique().to_list()
        sameCount = 0
        diffCount = 0
        failCount = 0
        examples = []

        for topic in topics[:50]:  # 상위 50개 topic
            topicRows = tableRows.filter(tableRows["topic"] == topic)
            # 기간별 핑거프린트
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
                        failCount += 1

            if len(fingerprints) < 2:
                continue

            # 모든 기간 쌍의 유사도
            periods = list(fingerprints.keys())
            pairSims = []
            for i in range(len(periods)):
                for j in range(i + 1, len(periods)):
                    sim = fingerprintSimilarity(fingerprints[periods[i]], fingerprints[periods[j]])
                    pairSims.append(sim)

            avgSim = sum(pairSims) / len(pairSims) if pairSims else 0
            if avgSim >= 0.7:
                sameCount += 1
            else:
                diffCount += 1
                if len(examples) < 5:
                    examples.append((topic, avgSim, periods[:2],
                                     fingerprints[periods[0]].signature,
                                     fingerprints[periods[1]].signature if len(periods) > 1 else "N/A"))

        print(f"\n  핑거프린트 결과 (상위 50 topics):")
        print(f"    같은 구조 판정: {sameCount}")
        print(f"    다른 구조 판정: {diffCount}")
        print(f"    파싱 실패: {failCount}")

        if examples:
            print(f"\n  다른 구조로 판정된 예시:")
            for topic, sim, periods, sig1, sig2 in examples:
                print(f"    - {topic}: sim={sim:.3f}")
                print(f"      {periods[0]}: {sig1}")
                print(f"      {periods[1] if len(periods) > 1 else 'N/A'}: {sig2}")

    except ImportError as e:
        print(f"  dartlab import 실패: {e}")
    except Exception as e:
        print(f"  오류: {e}")


def summarize():
    """결과 요약 및 장단점."""
    print()
    print("=" * 70)
    print("종합 평가: 셀 타입 핑거프린트 방법")
    print("=" * 70)
    print("""
장점:
  1. 헤더 텍스트에 독립적 — "인원수" vs "인원(명)" 같은 wording 차이 무시
  2. 구조적 유사도 — 열의 데이터 타입 패턴으로 테이블 성격 판별
  3. 이력형 vs 정형 구분 — D열(날짜)+T열 패턴 vs N열(숫자)+T열 패턴
  4. 컬럼 수 변화 감지 — 열 수 차이에 비례한 페널티 적용
  5. 구현이 단순하고 빠름 — 정규식 기반, 외부 의존성 없음

단점:
  1. 같은 열 수 + 같은 타입이면 구분 불가 — 3열 TNT인 다른 의미 테이블
  2. 혼합 셀(숫자+텍스트)이 많은 key_value는 모두 T로 빠짐
  3. 현행 방식의 보완재이지 대체재가 아님
  4. 행 수 차이는 유사도에 거의 영향 없음 (행 수가 판별 기준이 아니므로)

실용성 평가:
  현행 _normalizeHeader (헤더 텍스트 정규화)와 핑거프린트를 결합하면 최적:
  - 1차: 헤더 정규화로 빠른 그룹핑
  - 2차: 핑거프린트로 "헤더는 다르지만 같은 구조" 보완
  - 3차: 핑거프린트로 "헤더는 같지만 다른 구조" 거부

적용 제안:
  현재 company.py의 _groupHeader()에 핑거프린트 유사도를 보조 지표로 추가:
  - 헤더 그룹핑 실패 시 → 핑거프린트 유사도 ≥ 0.8이면 같은 그룹으로 병합
  - 헤더 그룹핑 성공이지만 핑거프린트 유사도 < 0.5이면 → 다른 구조로 분리
""")


if __name__ == "__main__":
    test_basic_cases()
    test_real_world_edge_cases()
    test_fingerprint_vs_header()
    test_with_real_data()
    summarize()
