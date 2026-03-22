"""
실험 ID: 005
실험명: Token Budget Profile — 현재 context 모듈별 토큰 분포 측정

목적:
- 현재 tiered context의 각 모듈(IS, BS, CF, ratios, report_*, pipeline)이 차지하는 토큰 비중 파악
- 어디에 토큰이 낭비되고 있는지, 어디를 압축해야 하는지 데이터 기반 판단

가설:
1. 전체 토큰의 50%+ 가 financeEngine(IS/BS/CF)에 집중되어 있다
2. reportEngine 섹션들은 각각 작지만 합치면 30%+ 차지
3. pipeline 자동 분석 결과는 전체의 10% 미만으로 효율적이다
4. 기업별 편차가 크다 (금융업 KB금융 vs 제조업 삼성전자)

방법:
1. 5개사 × 3 tier(skeleton/focused/full) 조합별 context 생성
2. 모듈별 토큰 수 측정
3. 비중 계산 + 기업별 편차 분석

결과 (5개사 종합, 종합 분석 질문):
- Tier별 평균 토큰:
  - skeleton: 100 tok (91~103)
  - focused: 1,490 tok (1,271~1,566)
  - full: 2,251 tok (1,865~2,391)
- full 모듈별 평균 비중 (5개사):
  - BS: 230 tok (10.2%)
  - IS: 186 tok (8.3%)
  - report_employee: 107 tok (4.8%)
  - report_majorHolder: 100 tok (4.4%)
  - report_audit: 89 tok (4.0%)
  - CF: 82 tok (3.6%)
  - report_dividend: 80 tok (3.6%)
  - header: 24 tok (1.1%)
  - report_executive: 22 tok (1.0%)
- 카테고리별 비중: financeEngine 21.8%, reportEngine 17.8%, pipeline 21.5%
- 기업별 편차: KB금융 1,865tok(최소) ~ 카카오 2,391tok(최대)

결론:
- 가설 1 기각: financeEngine이 21.8%로 50% 미만
- 가설 2 부분 채택: reportEngine 17.8% (가설 30% 미달)
- 가설 3 채택: pipeline 21.5%로 효율적
- 가설 4 채택: KB금융(1,865) vs 카카오(2,391) — 528tok 차이 (28% 편차)
- 핵심 발견: full이 평균 2,251tok으로 예상 14k보다 훨씬 작음
  → focused(1,490)와 full(2,251)의 차이가 ~760tok밖에 안 됨
  → skeleton(100tok)은 정보 밀도를 크게 높일 여지 있음

실험일: 2026-03-20
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))


def _estimate_tokens(text: str) -> int:
    """간이 토큰 추정 (한국어: ~1.5 char/token, 영어: ~4 char/token)."""
    korean_chars = sum(1 for c in text if "\uac00" <= c <= "\ud7a3")
    other_chars = len(text) - korean_chars
    return int(korean_chars / 1.5 + other_chars / 4)


COMPANIES = [
    ("005930", "삼성전자"),
    ("000660", "SK하이닉스"),
    ("105560", "KB금융"),
    ("051910", "LG화학"),
    ("035720", "카카오"),
]

# 대표 질문 (종합 분석 — 모든 모듈 활성화)
TEST_QUESTION = "이 기업에 대해 종합적으로 분석해주세요."


def profile_full_context(company, question: str) -> dict:
    """full context의 모듈별 토큰 분포."""
    from dartlab.engines.ai.context import build_context_by_module
    from dartlab.engines.ai.pipeline import run_pipeline

    modules, included, header = build_context_by_module(
        company, question, compact=False
    )

    result = {"header": _estimate_tokens(header)}
    total = result["header"]

    for name, text in modules.items():
        tokens = _estimate_tokens(text)
        result[name] = tokens
        total += tokens

    # pipeline 결과
    pipeline_text = run_pipeline(company, question, included)
    if pipeline_text:
        pipeline_tokens = _estimate_tokens(pipeline_text)
        result["_pipeline"] = pipeline_tokens
        total += pipeline_tokens

    result["_total"] = total
    result["_module_count"] = len(modules)
    result["_included"] = included

    return result


def profile_skeleton_context(company) -> dict:
    """skeleton context 토큰."""
    from dartlab.engines.ai.context import build_context_skeleton

    text, included = build_context_skeleton(company)
    return {
        "_total": _estimate_tokens(text),
        "_included": included,
        "_text_length": len(text),
    }


def profile_focused_context(company, question: str) -> dict:
    """focused context의 모듈별 토큰 분포."""
    from dartlab.engines.ai.context import build_context_focused

    modules, included, header = build_context_focused(company, question)

    result = {"header": _estimate_tokens(header)}
    total = result["header"]

    for name, text in modules.items():
        tokens = _estimate_tokens(text)
        result[name] = tokens
        total += tokens

    result["_total"] = total
    result["_included"] = included

    return result


if __name__ == "__main__":
    import dartlab

    print("=" * 70)
    print("실험 005: Token Budget Profile")
    print("=" * 70)

    all_profiles = {}

    for code, name in COMPANIES:
        print(f"\n{'─' * 50}")
        print(f"[{code}] {name}")
        print(f"{'─' * 50}")

        c = dartlab.Company(code)

        # Skeleton
        sk = profile_skeleton_context(c)
        print(f"\n  skeleton: {sk['_total']} tokens (text {sk['_text_length']} chars)")

        # Focused
        fo = profile_focused_context(c, TEST_QUESTION)
        print(f"  focused:  {fo['_total']} tokens")
        fo_modules = {k: v for k, v in fo.items() if not k.startswith("_")}
        for mod, tok in sorted(fo_modules.items(), key=lambda x: -x[1]):
            pct = round(tok / max(fo["_total"], 1) * 100, 1)
            print(f"    {mod:>20}: {tok:>5} tok ({pct}%)")

        # Full
        fu = profile_full_context(c, TEST_QUESTION)
        print(f"  full:     {fu['_total']} tokens")
        fu_modules = {k: v for k, v in fu.items() if not k.startswith("_")}
        for mod, tok in sorted(fu_modules.items(), key=lambda x: -x[1]):
            pct = round(tok / max(fu["_total"], 1) * 100, 1)
            print(f"    {mod:>20}: {tok:>5} tok ({pct}%)")

        all_profiles[code] = {
            "name": name,
            "skeleton": sk,
            "focused": fo,
            "full": fu,
        }

    # 종합 분석
    print("\n" + "=" * 70)
    print("=== 종합 분석 ===")
    print("=" * 70)

    # Tier별 평균 토큰
    for tier in ["skeleton", "focused", "full"]:
        totals = [p[tier]["_total"] for p in all_profiles.values()]
        avg = round(sum(totals) / len(totals))
        mn = min(totals)
        mx = max(totals)
        print(f"\n  {tier:>8}: 평균 {avg} tok (min={mn}, max={mx})")

    # Full context 모듈별 평균 비중
    print("\n  [full context 모듈별 평균 비중]")
    all_module_tokens = {}
    all_totals = []
    for p in all_profiles.values():
        fu = p["full"]
        total = fu["_total"]
        all_totals.append(total)
        for k, v in fu.items():
            if not k.startswith("_"):
                all_module_tokens.setdefault(k, []).append(v)

    avg_total = sum(all_totals) / len(all_totals)
    for mod, vals in sorted(all_module_tokens.items(), key=lambda x: -sum(x[1])):
        avg_tok = round(sum(vals) / len(vals))
        pct = round(avg_tok / max(avg_total, 1) * 100, 1)
        print(f"    {mod:>20}: {avg_tok:>5} tok ({pct}%)")

    # Finance vs Report vs Pipeline 비중
    print("\n  [카테고리별 비중]")
    finance_keys = {"IS", "BS", "CF", "CIS", "ratios"}
    report_keys = {"report_dividend", "report_employee", "report_majorHolder", "report_executive", "report_audit"}

    for cat, keys in [("financeEngine", finance_keys), ("reportEngine", report_keys)]:
        cat_tokens = []
        for p in all_profiles.values():
            fu = p["full"]
            total = fu["_total"]
            cat_sum = sum(fu.get(k, 0) for k in keys)
            cat_tokens.append(round(cat_sum / max(total, 1) * 100, 1))
        avg_pct = round(sum(cat_tokens) / len(cat_tokens), 1)
        print(f"    {cat:>15}: {avg_pct}%")

    pipeline_tokens = []
    for p in all_profiles.values():
        fu = p["full"]
        total = fu["_total"]
        pt = fu.get("_pipeline", 0)
        pipeline_tokens.append(round(pt / max(total, 1) * 100, 1))
    avg_pipeline = round(sum(pipeline_tokens) / len(pipeline_tokens), 1)
    print(f"    {'pipeline':>15}: {avg_pipeline}%")

    # 기업별 편차
    print("\n  [기업별 full context 토큰]")
    for code, name in COMPANIES:
        total = all_profiles[code]["full"]["_total"]
        print(f"    {name:>10}: {total:>6} tok")
