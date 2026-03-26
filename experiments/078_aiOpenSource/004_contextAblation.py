"""
실험 ID: 004
실험명: Context Ablation — skeleton/focused/full tier별 품질 차이 정량화

목적:
- tiered context (skeleton ~500tok / focused ~2k / full ~14k)가 실제 응답 품질에 미치는 영향 측정
- 토큰 효율(점수/토큰)을 계산하여 최적 tier 전략 도출

가설:
1. full > focused > skeleton 순으로 품질이 높되, full과 focused의 차이는 20% 미만
2. skeleton은 full 대비 40%+ 품질 하락
3. 토큰 효율(점수/1000tok)은 focused가 가장 높다

방법:
1. golden_dataset.json에서 5건 선택 (003과 동일 subset)
2. 각 질문에 대해 3개 tier의 context 생성
3. 각 tier별 토큰 수 측정 + 실제 LLM 호출 + 자동 채점
4. tier별 평균 점수, 토큰 수, 효율 비교

결과 (실험 후 작성):

결론:

실험일: 2026-03-20
"""

import importlib.util
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))


def _load_scorer():
    """002 채점기 동적 로드."""
    spec = importlib.util.spec_from_file_location(
        "_scoring", Path(__file__).parent / "002_scoringRubric.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.auto_score


def _estimate_tokens(text: str) -> int:
    """간이 토큰 추정 (한국어: ~1.5 char/token, 영어: ~4 char/token)."""
    korean_chars = sum(1 for c in text if "\uac00" <= c <= "\ud7a3")
    other_chars = len(text) - korean_chars
    return int(korean_chars / 1.5 + other_chars / 4)


def build_contexts_by_tier(company, question: str) -> dict[str, str]:
    """한 질문에 대해 3개 tier context 생성."""
    from dartlab.ai.context import (
        build_context_by_module,
        build_context_focused,
        build_context_skeleton,
    )

    # skeleton (~500 tokens) → (text, included_list)
    skeleton_text, _sk_included = build_context_skeleton(company)
    skeleton_ctx = skeleton_text

    # focused (~2000 tokens) → (modules_dict, included_list, header)
    fo_modules, _fo_included, fo_header = build_context_focused(company, question)
    focused_ctx = fo_header + "\n\n" + "\n\n".join(fo_modules.values())

    # full (~14000 tokens)
    full_modules, _fu_included, full_header = build_context_by_module(
        company, question, compact=False
    )
    full_ctx = full_header + "\n\n" + "\n\n".join(full_modules.values())

    return {
        "skeleton": skeleton_ctx,
        "focused": focused_ctx,
        "full": full_ctx,
    }


def run_ablation(qa_subset: list[dict], provider_name: str = "claude") -> list[dict]:
    """tier별 LLM 호출 + 채점."""
    import dartlab
    from dartlab.ai.prompts import SYSTEM_PROMPT_KR
    from dartlab.ai.providers import create_provider
    from dartlab.ai.types import LLMConfig

    auto_score = _load_scorer()

    config = LLMConfig(provider=provider_name, temperature=0.3, max_tokens=1024)
    provider = create_provider(config)

    if not provider.check_available():
        print(f"  [{provider_name}] 사용 불가")
        return []

    # API 연결 테스트
    try:
        test_resp = provider.complete([{"role": "user", "content": "OK"}])
        if not test_resp.answer:
            print(f"  [{provider_name}] 테스트 실패")
            return []
    except (TypeError, ConnectionError, RuntimeError, OSError, ValueError) as e:
        print(f"  [{provider_name}] 테스트 실패: {e}")
        return []

    print(f"  provider: {provider_name} ({provider.resolved_model})")
    results = []
    tiers = ["skeleton", "focused", "full"]

    for qa in qa_subset:
        code = qa["stock_code"]
        question = qa["question"]
        qa_id = qa["id"]

        try:
            c = dartlab.Company(code)
            contexts = build_contexts_by_tier(c, question)

            for tier in tiers:
                ctx = contexts[tier]
                tokens = _estimate_tokens(ctx)

                system_prompt = SYSTEM_PROMPT_KR[:2000]
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"[컨텍스트]\n{ctx}\n\n[질문]\n{question}"},
                ]

                start = time.perf_counter()
                response = provider.complete(messages)
                elapsed = time.perf_counter() - start

                answer = response.answer
                scores = auto_score(answer, qa["expected_facts"])

                results.append({
                    "qa_id": qa_id,
                    "tier": tier,
                    "context_tokens": tokens,
                    "answer_length": len(answer),
                    "latency_s": round(elapsed, 2),
                    "scores": {
                        "factual_accuracy": scores.factual_accuracy,
                        "completeness": scores.completeness,
                        "source_citation": scores.source_citation,
                        "hallucination": scores.hallucination,
                        "actionability": scores.actionability,
                        "total": scores.total,
                    },
                })

                efficiency = round(scores.total / max(tokens / 1000, 0.1), 2)
                print(f"  {qa_id} [{tier:>8}] tok={tokens:>5} total={scores.total} eff={efficiency} ({elapsed:.1f}s)")

        except (TypeError, ConnectionError, RuntimeError, OSError, ValueError) as e:
            print(f"  {qa_id}: ERROR {type(e).__name__}: {e}")

    return results


def analyze_results(results: list[dict]) -> dict:
    """tier별 집계 및 비교."""
    tiers = ["skeleton", "focused", "full"]
    summary = {}

    for tier in tiers:
        tier_results = [r for r in results if r["tier"] == tier]
        if not tier_results:
            continue

        totals = [r["scores"]["total"] for r in tier_results]
        tokens = [r["context_tokens"] for r in tier_results]
        latencies = [r["latency_s"] for r in tier_results]

        avg_total = round(sum(totals) / len(totals), 2)
        avg_tokens = round(sum(tokens) / len(tokens))
        avg_latency = round(sum(latencies) / len(latencies), 2)
        efficiency = round(avg_total / max(avg_tokens / 1000, 0.1), 2)

        dims = ["factual_accuracy", "completeness", "source_citation", "hallucination", "actionability"]
        avg_dims = {}
        for d in dims:
            vals = [r["scores"][d] for r in tier_results]
            avg_dims[d] = round(sum(vals) / len(vals), 2)

        summary[tier] = {
            "count": len(tier_results),
            "avg_total": avg_total,
            "avg_tokens": avg_tokens,
            "avg_latency_s": avg_latency,
            "efficiency_per_1k_tok": efficiency,
            "avg_by_dimension": avg_dims,
        }

    return summary


if __name__ == "__main__":
    exp_dir = Path(__file__).parent

    print("=" * 60)
    print("실험 004: Context Ablation")
    print("=" * 60)

    # Load golden dataset
    golden_path = exp_dir / "golden_dataset.json"
    with open(golden_path, encoding="utf-8") as f:
        golden = json.load(f)

    # 003과 동일 subset
    targets = [
        ("005930", "health"),
        ("005930", "profitability"),
        ("005930", "cashflow"),
        ("000660", "health"),
        ("051910", "health"),
    ]
    subset = []
    for code, qtype in targets:
        for qa in golden:
            if qa["stock_code"] == code and qa["question_type"] == qtype:
                subset.append(qa)
                break

    print(f"\n벤치마크 QA: {len(subset)}건")

    # Run ablation
    results = run_ablation(subset, provider_name="claude")

    if not results:
        print("\n결과 없음 — provider 미사용")
    else:
        summary = analyze_results(results)

        print("\n" + "=" * 60)
        print("=== Tier별 요약 ===")
        print("=" * 60)

        for tier, s in summary.items():
            print(f"\n[{tier}]")
            print(f"  평균 총점: {s['avg_total']}/5.0")
            print(f"  평균 토큰: {s['avg_tokens']}")
            print(f"  평균 지연: {s['avg_latency_s']}s")
            print(f"  효율(점/1k tok): {s['efficiency_per_1k_tok']}")
            dims = s["avg_by_dimension"]
            print(f"  FA={dims['factual_accuracy']} CO={dims['completeness']} SC={dims['source_citation']} HA={dims['hallucination']} AC={dims['actionability']}")

        # Tier간 비교
        if "skeleton" in summary and "full" in summary:
            sk = summary["skeleton"]["avg_total"]
            fu = summary["full"]["avg_total"]
            drop = round((1 - sk / max(fu, 0.01)) * 100, 1)
            print(f"\nskeleton vs full: {drop}% 하락 (가설: 40%+)")

        if "focused" in summary and "full" in summary:
            fo = summary["focused"]["avg_total"]
            fu = summary["full"]["avg_total"]
            drop = round((1 - fo / max(fu, 0.01)) * 100, 1)
            print(f"focused vs full: {drop}% 하락 (가설: 20% 미만)")

        if "focused" in summary:
            print(f"\nfocused 효율: {summary['focused']['efficiency_per_1k_tok']} 점/1k tok (가설: 최고)")

        # 저장
        output = {
            "experiment_date": "2026-03-20",
            "qa_count": len(subset),
            "provider": "claude",
            "results": results,
            "summary": summary,
        }
        output_path = exp_dir / "context_ablation.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2, default=str)
        print(f"\n저장: {output_path}")
