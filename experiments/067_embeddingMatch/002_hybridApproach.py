"""
실험 ID: 067-002
실험명: 정규화 전처리 + 임베딩 하이브리드 항목 매칭

목적:
- 001 결과에서 임베딩 단독으로는 분리 불가 (gap=-0.06) 확인
- 정규화 전처리로 표면적 변이를 먼저 제거한 뒤 임베딩을 적용하면 분리되는지 검증
- 대안으로 정규화 + exact match + fallback 임베딩 전략 비교

가설:
1. 주석 제거, 단위 제거, 기수 제거 등 정규화 후 exact match만으로 80%+ 커버 가능
2. 남는 20%에만 임베딩 적용하면 속도와 정확도 모두 확보
3. 임베딩은 "DS부문 약어" 같은 구조 변이에만 필요

방법:
1. 정규화 함수 정의 (주석/단위/기수/괄호 내용 표준화)
2. 정규화 후 exact match 성공률 측정
3. 실패 케이스에만 임베딩 적용 후 분리도 재측정
4. 실제 테이블 항목으로 대규모 검증

결과 (실험 후 작성):

결론:

실험일: 2026-03-18
"""

import re
import time
import numpy as np
from difflib import SequenceMatcher

# ── 정규화 함수들 ──

def normalize_item(text: str) -> str:
    """항목명 정규화 — 표면적 변이 제거"""
    s = text.strip()
    # 1. 주석 번호 제거: (주1), (주22), (주석1) 등
    s = re.sub(r'\(주석?\d+\)', '', s)
    # 2. 단위 제거: (원), (백만원), (%), (천원), (억원)
    s = re.sub(r'\((?:원|백만원|천원|억원|%|천주|주)\)', '', s)
    # 3. 기수 제거: _당기, _전기, _전전기, 제76기, (당기), (전기)
    s = re.sub(r'_(?:당기|전기|전전기)', '', s)
    s = re.sub(r'\((?:당기|전기|전전기)\)', '', s)
    s = re.sub(r'제\d+기', '', s)
    # 4. 공백 정규화
    s = re.sub(r'\s+', ' ', s).strip()
    # 5. 빈 괄호 제거
    s = re.sub(r'\(\s*\)', '', s)
    return s


def normalize_aggressive(text: str) -> str:
    """공격적 정규화 — 괄호 내 세부 차이도 흡수"""
    s = normalize_item(text)
    # 괄호 안 쉼표 구분 내용 정렬 (순서 무관하게)
    def sort_parens(m):
        content = m.group(1)
        if ',' in content:
            parts = sorted(p.strip() for p in content.split(','))
            return '(' + ','.join(parts) + ')'
        return m.group(0)
    s = re.sub(r'\(([^)]+)\)', sort_parens, s)
    # 영문 대소문자 통일
    # SYS.LSI vs SystemLSI 같은 차이 → 소문자화
    s = s.lower()
    # 점, 공백 제거하여 약어 통일
    s = re.sub(r'[.\s]', '', s)
    return s


# ── 테스트 항목 ──
items = [
    "DS부문(메모리,SYS.LSI)",
    "DS부문(메모리,SystemLSI)",
    "사내이사",
    "사외이사",
    "등기이사(사외이사,감사위원회위원제외)",
    "등기이사(사외이사,감사위원회제외)",
    "매출액",
    "매출액(주22)",
    "당기순이익",
    "전기순이익",
    "(연결)당기순이익(백만원)",
    "(별도)당기순이익(백만원)",
    "주당액면가액(원)_당기",
    "주당액면가액(원)_전기",
    # 추가
    "보통주",
    "보통주(주1)",
    "우선주",
    "1주당 배당금(원)",
    "주당 배당금(원)",
    "현금배당수익률(%)",
    "현금배당성향(%)",
    "영업이익",
    "영업이익(손실)",
    "자본총계",
    "자본금",
]

# positive 쌍 (매칭해야 함)
positive_pairs = [
    (0, 1, "DS부문 약어"),
    (4, 5, "감사위원회 미세표현"),
    (6, 7, "주석번호 유무"),
    (8, 10, "당기순이익 ≈ (연결)당기순이익"),
    (10, 11, "(연결) vs (별도)"),
    (12, 13, "주당액면가액 당기/전기"),
    (14, 15, "보통주 ≈ 보통주(주1)"),
    (17, 18, "1주당 ≈ 주당 배당금"),
    (21, 22, "영업이익 ≈ 영업이익(손실)"),
]

# negative 쌍 (매칭하면 안 됨)
negative_pairs = [
    (2, 3, "사내이사 vs 사외이사"),
    (8, 9, "당기순이익 vs 전기순이익"),
    (14, 16, "보통주 vs 우선주"),
    (19, 20, "현금배당수익률 vs 현금배당성향"),
    (23, 24, "자본총계 vs 자본금"),
    (6, 8, "매출액 vs 당기순이익"),
]


def test_normalization():
    """정규화 결과 확인"""
    print("="*80)
    print("  Step 1: 정규화 결과")
    print("="*80)

    print("\n── normalize_item (기본 정규화) ──")
    for i, item in enumerate(items):
        norm = normalize_item(item)
        changed = " ←" if norm != item else ""
        print(f"  [{i:2d}] {item:40s} → {norm}{changed}")

    print("\n── normalize_aggressive (공격적 정규화) ──")
    for i, item in enumerate(items):
        norm = normalize_aggressive(item)
        changed = " ←" if norm != item.lower().replace('.','').replace(' ','') else ""
        print(f"  [{i:2d}] {item:40s} → {norm}")


def test_exact_match_after_norm():
    """정규화 후 exact match 테스트"""
    print(f"\n{'='*80}")
    print("  Step 2: 정규화 후 Exact Match")
    print("="*80)

    for label, norm_fn in [("기본 정규화", normalize_item),
                           ("공격적 정규화", normalize_aggressive)]:
        print(f"\n── {label} ──")
        normed = [norm_fn(item) for item in items]

        pos_match = 0
        for i, j, desc in positive_pairs:
            match = normed[i] == normed[j]
            marker = "✓" if match else "✗"
            if match:
                pos_match += 1
            print(f"  {marker} [{i:2d}]×[{j:2d}] {desc}")
            if not match:
                print(f"         '{normed[i]}' ≠ '{normed[j]}'")

        neg_safe = 0
        for i, j, desc in negative_pairs:
            match = normed[i] == normed[j]
            marker = "✓" if not match else "✗ FALSE POSITIVE!"
            if not match:
                neg_safe += 1
            print(f"  {marker} [{i:2d}]×[{j:2d}] {desc}")
            if match:
                print(f"         '{normed[i]}' == '{normed[j]}' → 오탐!")

        print(f"\n  Positive 매칭: {pos_match}/{len(positive_pairs)} ({pos_match/len(positive_pairs)*100:.0f}%)")
        print(f"  Negative 안전: {neg_safe}/{len(negative_pairs)} ({neg_safe/len(negative_pairs)*100:.0f}%)")


def test_tiered_matching():
    """3단계 tiered 매칭 전략"""
    print(f"\n{'='*80}")
    print("  Step 3: 3-Tier 매칭 전략")
    print("  Tier 1: 정규화 exact match")
    print("  Tier 2: 토큰 집합 유사도 (Jaccard)")
    print("  Tier 3: 임베딩 cosine (fallback)")
    print("="*80)

    def tokenize(text):
        """한국어 항목명을 의미 토큰으로 분해"""
        s = normalize_item(text)
        # 괄호 내용을 별도 토큰으로
        parens = re.findall(r'\(([^)]+)\)', s)
        base = re.sub(r'\([^)]*\)', '', s).strip()
        tokens = set()
        tokens.add(base)
        for p in parens:
            for part in p.split(','):
                tokens.add(part.strip())
        return tokens

    def jaccard(a, b):
        sa, sb = tokenize(a), tokenize(b)
        if not sa or not sb:
            return 0.0
        return len(sa & sb) / len(sa | sb)

    # Tier 1: exact match after normalization
    normed = [normalize_aggressive(item) for item in items]

    all_pairs = positive_pairs + negative_pairs
    results = {}

    print("\n── Tier 1: 정규화 exact match ──")
    tier1_resolved = set()
    for i, j, desc in all_pairs:
        if normed[i] == normed[j]:
            tier1_resolved.add((i, j))
            is_pos = any(pi == i and pj == j for pi, pj, _ in positive_pairs)
            marker = "✓" if is_pos else "✗ FALSE POSITIVE"
            print(f"  {marker} [{i:2d}]×[{j:2d}] = EXACT  {desc}")
            results[(i, j)] = ("exact", 1.0)

    # Tier 2: Jaccard for unresolved
    print("\n── Tier 2: 토큰 Jaccard (미해결 쌍) ──")
    tier2_resolved = set()
    for i, j, desc in all_pairs:
        if (i, j) in tier1_resolved:
            continue
        score = jaccard(items[i], items[j])
        is_pos = any(pi == i and pj == j for pi, pj, _ in positive_pairs)
        if score >= 0.5:
            tier2_resolved.add((i, j))
            marker = "✓" if is_pos else "✗ FALSE POSITIVE"
            results[(i, j)] = ("jaccard", score)
        else:
            marker = "·" if not is_pos else "? UNRESOLVED"
            results[(i, j)] = ("unresolved", score)
        print(f"  {marker} [{i:2d}]×[{j:2d}] = {score:.3f}  {desc}")

    # 미해결 쌍 목록
    unresolved = [(i, j, d) for i, j, d in all_pairs
                  if (i, j) not in tier1_resolved and (i, j) not in tier2_resolved]
    print(f"\n── 미해결 쌍: {len(unresolved)}개 → Tier 3 (임베딩) 대상 ──")
    for i, j, desc in unresolved:
        print(f"  [{i:2d}]×[{j:2d}] {desc}")

    return unresolved


def test_embedding_on_unresolved(unresolved):
    """미해결 쌍에 대해서만 임베딩 적용"""
    if not unresolved:
        print("\n모든 쌍이 Tier 1/2에서 해결됨. 임베딩 불필요!")
        return

    print(f"\n{'='*80}")
    print(f"  Step 4: 미해결 {len(unresolved)}쌍에 임베딩 적용")
    print("="*80)

    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("jhgan/ko-sroberta-multitask")

    # 미해결 쌍에 관련된 항목만 인코딩
    indices = set()
    for i, j, _ in unresolved:
        indices.add(i)
        indices.add(j)

    subset_items = [(idx, items[idx]) for idx in sorted(indices)]
    texts = [t for _, t in subset_items]

    t0 = time.time()
    embeddings = model.encode(texts)
    elapsed = time.time() - t0
    print(f"  {len(texts)}개 항목 인코딩: {elapsed:.3f}초")

    # 인덱스 매핑
    idx_map = {orig: enc for enc, (orig, _) in enumerate(subset_items)}

    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normed_emb = embeddings / norms

    for i, j, desc in unresolved:
        ei, ej = idx_map[i], idx_map[j]
        sim = float(normed_emb[ei] @ normed_emb[ej])
        is_pos = any(pi == i and pj == j for pi, pj, _ in positive_pairs)
        expected = "매칭" if is_pos else "비매칭"
        verdict = "✓" if (is_pos and sim > 0.75) or (not is_pos and sim < 0.75) else "✗"
        print(f"  {verdict} [{i:2d}]×[{j:2d}] = {sim:.4f} (기대: {expected})  {desc}")


def test_normalized_embedding():
    """정규화 후 임베딩으로 분리도 재측정"""
    print(f"\n{'='*80}")
    print("  Step 5: 정규화 후 임베딩 분리도")
    print("="*80)

    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("jhgan/ko-sroberta-multitask")

    normed_items = [normalize_item(item) for item in items]
    embeddings = model.encode(normed_items)

    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normed_emb = embeddings / norms
    sim_matrix = normed_emb @ normed_emb.T

    pos_scores = []
    neg_scores = []

    print("\n── Positive (정규화 후 임베딩) ──")
    for i, j, desc in positive_pairs:
        score = float(sim_matrix[i][j])
        pos_scores.append(score)
        print(f"  [{i:2d}]×[{j:2d}] = {score:.4f}  {desc}")

    print("\n── Negative (정규화 후 임베딩) ──")
    for i, j, desc in negative_pairs:
        score = float(sim_matrix[i][j])
        neg_scores.append(score)
        print(f"  [{i:2d}]×[{j:2d}] = {score:.4f}  {desc}")

    pos_min = min(pos_scores)
    neg_max = max(neg_scores)
    gap = pos_min - neg_max
    print(f"\n  Positive min: {pos_min:.4f}")
    print(f"  Negative max: {neg_max:.4f}")
    print(f"  Gap: {gap:.4f}")
    if gap > 0:
        print(f"  → 분리 가능! threshold ∈ ({neg_max:.4f}, {pos_min:.4f})")
    else:
        print(f"  → 분리 불가능")


def test_final_strategy():
    """최종 전략: 정규화 단계별 매칭"""
    print(f"\n{'='*80}")
    print("  FINAL: 권장 매칭 전략")
    print("="*80)

    all_pairs = positive_pairs + negative_pairs
    tp, fp, fn, tn = 0, 0, 0, 0

    for i, j, desc in all_pairs:
        is_pos = any(pi == i and pj == j for pi, pj, _ in positive_pairs)

        # Step 1: 공격적 정규화 exact match
        na, nb = normalize_aggressive(items[i]), normalize_aggressive(items[j])
        if na == nb:
            predicted = True
        else:
            # Step 2: 기본 정규화 후 접두사/접미사 허용 매칭
            na2, nb2 = normalize_item(items[i]), normalize_item(items[j])
            # 짧은 쪽이 긴 쪽에 포함되면 매칭 (매출액 ⊂ 매출액(주22) → 정규화 후 매출액 == 매출액)
            if na2 == nb2:
                predicted = True
            elif len(na2) > 2 and len(nb2) > 2:
                # 한쪽이 다른 쪽을 포함하면 매칭
                if na2 in nb2 or nb2 in na2:
                    predicted = True
                else:
                    # Step 3: 구조 유사도 (수정된 SequenceMatcher)
                    ratio = SequenceMatcher(None, na2, nb2).ratio()
                    predicted = ratio >= 0.85
            else:
                predicted = False

        if is_pos and predicted:
            tp += 1
            marker = "✓ TP"
        elif is_pos and not predicted:
            fn += 1
            marker = "✗ FN"
        elif not is_pos and predicted:
            fp += 1
            marker = "✗ FP"
        else:
            tn += 1
            marker = "✓ TN"

        print(f"  {marker}  [{i:2d}]×[{j:2d}]  {desc}")

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    accuracy = (tp + tn) / (tp + fp + fn + tn)

    print(f"\n  TP={tp}  FP={fp}  FN={fn}  TN={tn}")
    print(f"  Precision: {precision:.2%}")
    print(f"  Recall:    {recall:.2%}")
    print(f"  F1:        {f1:.2%}")
    print(f"  Accuracy:  {accuracy:.2%}")


if __name__ == "__main__":
    test_normalization()
    test_exact_match_after_norm()
    unresolved = test_tiered_matching()
    test_embedding_on_unresolved(unresolved)
    test_normalized_embedding()
    test_final_strategy()
