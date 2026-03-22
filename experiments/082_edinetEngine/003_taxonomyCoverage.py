"""실험 ID: 003
실험명: EDINET mapper × edinet-xbrl taxonomy 커버리지 측정

목적:
- edinet-xbrl 레포의 FSA Taxonomy (131개 element)에 대해 우리 mapper의 매핑률 측정
- CORE_MAP + ID_SYNONYMS + accountMappings.json 파이프라인의 실전 커버리지 확인
- 매핑 누락 element 식별

가설:
1. 재무제표 element (financial_statement 카테고리)는 90%+ 매핑률
2. 요약 element (summary 카테고리)는 prefix가 길어 accountMappings.json 의존
3. DEI element (edinet_code 등)는 재무 매핑 범위 밖

방법:
1. edinet-xbrl taxonomy.json 로드 (131개 element)
2. 각 element를 EdinetMapper.map()에 통과
3. 카테고리별/회계기준별 매핑률 집계
4. 미매핑 element 목록 출력

결과:
- 총 131개 중 72개 매핑 (55.0%)
  - DEI 15개 제외 시: 116개 중 72개 → 62.1%
- 카테고리별:
  | 카테고리               | 매핑   | 비율   |
  |----------------------|--------|--------|
  | dei                  | 0/15   | 0.0%   | 의도적 제외 (비재무)
  | financial_statement  | 33/40  | 82.5%  |
  | financial_stmt_ifrs  | 5/15   | 33.3%  |
  | summary              | 7/14   | 50.0%  |
  | summary_ifrs         | 4/15   | 26.7%  |
  | summary_us_gaap      | 23/32  | 71.9%  |
- 미매핑 59개 주요 원인:
  - DEI 15개: edinet_code, security_code, company_name 등 비재무 메타
  - IFRS 전용 prefix (jpigp_cor:): Revenue2IFRS, AssetsIFRS, EquityIFRS 등 10개
    → _PREFIXES에 jpigp_cor: 있지만 suffix에 "IFRS" 포함되어 CORE_MAP miss
  - 요약 전용 suffix: SummaryOfBusinessResults 계열 중 일본어 계정명이 동의어 테이블 미등록
  - ratio 계열: equity_ratio, pe_ratio, roe, payout_ratio → CORE_MAP 범위 밖

결론:
- 가설 1 부분 채택: financial_statement J-GAAP 82.5% (90%에 미달)
- 가설 2 채택: summary 카테고리는 accountMappings.json 시드 의존 확인
- 가설 3 채택: DEI는 의도적 매핑 제외 대상
- IFRS 전용 element (jpigp_cor:*IFRS)는 suffix "IFRS" 제거 로직 추가하면 +10개 매핑 가능
- ratio 계열 (equity_ratio, roe, pe_ratio)은 CORE_MAP 확장 대상
- 실제 EDINET XBRL 데이터 수집 후 매핑률 재측정 예정 (실험 006)

실험일: 2026-03-22
"""

import json
import sys
from collections import Counter
from pathlib import Path

# dartlab import
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from dartlab.engines.company.edinet.finance.mapper import EdinetMapper


def main():
    # ── edinet-xbrl taxonomy.json 로드 ──
    taxonomy_path = Path.home() / "edinet_xbrl_taxonomy.json"
    if not taxonomy_path.exists():
        print(f"taxonomy.json not found at {taxonomy_path}")
        print("먼저 GitHub에서 다운로드하세요:")
        print("  gh api repos/axioradev/edinet-xbrl/contents/src/edinet_xbrl/taxonomy.json "
              "-q '.content' | base64 -d > ~/edinet_xbrl_taxonomy.json")
        return

    with open(taxonomy_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    field_map = data.get("field_map", {})
    meta = data.get("_meta", {})
    print(f"=== edinet-xbrl taxonomy ===")
    print(f"출처: FSA EDINET Taxonomy {meta.get('taxonomy_year', '?')}")
    print(f"총 element: {len(field_map)}개")
    print(f"정의 field: {meta.get('fields_defined', '?')}개")
    print()

    # ── 매핑 테스트 ──
    results = []
    for element_id, info in field_map.items():
        label_jp = info.get("label_jp", "")
        category = info.get("category", "unknown")
        standard = info.get("standard", "unknown")
        field = info.get("field", "")

        snake_id = EdinetMapper.map(element_id, label_jp)
        results.append({
            "element_id": element_id,
            "label_jp": label_jp,
            "category": category,
            "standard": standard,
            "field": field,
            "mapped_to": snake_id,
            "is_mapped": snake_id is not None,
        })

    # ── 전체 집계 ──
    total = len(results)
    mapped = sum(1 for r in results if r["is_mapped"])
    print(f"=== 전체 매핑률 ===")
    print(f"총: {total}개, 매핑: {mapped}개, 미매핑: {total - mapped}개")
    print(f"매핑률: {mapped / total * 100:.1f}%")
    print()

    # DEI 제외
    non_dei = [r for r in results if r["category"] != "dei"]
    non_dei_mapped = sum(1 for r in non_dei if r["is_mapped"])
    print(f"DEI 제외: {len(non_dei)}개 중 {non_dei_mapped}개 매핑 "
          f"({non_dei_mapped / len(non_dei) * 100:.1f}%)")
    print()

    # ── 카테고리별 집계 ──
    categories = sorted(set(r["category"] for r in results))
    print(f"=== 카테고리별 매핑률 ===")
    for cat in categories:
        cat_results = [r for r in results if r["category"] == cat]
        cat_mapped = sum(1 for r in cat_results if r["is_mapped"])
        rate = cat_mapped / len(cat_results) * 100 if cat_results else 0
        print(f"  {cat:30s}: {cat_mapped}/{len(cat_results)} ({rate:.1f}%)")
    print()

    # ── 미매핑 element 목록 ──
    unmapped = [r for r in results if not r["is_mapped"]]
    print(f"=== 미매핑 element ({len(unmapped)}개) ===")
    for r in unmapped:
        print(f"  {r['element_id'][:70]:70s} | {r['label_jp']:20s} | {r['category']}")
    print()

    # ── field별 매핑 현황 ──
    fields = sorted(set(r["field"] for r in results))
    print(f"=== field별 매핑 현황 ({len(fields)}개 field) ===")
    for field in fields:
        field_results = [r for r in results if r["field"] == field]
        field_mapped = sum(1 for r in field_results if r["is_mapped"])
        if field_mapped < len(field_results):
            print(f"  {field:30s}: {field_mapped}/{len(field_results)} "
                  f"{'⚠ 누락' if field_mapped == 0 else '△ 부분'}")


if __name__ == "__main__":
    main()
