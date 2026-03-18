"""
실험 ID: 067
실험명: 한국어 sentence-transformer 기반 테이블 항목 매칭

목적:
- DART 사업보고서 마크다운 테이블의 기간별 항목 매칭에서 임베딩 유사도가 fuzzy matching보다 우수한지 검증
- 매칭해야 할 쌍(positive)과 매칭하면 안 되는 쌍(negative)의 유사도 분포를 비교

가설:
1. 한국어 sentence-transformer(ko-sroberta-multitask)는 의미적 유사도를 반영하여
   "사내이사"와 "사외이사"를 구분(cosine < 0.85)하면서
   "감사위원회제외"와 "감사위원회위원제외"를 통합(cosine > 0.90)할 수 있다
2. fuzzy matching(SequenceMatcher) 대비 positive/negative 분리도가 높다

방법:
1. 14개 항목명으로 cosine similarity matrix 계산
2. positive 쌍(매칭해야 할 것) 7개, negative 쌍(매칭하면 안 되는 것) 7개 정의
3. 임베딩 유사도 vs fuzzy 유사도 비교
4. threshold 탐색: positive min > negative max 되는 구간 확인
5. 인코딩 속도 측정

결과 (실험 후 작성):

결론:

실험일: 2026-03-18
"""

import time
import numpy as np

# ── 항목 목록 ──
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
]

# ── 매칭해야 할 쌍 (positive) ──
positive_pairs = [
    (0, 1, "DS부문 약어 차이"),
    (4, 5, "감사위원회 미세표현"),
    (6, 7, "주석번호 유무"),
    (8, 10, "당기순이익 ≈ (연결)당기순이익"),
    (8, 11, "당기순이익 ≈ (별도)당기순이익"),
    (10, 11, "(연결) vs (별도) 당기순이익"),
    (12, 13, "주당액면가액 당기/전기"),
]

# ── 매칭하면 안 되는 쌍 (negative) ──
negative_pairs = [
    (2, 3, "사내이사 vs 사외이사"),
    (8, 9, "당기순이익 vs 전기순이익"),
    (6, 8, "매출액 vs 당기순이익"),
    (2, 6, "사내이사 vs 매출액"),
    (0, 6, "DS부문 vs 매출액"),
    (12, 8, "주당액면가액 vs 당기순이익"),
    (2, 4, "사내이사 vs 등기이사(사외이사...)"),
]

# ── 추가 엣지케이스 ──
extra_items = [
    "보통주",
    "우선주",
    "보통주(주1)",
    "1주당 배당금(원)",
    "주당 배당금(원)",
    "현금배당수익률(%)",
    "현금배당성향(%)",
    "영업이익",
    "영업이익(손실)",
    "자본총계",
    "자본금",
]

extra_positive = [
    (0, 2, "보통주 ≈ 보통주(주1)"),
    (3, 4, "1주당 배당금 ≈ 주당 배당금"),
    (7, 8, "영업이익 ≈ 영업이익(손실)"),
]
extra_negative = [
    (0, 1, "보통주 vs 우선주"),
    (5, 6, "현금배당수익률 vs 현금배당성향"),
    (9, 10, "자본총계 vs 자본금"),
]


def cosine_sim_matrix(embeddings):
    """코사인 유사도 행렬 계산"""
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normed = embeddings / norms
    return normed @ normed.T


def fuzzy_ratio(a, b):
    """SequenceMatcher 유사도"""
    from difflib import SequenceMatcher
    return SequenceMatcher(None, a, b).ratio()


def print_matrix(items, sim_matrix, title=""):
    """유사도 행렬 출력"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}")

    # 항목 인덱스 헤더
    header = "      " + "".join(f"  [{i:2d}]" for i in range(len(items)))
    print(header)

    for i, item in enumerate(items):
        row = f"[{i:2d}] "
        for j in range(len(items)):
            val = sim_matrix[i][j]
            if i == j:
                row += "  ----"
            else:
                row += f"  {val:.2f}"
        label = item[:20]
        row += f"  {label}"
        print(row)


def evaluate_pairs(pairs, sim_matrix, items_list, label=""):
    """쌍별 유사도 평가"""
    print(f"\n── {label} ──")
    scores = []
    for i, j, desc in pairs:
        score = sim_matrix[i][j]
        scores.append(score)
        marker = "✓" if (label.startswith("Positive") and score > 0.85) or \
                       (label.startswith("Negative") and score < 0.85) else "✗"
        print(f"  {marker} [{i:2d}]×[{j:2d}] = {score:.4f}  {desc}")
        print(f"         {items_list[i][:30]}  ↔  {items_list[j][:30]}")

    arr = np.array(scores)
    print(f"  ── min={arr.min():.4f}  max={arr.max():.4f}  mean={arr.mean():.4f}  std={arr.std():.4f}")
    return scores


def run_embedding_experiment():
    """임베딩 실험"""
    from sentence_transformers import SentenceTransformer

    print("모델 로딩: jhgan/ko-sroberta-multitask")
    t0 = time.time()
    model = SentenceTransformer("jhgan/ko-sroberta-multitask")
    print(f"  모델 로딩: {time.time()-t0:.1f}초")

    # ── 메인 항목 인코딩 ──
    t0 = time.time()
    embeddings = model.encode(items)
    encode_time = time.time() - t0
    print(f"  {len(items)}개 항목 인코딩: {encode_time:.3f}초 ({encode_time/len(items)*1000:.1f}ms/항목)")

    sim = cosine_sim_matrix(embeddings)
    print_matrix(items, sim, "Embedding Cosine Similarity (ko-sroberta)")

    pos_scores = evaluate_pairs(positive_pairs, sim, items, "Positive (매칭해야 함)")
    neg_scores = evaluate_pairs(negative_pairs, sim, items, "Negative (매칭하면 안 됨)")

    # ── 분리도 분석 ──
    pos_min = min(pos_scores)
    neg_max = max(neg_scores)
    gap = pos_min - neg_max
    print(f"\n── 분리도 분석 ──")
    print(f"  Positive min: {pos_min:.4f}")
    print(f"  Negative max: {neg_max:.4f}")
    print(f"  Gap (pos_min - neg_max): {gap:.4f}")
    if gap > 0:
        print(f"  → 분리 가능! threshold ∈ ({neg_max:.4f}, {pos_min:.4f})")
    else:
        print(f"  → 분리 불가능. 겹침 구간 존재")

    # ── 추가 엣지케이스 ──
    print(f"\n{'='*80}")
    print(f"  추가 엣지케이스 (extra_items)")
    print(f"{'='*80}")

    extra_emb = model.encode(extra_items)
    extra_sim = cosine_sim_matrix(extra_emb)
    print_matrix(extra_items, extra_sim, "Extra Items Cosine Similarity")

    evaluate_pairs(extra_positive, extra_sim, extra_items, "Positive (매칭해야 함)")
    evaluate_pairs(extra_negative, extra_sim, extra_items, "Negative (매칭하면 안 됨)")

    # ── 속도 벤치마크 ──
    print(f"\n── 속도 벤치마크 ──")
    batch_sizes = [100, 500, 1000]
    for n in batch_sizes:
        fake_items = [f"테스트항목{i}" for i in range(n)]
        t0 = time.time()
        model.encode(fake_items, batch_size=64)
        elapsed = time.time() - t0
        print(f"  {n}개 항목: {elapsed:.2f}초 ({elapsed/n*1000:.1f}ms/항목)")

    # 283종목 × 200항목 추정
    per_item_ms = encode_time / len(items) * 1000
    total_est = 283 * 200 * per_item_ms / 1000
    print(f"  283종목 × 200항목 추정: {total_est:.0f}초 ({total_est/60:.1f}분)")

    return sim


def run_fuzzy_experiment():
    """Fuzzy matching 비교 실험"""
    print(f"\n{'='*80}")
    print(f"  Fuzzy Matching (SequenceMatcher) 비교")
    print(f"{'='*80}")

    # fuzzy sim matrix
    n = len(items)
    fuzzy_sim = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            fuzzy_sim[i][j] = fuzzy_ratio(items[i], items[j])

    print_matrix(items, fuzzy_sim, "Fuzzy Similarity (SequenceMatcher)")

    pos_scores = evaluate_pairs(positive_pairs, fuzzy_sim, items, "Positive (매칭해야 함)")
    neg_scores = evaluate_pairs(negative_pairs, fuzzy_sim, items, "Negative (매칭하면 안 됨)")

    pos_min = min(pos_scores)
    neg_max = max(neg_scores)
    gap = pos_min - neg_max
    print(f"\n── Fuzzy 분리도 분석 ──")
    print(f"  Positive min: {pos_min:.4f}")
    print(f"  Negative max: {neg_max:.4f}")
    print(f"  Gap: {gap:.4f}")
    if gap > 0:
        print(f"  → 분리 가능! threshold ∈ ({neg_max:.4f}, {pos_min:.4f})")
    else:
        print(f"  → 분리 불가능. 겹침 구간 존재")

    return fuzzy_sim


if __name__ == "__main__":
    print("="*80)
    print("  실험 067: 한국어 Sentence-Transformer 항목 매칭")
    print("="*80)

    # 1. Fuzzy 먼저 (baseline)
    fuzzy_sim = run_fuzzy_experiment()

    # 2. Embedding
    try:
        emb_sim = run_embedding_experiment()
    except ImportError:
        print("\n[ERROR] sentence-transformers 미설치. 설치 후 재실행:")
        print("  pip install sentence-transformers")
    except Exception as e:
        print(f"\n[ERROR] 임베딩 실험 실패: {e}")
        import traceback
        traceback.print_exc()
