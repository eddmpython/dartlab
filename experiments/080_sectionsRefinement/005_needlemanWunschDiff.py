"""실험 ID: 080-005
실험명: Needleman-Wunsch 단락 정렬 vs difflib SequenceMatcher

목적:
- 기간 간 공시 텍스트 diff에서 difflib 대비 NW 정렬이 얼마나 나은지 측정
- 특히 단락 재배치/삽입/삭제가 있을 때 정렬 품질 비교

가설:
1. NW 정렬이 difflib보다 재배치된 단락을 올바르게 매칭하는 비율이 20%+ 높다
2. 짧은 텍스트(5단락 미만)에서는 차이 없고, 긴 텍스트(10단락+)에서 차이 뚜렷

방법:
1. 10종목에서 sections 로드 → 기간 간 텍스트 쌍 수집
2. 각 쌍을 단락 단위로 분할
3. difflib SequenceMatcher 정렬 결과 추출
4. NW 정렬(rapidfuzz ratio로 유사도 채점) 결과 추출
5. 두 방법의 매칭된 단락 쌍 수, 유사도 합계, gap 수 비교

결과 (293건, 10종목, 234,914단락):
- 전체 평균 유사도: NW 88.1 vs difflib 85.1 → NW +3.0
- 고품질(≥70) 매칭: NW 81,174 vs difflib 75,202 → NW +5,972건 (7.9% 더 많음)
- 총 매칭 수: NW 95,971 vs difflib 88,832 → NW +7,139건
- 승패: NW 승 225건 / difflib 승 40건 / 동률 28건 (NW 76.8% 승률)
- 단락 수 구간별:
  - 10-50단락 (6건): NW 96.4 vs DL 92.6 → +3.8
  - 50+단락 (270건): NW 88.4 vs DL 84.8 → +3.6
- NW 최대 우위: consolidatedNotes (K-IFRS 주석) — +54.8 (NW 71.1 vs DL 16.3)
  - 주석은 단락 재배치/삽입이 많아 NW의 글로벌 정렬이 크게 유리
- difflib 우위 사례: fsSummary 대규모(1000+ 단락) — NW가 -36.3까지 열세
  - 원인: 매우 큰 시퀀스에서 NW의 O(n²) DP가 잘못된 gap 매칭 가능

결론:
- 가설 1 부분 채택: NW가 difflib보다 평균 +3.0 우위 (20%까지는 아님)
  단, consolidatedNotes(주석) 같은 재배치 빈번한 텍스트에서는 +54.8까지 압도적
- 가설 2 기각: 짧은 텍스트(10-50)에서도 +3.8 차이 존재, 긴 텍스트(50+)와 유사
- 실전 적용 권장: 50단락 이상 텍스트 diff에 NW 적용 시 매칭 품질 개선
  단, 1000+ 단락에서는 성능/품질 모두 검증 필요 (fsSummary 열세 사례)
- NW의 O(n²) 복잡도는 500단락 이하에서 문제없으나, 그 이상은 banded NW 고려

실험일: 2026-03-20
"""
from __future__ import annotations

import difflib
import sys
from pathlib import Path

import polars as pl
from rapidfuzz import fuzz

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


# ── Needleman-Wunsch 단락 정렬 ──────────────────────────────

def needleman_wunsch(
    seq_a: list[str],
    seq_b: list[str],
    *,
    sim_fn=None,
    gap_penalty: float = -0.3,
    match_threshold: float = 50.0,
) -> list[tuple[int | None, int | None, float]]:
    """Needleman-Wunsch 글로벌 정렬.

    Returns:
        [(i, j, score)] — i=seq_a idx(또는 None=gap), j=seq_b idx(또는 None=gap)
    """
    if sim_fn is None:
        sim_fn = lambda a, b: fuzz.ratio(a, b)

    n, m = len(seq_a), len(seq_b)

    # 유사도 매트릭스 사전 계산
    sim_matrix = [[0.0] * m for _ in range(n)]
    for i in range(n):
        for j in range(m):
            sim_matrix[i][j] = sim_fn(seq_a[i], seq_b[j])

    # DP 테이블
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0] = dp[i - 1][0] + gap_penalty
    for j in range(1, m + 1):
        dp[0][j] = dp[0][j - 1] + gap_penalty

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            sim = sim_matrix[i - 1][j - 1]
            # 매칭 점수: 높은 유사도 → 보상, 낮은 유사도 → 페널티
            match_score = (sim - match_threshold) / 100.0
            dp[i][j] = max(
                dp[i - 1][j - 1] + match_score,  # 매칭/미스매치
                dp[i - 1][j] + gap_penalty,        # seq_a 삭제
                dp[i][j - 1] + gap_penalty,        # seq_b 삽입
            )

    # 역추적
    alignment = []
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0:
            sim = sim_matrix[i - 1][j - 1]
            match_score = (sim - match_threshold) / 100.0
            if dp[i][j] == dp[i - 1][j - 1] + match_score:
                alignment.append((i - 1, j - 1, sim))
                i -= 1
                j -= 1
                continue
        if i > 0 and dp[i][j] == dp[i - 1][j] + gap_penalty:
            alignment.append((i - 1, None, 0.0))
            i -= 1
        else:
            alignment.append((None, j - 1, 0.0))
            j -= 1

    alignment.reverse()
    return alignment


def difflib_align(
    seq_a: list[str], seq_b: list[str], *, sim_fn=None
) -> list[tuple[int | None, int | None, float]]:
    """difflib SequenceMatcher 기반 정렬."""
    if sim_fn is None:
        sim_fn = lambda a, b: fuzz.ratio(a, b)

    alignment = []
    matcher = difflib.SequenceMatcher(None, seq_a, seq_b)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                alignment.append((i1 + k, j1 + k, 100.0))
        elif tag == "replace":
            # 1:1 매칭 시도
            la, lb = i2 - i1, j2 - j1
            for k in range(max(la, lb)):
                ai = i1 + k if k < la else None
                bj = j1 + k if k < lb else None
                sim = sim_fn(seq_a[ai], seq_b[bj]) if ai is not None and bj is not None else 0.0
                alignment.append((ai, bj, sim))
        elif tag == "delete":
            for k in range(i1, i2):
                alignment.append((k, None, 0.0))
        elif tag == "insert":
            for k in range(j1, j2):
                alignment.append((None, k, 0.0))

    return alignment


# ── 평가 지표 ──────────────────────────────────────────────

def evaluate_alignment(alignment: list[tuple[int | None, int | None, float]]) -> dict:
    """정렬 품질 지표 계산."""
    matched = [(a, b, s) for a, b, s in alignment if a is not None and b is not None]
    gaps_a = sum(1 for a, b, _ in alignment if a is not None and b is None)
    gaps_b = sum(1 for a, b, _ in alignment if a is None and b is not None)
    avg_sim = sum(s for _, _, s in matched) / len(matched) if matched else 0.0
    high_quality = sum(1 for _, _, s in matched if s >= 70.0)

    return {
        "matched": len(matched),
        "gaps_a": gaps_a,
        "gaps_b": gaps_b,
        "avg_sim": round(avg_sim, 1),
        "high_quality": high_quality,
        "total": len(alignment),
    }


def split_paragraphs(text: str) -> list[str]:
    """텍스트를 단락으로 분할 (빈 줄 기준)."""
    paras = []
    current = []
    for line in text.splitlines():
        if line.strip() == "":
            if current:
                paras.append("\n".join(current))
                current = []
        else:
            current.append(line)
    if current:
        paras.append("\n".join(current))
    return paras


if __name__ == "__main__":
    print("=" * 70)
    print("080-005: Needleman-Wunsch 단락 정렬 vs difflib SequenceMatcher")
    print("=" * 70)

    from dartlab import Company

    sample_codes = [
        "005930",  # 삼성전자
        "000660",  # SK하이닉스
        "005380",  # 현대자동차
        "035420",  # NAVER
        "105560",  # KB금융
        "055550",  # 신한지주
        "017670",  # SK텔레콤
        "032830",  # 삼성생명
        "003550",  # LG
        "006400",  # 삼성SDI
    ]

    all_results = []
    text_pairs = 0
    total_paras = 0

    for code in sample_codes:
        try:
            c = Company(code)
            sec = c.docs.sections
        except (FileNotFoundError, OSError, ValueError) as e:
            print(f"  {code}: {e}")
            continue

        periods = [col for col in sec.columns if col[:4].isdigit()]
        if len(periods) < 2:
            continue

        # text 블록만
        if "blockType" in sec.columns:
            textSec = sec.filter(pl.col("blockType") == "text")
        else:
            textSec = sec

        topics = textSec["topic"].unique().to_list()

        # 연도 기간만 사용 (분기 제외 — 텍스트 비교에 적합)
        annualPeriods = [p for p in periods if "Q" not in p]
        if len(annualPeriods) < 2:
            annualPeriods = periods[:min(6, len(periods))]

        # topic을 row 수 기준 내림차순 정렬 — row가 많을수록 비교에 유의미
        def _max_row_count(topic: str) -> int:
            rows = textSec.filter(pl.col("topic") == topic)
            best = 0
            for p in annualPeriods:
                if p not in rows.columns:
                    continue
                best = max(best, rows[p].drop_nulls().len())
            return best

        topics = sorted(topics, key=_max_row_count, reverse=True)

        for topic in topics[:5]:  # row 많은 topic 우선
            topicRows = textSec.filter(pl.col("topic") == topic)
            for pi in range(len(annualPeriods) - 1):
                p1, p2 = annualPeriods[pi], annualPeriods[pi + 1]
                if p1 not in topicRows.columns or p2 not in topicRows.columns:
                    continue

                # sections의 각 row가 이미 단락 → 직접 리스트로 사용
                paras1 = [str(v) for v in topicRows[p1].drop_nulls().to_list()]
                paras2 = [str(v) for v in topicRows[p2].drop_nulls().to_list()]
                if len(paras1) < 3 or len(paras2) < 3:
                    continue

                text_pairs += 1
                total_paras += len(paras1) + len(paras2)

                # 두 방법 비교
                nw_align = needleman_wunsch(paras1, paras2)
                dl_align = difflib_align(paras1, paras2)

                nw_eval = evaluate_alignment(nw_align)
                dl_eval = evaluate_alignment(dl_align)

                all_results.append({
                    "code": code,
                    "topic": topic,
                    "periods": f"{p1}-{p2}",
                    "paras_a": len(paras1),
                    "paras_b": len(paras2),
                    "nw_matched": nw_eval["matched"],
                    "nw_avg_sim": nw_eval["avg_sim"],
                    "nw_high_q": nw_eval["high_quality"],
                    "dl_matched": dl_eval["matched"],
                    "dl_avg_sim": dl_eval["avg_sim"],
                    "dl_high_q": dl_eval["high_quality"],
                    "sim_diff": round(nw_eval["avg_sim"] - dl_eval["avg_sim"], 1),
                })

    print(f"\n총 텍스트 쌍: {text_pairs}개, 총 단락: {total_paras}개")

    if not all_results:
        print("비교 가능한 텍스트 쌍이 없습니다.")
        sys.exit(0)

    df = pl.DataFrame(all_results)
    print(f"\n비교 결과 ({df.height}건):")

    # 전체 통계
    nw_avg = df["nw_avg_sim"].mean()
    dl_avg = df["dl_avg_sim"].mean()
    nw_hq = df["nw_high_q"].sum()
    dl_hq = df["dl_high_q"].sum()
    nw_matched_total = df["nw_matched"].sum()
    dl_matched_total = df["dl_matched"].sum()

    print(f"\n=== 전체 통계 ===")
    print(f"  NW 평균 유사도: {nw_avg:.1f}  |  difflib 평균 유사도: {dl_avg:.1f}  |  차이: {nw_avg - dl_avg:+.1f}")
    print(f"  NW 고품질(≥70) 매칭: {nw_hq}  |  difflib 고품질: {dl_hq}  |  차이: {nw_hq - dl_hq:+d}")
    print(f"  NW 총 매칭: {nw_matched_total}  |  difflib 총 매칭: {dl_matched_total}")

    # NW가 더 나은 경우
    nw_better = df.filter(pl.col("sim_diff") > 0)
    dl_better = df.filter(pl.col("sim_diff") < 0)
    tied = df.filter(pl.col("sim_diff") == 0)
    print(f"\n  NW 승: {nw_better.height}건  |  difflib 승: {dl_better.height}건  |  동률: {tied.height}건")

    # 단락 수 구간별 분석
    print(f"\n=== 단락 수 구간별 ===")
    for lo, hi, label in [(3, 5, "3-5"), (5, 10, "5-10"), (10, 50, "10-50"), (50, 999, "50+")]:
        subset = df.filter((pl.col("paras_a") >= lo) & (pl.col("paras_a") < hi))
        if subset.height == 0:
            continue
        nw_m = subset["nw_avg_sim"].mean()
        dl_m = subset["dl_avg_sim"].mean()
        print(f"  {label}단락 ({subset.height}건): NW {nw_m:.1f} vs DL {dl_m:.1f} → 차이 {nw_m - dl_m:+.1f}")

    # NW가 크게 나은 사례 Top-5
    if nw_better.height > 0:
        print(f"\n=== NW가 크게 나은 사례 (Top-5) ===")
        top5 = nw_better.sort("sim_diff", descending=True).head(5)
        for row in top5.iter_rows(named=True):
            print(f"  {row['code']} {row['topic']} {row['periods']}: "
                  f"NW {row['nw_avg_sim']} vs DL {row['dl_avg_sim']} (+{row['sim_diff']})")

    print(f"\n상세:")
    print(df.sort("sim_diff", descending=True))
