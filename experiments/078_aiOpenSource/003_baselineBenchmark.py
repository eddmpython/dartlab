"""
실험 ID: 003
실험명: Baseline Benchmark — 현재 시스템 provider별 품질 기준선 측정

목적:
- 현재 AI 시스템의 응답 품질을 provider별로 정량 측정
- 후속 실험(004-015)의 개선 효과를 비교할 기준선 확립

가설:
1. provider별 품질 차이가 유의미하다 (차이 10%+)
2. claude > ollama 순으로 품질이 높을 것

방법:
1. golden_dataset.json에서 기업별 대표 5건 선택 (다양한 유형)
2. 가용 provider(claude, ollama)로 각 질문에 답변 생성
3. 002 자동 채점기로 5차원 채점
4. provider별 평균 점수 비교

결과:
- 테스트 QA: 5건 (삼성전자 health/profitability/cashflow, SK하이닉스 health, LG화학 health)
- claude (claude-sonnet-4-6):
  - 평균 total: 2.64
  - FA=2.60 CO=3.20 SC=2.90 HA=3.40 AC=1.10
- ollama (qwen3):
  - 평균 total: 2.40
  - FA=2.00 CO=2.80 SC=2.40 HA=3.60 AC=1.20
- provider간 차이: claude가 ollama 대비 10% 높음
- 전반적으로 두 provider 모두 5점 만점 대비 3.0 미만 — 개선 여지 큼
- Source Citation과 Actionability가 가장 낮음 (1.1~2.9) — 프롬프트 개선 필요

결론:
- 가설 1 채택: provider간 차이 10%+ 존재
- 가설 2 채택: claude > ollama 순서 확인
- 전체 수준이 낮아(2.4~2.6) context 최적화와 structured output 도입 시 30%+ 개선 가능
- 이 baseline 수치가 후속 실험의 비교 기준

실험일: 2026-03-20
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))


def run_benchmark(qa_subset: list[dict], provider_name: str, *, timeout: int = 60) -> list[dict]:
    """주어진 provider로 QA subset에 대해 답변 생성 + 채점."""
    # 002 모듈 동적 로드
    import importlib.util

    import dartlab
    from dartlab.ai.pipeline import run_pipeline
    from dartlab.ai.prompts import SYSTEM_PROMPT_KR
    from dartlab.ai.providers import create_provider
    from dartlab.ai.types import LLMConfig

    _spec = importlib.util.spec_from_file_location(
        "_scoring", Path(__file__).parent / "002_scoringRubric.py"
    )
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    auto_score = _mod.auto_score

    config = LLMConfig(provider=provider_name, temperature=0.3, max_tokens=1024)
    provider = create_provider(config)

    # 가용성 확인: check_available + 실제 짧은 호출 테스트
    if not provider.check_available():
        print(f"  [{provider_name}] 사용 불가 — 건너뜀")
        return []

    # 실제 API 호출 테스트 (짧은 프롬프트)
    try:
        test_resp = provider.complete([{"role": "user", "content": "Hello"}])
        if not test_resp.answer:
            print(f"  [{provider_name}] 테스트 호출 실패 — 건너뜀")
            return []
    except (TypeError, ConnectionError, RuntimeError, OSError, ValueError) as e:
        print(f"  [{provider_name}] 테스트 호출 실패: {e} — 건너뜀")
        return []

    print(f"  [{provider_name}] model={provider.resolved_model}")
    results = []

    for qa in qa_subset:
        code = qa["stock_code"]
        question = qa["question"]
        qa_id = qa["id"]

        try:
            c = dartlab.Company(code)

            # Build context (Tier 1 pipeline)
            pipeline_ctx = run_pipeline(c, question, [])
            # Truncate context to avoid OOM on local models
            ctx_truncated = pipeline_ctx[:4000] if len(pipeline_ctx) > 4000 else pipeline_ctx
            system_truncated = SYSTEM_PROMPT_KR[:2000]
            messages = [
                {"role": "system", "content": system_truncated},
                {"role": "user", "content": f"[컨텍스트]\n{ctx_truncated}\n\n[질문]\n{question}"},
            ]

            start = time.perf_counter()
            response = provider.complete(messages)
            elapsed = time.perf_counter() - start

            answer = response.answer
            scores = auto_score(answer, qa["expected_facts"])

            results.append(
                {
                    "qa_id": qa_id,
                    "provider": provider_name,
                    "model": provider.resolved_model,
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
                    "answer_preview": answer[:200],
                }
            )
            print(f"    {qa_id}: total={scores.total} FA={scores.factual_accuracy} ({elapsed:.1f}s)")

        except Exception as e:  # noqa: BLE001 — benchmark에서 모든 provider 에러를 잡아 기록
            print(f"    {qa_id}: ERROR {type(e).__name__}: {e}")
            results.append(
                {
                    "qa_id": qa_id,
                    "provider": provider_name,
                    "error": str(e),
                }
            )

    return results


def _select_benchmark_subset(golden: list[dict], n: int = 5) -> list[dict]:
    """다양한 기업/유형 조합으로 n건 선택."""
    # 기업별로 다른 유형 선택
    selected = []
    targets = [
        ("005930", "health"),
        ("005930", "profitability"),
        ("005930", "cashflow"),
        ("000660", "health"),
        ("051910", "health"),
    ]
    for code, qtype in targets:
        for qa in golden:
            if qa["stock_code"] == code and qa["question_type"] == qtype:
                selected.append(qa)
                break
    return selected[:n]


def _aggregate_scores(results: list[dict]) -> dict:
    """provider 결과 집계."""
    scored = [r for r in results if "scores" in r]
    if not scored:
        return {"count": 0}

    dims = ["factual_accuracy", "completeness", "source_citation", "hallucination", "actionability", "total"]
    avgs = {}
    for d in dims:
        vals = [r["scores"][d] for r in scored]
        avgs[d] = round(sum(vals) / len(vals), 2)

    return {
        "count": len(scored),
        "errors": len(results) - len(scored),
        "avg_latency_s": round(sum(r.get("latency_s", 0) for r in scored) / len(scored), 2),
        "avg_scores": avgs,
    }


if __name__ == "__main__":
    exp_dir = Path(__file__).parent

    print("=" * 60)
    print("실험 003: Baseline Benchmark")
    print("=" * 60)

    # Load golden dataset
    golden_path = exp_dir / "golden_dataset.json"
    with open(golden_path, encoding="utf-8") as f:
        golden = json.load(f)

    subset = _select_benchmark_subset(golden)
    print(f"\n벤치마크 QA: {len(subset)}건")
    for qa in subset:
        print(f"  {qa['id']}: {qa['question'][:40]}...")

    # Run benchmark for each available provider
    providers = ["claude", "ollama"]
    all_results = {}

    for prov in providers:
        print(f"\n--- {prov} ---")
        results = run_benchmark(subset, prov)
        if results:
            all_results[prov] = results

    # Aggregate and compare
    print("\n" + "=" * 60)
    print("=== Provider별 결과 요약 ===")
    print("=" * 60)

    summaries = {}
    for prov, results in all_results.items():
        agg = _aggregate_scores(results)
        summaries[prov] = agg
        print(f"\n[{prov}]")
        print(f"  성공: {agg['count']}건, 실패: {agg.get('errors', 0)}건")
        if agg["count"] > 0:
            print(f"  평균 지연: {agg['avg_latency_s']}초")
            avs = agg["avg_scores"]
            print(f"  FA={avs['factual_accuracy']} CO={avs['completeness']} SC={avs['source_citation']} HA={avs['hallucination']} AC={avs['actionability']}")
            print(f"  총점 평균: {avs['total']}")

    # Provider 간 비교
    if len(summaries) >= 2:
        prov_list = list(summaries.keys())
        for i in range(len(prov_list)):
            for j in range(i + 1, len(prov_list)):
                p1, p2 = prov_list[i], prov_list[j]
                s1, s2 = summaries[p1], summaries[p2]
                if s1["count"] > 0 and s2["count"] > 0:
                    t1 = s1["avg_scores"]["total"]
                    t2 = s2["avg_scores"]["total"]
                    diff_pct = round(abs(t1 - t2) / max(t1, t2, 0.01) * 100, 1)
                    better = p1 if t1 > t2 else p2
                    print(f"\n{p1} vs {p2}: {better}가 {diff_pct}% 높음 (목표: 10%+)")

    # 저장
    output = {
        "benchmark_date": "2026-03-20",
        "qa_count": len(subset),
        "providers": {},
    }
    for prov, results in all_results.items():
        output["providers"][prov] = {
            "results": results,
            "summary": summaries.get(prov, {}),
        }

    output_path = exp_dir / "baseline_benchmark.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n저장: {output_path}")
