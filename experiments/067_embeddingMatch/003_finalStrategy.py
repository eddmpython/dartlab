"""
실험 ID: 067-003
실험명: 최종 전략 — 구조 분해 매칭 (임베딩 없이)

목적:
- 001/002 결과 종합: 임베딩 단독으로는 분리 불가 (gap < 0), 정규화만으로는 커버리지 부족
- 핵심 통찰: 항목명의 구조를 분해하면 임베딩 없이도 정확한 매칭 가능
- 속도 제약: 283종목 × 200항목 임베딩 = 38분 → 실용 불가
- 목표: 정규화 + 구조 분해만으로 Precision 100%, Recall 90%+ 달성

가설:
1. 항목명은 [core] + [qualifier] + [annotation] 구조로 분해 가능
2. core만 비교하면 "매출액(주22)" = "매출액", "(연결)당기순이익(백만원)" = "당기순이익"
3. qualifier 비교로 "(연결)" ≠ "(별도)", "사내" ≠ "사외" 구분
4. 특수 패턴 룰로 "영업이익(손실)" = "영업이익" 흡수

방법:
1. 항목명을 core/qualifier/annotation으로 파싱
2. 매칭 규칙: core 동일 + qualifier 호환 → 매칭
3. 전체 테스트 쌍으로 검증
4. 실제 sections 데이터에서 미매칭 항목 통계

결과 (실험 후 작성):

결론:

실험일: 2026-03-18
"""

import re
from dataclasses import dataclass

# ── 항목명 구조 분해 ──

# 제거할 annotation 패턴 (매칭에 무관)
_ANNOTATION_RE = re.compile(
    r'\(주석?\d+\)'               # (주1), (주22), (주석3)
    r'|\((?:백만|천|억)?원\)'       # (원), (백만원), (천원), (억원)
    r'|\(%\)'                     # (%)
    r'|\(천주\)'                   # (천주)
    r'|\(주\)'                     # (주)
)

# 기수/기간 접미사 (매칭 시 무시)
_PERIOD_SUFFIX_RE = re.compile(
    r'[_\s]*(?:당기|전기|전전기|제\d+기)$'
    r'|[_\s]*(?:당기|전기|전전기|제\d+기)\b'
)

# 의미적으로 동일한 괄호 내용 (흡수 가능)
_ABSORB_QUALIFIERS = {
    '손실',            # 영업이익(손실) = 영업이익
    '이익',            # 영업이익(이익) = 영업이익
    '차입금',
}

# 구분해야 하는 qualifier
_DISTINCT_QUALIFIERS = {
    '연결', '별도',     # (연결) ≠ (별도)
    '보통주', '우선주',  # 보통주 ≠ 우선주
}

# 선행 접두사 (매칭 시 제거하되, 구분이 필요한 것은 qualifier로)
_PREFIX_RE = re.compile(r'^[\(（](연결|별도|개별)[\)）]')


@dataclass
class ParsedItem:
    """분해된 항목명"""
    original: str
    core: str           # 핵심 의미 (비교 대상)
    qualifiers: list    # 구분 qualifier [(연결), (사외이사) 등]
    absorbed: list      # 흡수된 qualifier [(손실) 등]
    annotations: list   # 제거된 annotation [(주22), (백만원) 등]


def parse_item(text: str) -> ParsedItem:
    """항목명을 구조 분해"""
    s = text.strip()
    original = s

    # 1. 선행 접두사 추출: (연결), (별도) 등
    qualifiers = []
    prefix_m = _PREFIX_RE.match(s)
    if prefix_m:
        qualifiers.append(prefix_m.group(1))
        s = s[prefix_m.end():]

    # 2. annotation 추출 및 제거
    annotations = _ANNOTATION_RE.findall(s)
    s = _ANNOTATION_RE.sub('', s)

    # 3. 기수/기간 접미사 제거
    s = _PERIOD_SUFFIX_RE.sub('', s)

    # 4. 괄호 내용을 qualifier로 분해
    absorbed = []

    def process_paren(m):
        content = m.group(1).strip()
        # 쉼표 구분된 복합 qualifier
        parts = [p.strip() for p in content.split(',')]
        for part in parts:
            if part in _ABSORB_QUALIFIERS:
                absorbed.append(part)
            else:
                qualifiers.append(part)
        return ''

    s = re.sub(r'\(([^)]+)\)', process_paren, s)

    # 5. core 정리
    core = re.sub(r'\s+', '', s).strip()
    # 빈 괄호 제거
    core = re.sub(r'[\(（][\s]*[\)）]', '', core)

    return ParsedItem(
        original=original,
        core=core,
        qualifiers=sorted(qualifiers),
        absorbed=absorbed,
        annotations=annotations,
    )


def items_match(a: str, b: str) -> tuple[bool, str]:
    """두 항목명이 같은 항목인지 판단

    Returns:
        (매칭여부, 판단근거)
    """
    pa, pb = parse_item(a), parse_item(b)

    # Rule 1: core 동일 + qualifier 호환
    if pa.core == pb.core:
        # qualifier가 모두 같으면 매칭
        if pa.qualifiers == pb.qualifiers:
            return True, f"core='{pa.core}' exact, qualifiers={pa.qualifiers}"

        # qualifier가 다르면 → distinct qualifier 포함 여부 확인
        qa_set, qb_set = set(pa.qualifiers), set(pb.qualifiers)
        diff = qa_set.symmetric_difference(qb_set)

        # distinct qualifier가 다르면 비매칭
        for d in diff:
            if d in _DISTINCT_QUALIFIERS:
                return False, f"core='{pa.core}' same but distinct qualifier differs: {diff}"

        # 나머지 qualifier 차이는 흡수
        return True, f"core='{pa.core}' same, qualifier diff absorbed: {diff}"

    # Rule 2: 한쪽 core가 다른 쪽 core를 포함 (접두사/접미사 차이)
    if len(pa.core) >= 2 and len(pb.core) >= 2:
        if pa.core in pb.core or pb.core in pa.core:
            shorter = pa if len(pa.core) <= len(pb.core) else pb
            longer = pb if len(pa.core) <= len(pb.core) else pa
            extra = longer.core.replace(shorter.core, '', 1)
            # "1주당" vs "주당" → 숫자 접두사 차이
            if re.match(r'^\d+$', extra):
                return True, f"numeric prefix: '{shorter.core}' ⊂ '{longer.core}'"
            # 포함 관계: 짧은 쪽이 긴 쪽의 80% 이상이어야 매칭
            # (기본주당이익 vs 주당이익 = 4/6 = 67% → 거부)
            ratio = len(shorter.core) / len(longer.core)
            if ratio >= 0.80 and len(shorter.core) >= 3:
                return True, f"substring({ratio:.0%}): '{shorter.core}' ⊂ '{longer.core}'"

    # Rule 3: 괄호 내용 정렬 후 비교 (SYS.LSI vs SystemLSI 등)
    #   core를 소문자 + 특수문자 제거 후 비교
    def normalize_core(c):
        c = c.lower()
        c = re.sub(r'[.\s_\-]', '', c)
        return c

    if normalize_core(pa.core) == normalize_core(pb.core):
        return True, f"normalized core match: '{pa.core}' ≈ '{pb.core}'"

    # Rule 4: qualifier를 core에 합산한 full form 비교
    def full_form(p):
        parts = [p.core] + p.qualifiers
        return normalize_core(''.join(parts))

    if full_form(pa) == full_form(pb):
        return True, f"full form match"

    # Rule 5: core의 fuzzy 유사도 (높은 threshold)
    from difflib import SequenceMatcher
    core_ratio = SequenceMatcher(None, pa.core, pb.core).ratio()
    if core_ratio >= 0.90:
        return True, f"core fuzzy={core_ratio:.3f}: '{pa.core}' ≈ '{pb.core}'"

    return False, f"no match: core='{pa.core}' vs '{pb.core}'"


# ── 테스트 ──

items = [
    "DS부문(메모리,SYS.LSI)",            # 0
    "DS부문(메모리,SystemLSI)",           # 1
    "사내이사",                            # 2
    "사외이사",                            # 3
    "등기이사(사외이사,감사위원회위원제외)",  # 4
    "등기이사(사외이사,감사위원회제외)",      # 5
    "매출액",                              # 6
    "매출액(주22)",                        # 7
    "당기순이익",                           # 8
    "전기순이익",                           # 9
    "(연결)당기순이익(백만원)",              # 10
    "(별도)당기순이익(백만원)",              # 11
    "주당액면가액(원)_당기",                # 12
    "주당액면가액(원)_전기",                # 13
    "보통주",                              # 14
    "보통주(주1)",                          # 15
    "우선주",                              # 16
    "1주당 배당금(원)",                     # 17
    "주당 배당금(원)",                      # 18
    "현금배당수익률(%)",                    # 19
    "현금배당성향(%)",                      # 20
    "영업이익",                             # 21
    "영업이익(손실)",                       # 22
    "자본총계",                             # 23
    "자본금",                              # 24
    # 추가 hard case
    "DS부문(메모리, Sys. LSI)",            # 25 — 공백/대소문자 변형
    "매출원가",                             # 26
    "매출총이익",                           # 27
    "법인세비용차감전순이익",                 # 28
    "법인세비용차감전계속사업이익",            # 29
    "기본주당이익(원)",                      # 30
    "기본주당순이익(원)",                    # 31
    "주당이익(원)",                         # 32
]

positive_pairs = [
    (0, 1, "DS부문 약어 (SYS.LSI vs SystemLSI)"),
    (0, 25, "DS부문 공백/대소문자 변형"),
    (4, 5, "감사위원회 미세표현"),
    (6, 7, "주석번호 유무"),
    (8, 10, "당기순이익 ≈ (연결)당기순이익"),
    (12, 13, "주당액면가액 당기/전기"),
    (14, 15, "보통주 ≈ 보통주(주1)"),
    (17, 18, "1주당 ≈ 주당 배당금"),
    (21, 22, "영업이익 ≈ 영업이익(손실)"),
    (30, 31, "기본주당이익 ≈ 기본주당순이익"),
]

negative_pairs = [
    (2, 3, "사내이사 vs 사외이사"),
    (8, 9, "당기순이익 vs 전기순이익"),
    (10, 11, "(연결) vs (별도) 당기순이익"),
    (14, 16, "보통주 vs 우선주"),
    (19, 20, "현금배당수익률 vs 현금배당성향"),
    (23, 24, "자본총계 vs 자본금"),
    (6, 8, "매출액 vs 당기순이익"),
    (26, 27, "매출원가 vs 매출총이익"),
    (28, 29, "법인세비용차감전 순이익 vs 계속사업이익"),
    (6, 26, "매출액 vs 매출원가"),
    (30, 32, "기본주당이익 vs 주당이익"),
]


def run_test():
    print("="*90)
    print("  실험 067-003: 구조 분해 매칭 (임베딩 없이)")
    print("="*90)

    # 파싱 결과 표시
    print("\n── 구조 분해 결과 ──")
    for i, item in enumerate(items):
        p = parse_item(item)
        print(f"  [{i:2d}] {item:42s} → core='{p.core}' qual={p.qualifiers} abs={p.absorbed} ann={p.annotations}")

    # 매칭 테스트
    tp, fp, fn, tn = 0, 0, 0, 0
    errors = []

    print(f"\n── Positive 쌍 (매칭해야 함) ──")
    for i, j, desc in positive_pairs:
        matched, reason = items_match(items[i], items[j])
        if matched:
            tp += 1
            print(f"  ✓ TP  [{i:2d}]×[{j:2d}]  {desc}")
        else:
            fn += 1
            errors.append(('FN', i, j, desc, reason))
            print(f"  ✗ FN  [{i:2d}]×[{j:2d}]  {desc}")
        print(f"         reason: {reason}")

    print(f"\n── Negative 쌍 (매칭하면 안 됨) ──")
    for i, j, desc in negative_pairs:
        matched, reason = items_match(items[i], items[j])
        if not matched:
            tn += 1
            print(f"  ✓ TN  [{i:2d}]×[{j:2d}]  {desc}")
        else:
            fp += 1
            errors.append(('FP', i, j, desc, reason))
            print(f"  ✗ FP  [{i:2d}]×[{j:2d}]  {desc}")
        print(f"         reason: {reason}")

    # 결과 요약
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    accuracy = (tp + tn) / (tp + fp + fn + tn)

    print(f"\n{'='*90}")
    print(f"  결과 요약")
    print(f"{'='*90}")
    print(f"  TP={tp}  FP={fp}  FN={fn}  TN={tn}")
    print(f"  Precision: {precision:.2%}")
    print(f"  Recall:    {recall:.2%}")
    print(f"  F1:        {f1:.2%}")
    print(f"  Accuracy:  {accuracy:.2%}")

    if errors:
        print(f"\n── 오류 케이스 ──")
        for typ, i, j, desc, reason in errors:
            print(f"  {typ}: [{i}]×[{j}] {desc}")
            print(f"    → {reason}")

    # 속도
    import time
    fake_items = [f"테스트항목{i}(백만원)" for i in range(200)]
    t0 = time.time()
    count = 0
    for a in fake_items:
        for b in fake_items:
            items_match(a, b)
            count += 1
    elapsed = time.time() - t0
    print(f"\n── 속도 벤치마크 ──")
    print(f"  200×200 = {count} 쌍: {elapsed:.3f}초 ({elapsed/count*1e6:.1f}μs/쌍)")
    print(f"  283종목 × 200항목 추정: {283 * elapsed:.1f}초 ({283 * elapsed / 60:.1f}분)")
    print(f"  (cf. 임베딩: 38분)")

    # 비교 요약
    print(f"\n{'='*90}")
    print(f"  방법별 비교 요약")
    print(f"{'='*90}")
    print(f"  {'방법':30s} {'Precision':>10s} {'Recall':>10s} {'F1':>10s} {'속도':>15s}")
    print(f"  {'-'*75}")
    print(f"  {'Fuzzy (SequenceMatcher)':30s} {'N/A':>10s} {'N/A':>10s} {'N/A':>10s} {'< 1초':>15s}")
    print(f"  {'임베딩 (ko-sroberta)':30s} {'N/A':>10s} {'N/A':>10s} {'N/A':>10s} {'~38분':>15s}")
    print(f"  {'정규화 + 포함 매칭 (002)':30s} {'100%':>10s} {'78%':>10s} {'88%':>10s} {'< 1초':>15s}")
    print(f"  {'구조 분해 매칭 (003, 이것)':30s} {precision:>10.0%} {recall:>10.0%} {f1:>10.0%} {f'{283*elapsed:.0f}초':>15s}")


if __name__ == "__main__":
    run_test()
