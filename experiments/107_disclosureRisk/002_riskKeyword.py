"""
실험 ID: 107-002
실험명: 리스크 키워드 신규 등장 시그널 유효성 검증

목적:
- 횡령/배임/과징금/손해배상/소송이 올해 처음 공시에 등장한 종목이
- 기존 audit riskLevel "안전"인 비율 측정 → 기존 축이 못 잡는 선행 위험 확인

가설:
1. 횡령/배임/과징금 신규 등장 종목은 audit "안전" 비율 60% 이상 → 선행 지표
2. 소송은 노이즈 섞임 → 횡령/배임/과징금이 더 정밀한 시그널

방법:
1. 최신(2024→2025) preview에서 키워드 매칭 종목
2. 이전(2023→2024)에 없던 종목만 = "신규 등장"
3. 신규 등장 vs audit riskLevel 교차
4. 신규 등장 vs profitability grade 교차

결과 (실험 후 작성):
| 키워드 | 신규 등장 | audit 안전 | 안전% | 적자/저수익% | 판정 |
|--------|----------|-----------|------|-----------|------|
| 횡령 | 21 | 15 | 71.4% | 66.7% | 유효 |
| 배임 | 22 | 15 | 68.2% | 68.2% | 유효 |
| 과징금 | 29 | 19 | 65.5% | 48.3% | 유효 |
| 손해배상 | 52 | 30 | 57.7% | 53.8% | 유효 |
| 소송 | 151 | 108 | 71.5% | 40.4% | 유효 |
| 횡령+배임+과징금 합산 | 49 | 33 | 67.3% | - | 유효 |

결론:
- 가설1 채택: 횡령/배임/과징금 신규 등장의 audit "안전" 비율 65~71% → 기존 감사 축이 완전히 못 잡는 위험
- 가설2 부분 기각: 소송도 71.5%로 유효 — 노이즈가 많을 줄 알았지만 변별력 있음
- **핵심 발견**: 횡령/배임 신규 등장 기업의 적자/저수익 비율 67~68% → 수익성 악화 동반
- 흡수 권장: 횡령+배임+과징금 합산 49종목을 "심각 리스크", 소송/손해배상은 "주의"로 차등 반영
- "신규 등장" 개념이 단순 키워드 검색보다 훨씬 정밀함 — 이전 기간 대비 차분이 핵심

실험일: 2026-04-01
"""
from __future__ import annotations

import gc
import json
from pathlib import Path

import polars as pl

CHANGES_PATH = Path("data/dart/scan/changes.parquet")

_KEYWORDS = {
    "횡령": "횡령",
    "배임": "배임",
    "과징금": "과징금",
    "손해배상": "손해배상",
    "소송": "소송",
}


def _keywordStocks(changes: pl.DataFrame, keyword: str) -> set[str]:
    """preview에서 키워드가 있는 종목 set."""
    return set(
        changes.filter(pl.col("preview").str.contains(keyword))["stockCode"]
        .unique()
        .to_list()
    )


def main():
    print("=== 107-002: 리스크 키워드 신규 등장 ===\n")

    df = pl.read_parquet(str(CHANGES_PATH))

    latest = df.filter((pl.col("fromPeriod") == "2024") & (pl.col("toPeriod") == "2025"))
    prev = df.filter((pl.col("fromPeriod") == "2023") & (pl.col("toPeriod") == "2024"))
    del df

    print(f"최신 기간: {latest.height:,}행, {latest['stockCode'].n_unique()}종목")
    print(f"이전 기간: {prev.height:,}행, {prev['stockCode'].n_unique()}종목\n")

    # 기존 축 로드
    from dartlab.scan import Scan
    s = Scan()
    audit = s("audit")
    prof = s("profitability")
    # 컬럼명 정규화
    if "종목코드" in prof.columns and "stockCode" not in prof.columns:
        prof = prof.rename({"종목코드": "stockCode"})
    if "등급" in prof.columns and "grade" not in prof.columns:
        prof = prof.rename({"등급": "grade"})
    gc.collect()

    results = {}

    for label, kw in _KEYWORDS.items():
        now_stocks = _keywordStocks(latest, kw)
        prev_stocks = _keywordStocks(prev, kw)
        new_stocks = now_stocks - prev_stocks

        print(f"--- {label} ---")
        print(f"  현재: {len(now_stocks)}, 이전: {len(prev_stocks)}, 신규: {len(new_stocks)}")

        if not new_stocks:
            results[label] = {"new": 0, "verdict": "데이터 없음"}
            print()
            continue

        # audit 교차
        new_df = pl.DataFrame({"stockCode": list(new_stocks)})
        merged_audit = new_df.join(
            audit.select(["stockCode", "riskLevel"]), on="stockCode", how="left"
        )
        safe = merged_audit.filter(pl.col("riskLevel") == "안전").height
        safe_pct = round(safe / len(new_stocks) * 100, 1)

        # profitability 교차
        merged_prof = new_df.join(
            prof.select(["stockCode", "grade"]), on="stockCode", how="left"
        )
        loss = merged_prof.filter(pl.col("grade").is_in(["적자", "저수익"])).height
        loss_pct = round(loss / len(new_stocks) * 100, 1)

        # audit 등급 분포
        audit_dist = {}
        for r in merged_audit["riskLevel"].drop_nulls().value_counts().to_dicts():
            audit_dist[r["riskLevel"]] = r["count"]

        verdict = "유효" if safe >= 10 else ("소규모유효" if safe >= 5 else "미달")

        results[label] = {
            "new": len(new_stocks),
            "auditSafe": safe,
            "auditSafePct": safe_pct,
            "auditDist": audit_dist,
            "profLossPct": loss_pct,
            "verdict": verdict,
        }

        print(f"  audit 안전: {safe}건 ({safe_pct}%)")
        print(f"  audit 분포: {audit_dist}")
        print(f"  profitability 적자/저수익: {loss_pct}%")
        print(f"  판정: {verdict}")
        print()

    # 복합 키워드: 횡령+배임+과징금 합산
    severe_kws = ["횡령", "배임", "과징금"]
    severe_now = set()
    severe_prev = set()
    for kw in severe_kws:
        severe_now |= _keywordStocks(latest, kw)
        severe_prev |= _keywordStocks(prev, kw)
    severe_new = severe_now - severe_prev

    if severe_new:
        new_df = pl.DataFrame({"stockCode": list(severe_new)})
        merged = new_df.join(audit.select(["stockCode", "riskLevel"]), on="stockCode", how="left")
        safe = merged.filter(pl.col("riskLevel") == "안전").height
        results["횡령+배임+과징금_합산"] = {
            "new": len(severe_new),
            "auditSafe": safe,
            "auditSafePct": round(safe / len(severe_new) * 100, 1),
            "verdict": "유효" if safe >= 10 else "미달",
        }
        print(f"--- 횡령+배임+과징금 합산 ---")
        print(f"  신규: {len(severe_new)}, audit 안전: {safe} ({results['횡령+배임+과징금_합산']['auditSafePct']}%)")
        print(f"  판정: {results['횡령+배임+과징금_합산']['verdict']}")

    outPath = Path("experiments/107_disclosureRisk/002_result.json")
    outPath.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\n[SAVED] {outPath}")


if __name__ == "__main__":
    main()
