"""실험 ID: 002
실험명: DART/EDGAR ↔ EDINET XBRL 계정 공유분 분석

목적:
- DART(K-IFRS)와 EDGAR(US-GAAP)의 기존 매핑에서 EDINET(J-GAAP/IFRS)에
  재사용 가능한 계정이 얼마나 되는지 측정
- IFRS 공유 계정(ifrs-full_ prefix)의 교집합 파악
- EDINET 초기 CORE_MAP 시드의 커버리지 추정

가설:
1. DART K-IFRS와 EDINET IFRS는 ifrs-full_ prefix 계정을 공유하여
   영문 element 기준 50% 이상 재사용 가능
2. EDGAR US-GAAP ↔ EDINET US-GAAP 공유 기업은 소수지만
   매핑 패턴은 동일하게 적용 가능
3. EDINET CORE_MAP 28개 시드가 실제 주요 계정의 80% 이상 커버

방법:
1. DART accountMappings.json에서 ifrs-full_ 기반 계정 추출
2. EDGAR standardAccounts.json에서 공통 snakeId 추출
3. EDINET CORE_MAP과 대조하여 커버리지 측정
4. 누락된 주요 계정 후보 식별

결과:
- DART accountMappings: 34,249개 (한글 33,478 + 영문 771), 5,539 고유 snakeId
- EDGAR standardAccounts: 188개 계정, 187 snakeId, 353 공통 태그
- DART↔EDGAR snakeId 교집합: 46개 (예상보다 적음 — 네이밍 차이)
- EDINET CORE_MAP: 40항목 → 28 고유 snakeId
  - DART 존재: 21개 (75%)
  - EDGAR 존재: 6개 (21%)
  - EDINET 고유: 7개 (ordinary_income, extraordinary_income/loss 등 J-GAAP 고유)
- 핵심 15개 재무 snakeId: DART 한글 매핑 존재 (일본어 대응 가능)
- DART 상위 30 빈출 snakeId 중 EDINET CORE_MAP 누락: 30개 전부 누락
  → CORE_MAP 확장 필요 (tangible_assets, income_taxes, retained_earnings 등)

결론:
- 가설 1 기각: ifrs-full_ prefix 공유는 영문 키 771개 중 1개뿐.
  DART는 한글 위주 매핑이라 영문 IFRS element 공유 효과 미미.
  → EDINET은 일본어 계정명 기반 독자 학습 필요.
- 가설 2 부분 채택: EDGAR US-GAAP 매핑 패턴은 적용 가능하나
  snakeId 네이밍 차이 (46개만 공유)로 alias 레이어 필요.
- 가설 3 기각: CORE_MAP 28개 snakeId는 DART 상위 30에 하나도 없음.
  → tangible_assets, retained_earnings, income_taxes 등 주요 계정 추가 필수.
- **즉시 조치**: EDINET CORE_MAP에 DART 빈출 상위 계정 추가

실험일: 2026-03-22
"""

from __future__ import annotations

import json
from pathlib import Path

# ── 경로 ──
ROOT = Path(__file__).resolve().parents[2] / "src" / "dartlab" / "engines"

DART_MAPPINGS = ROOT / "dart" / "finance" / "mapperData" / "accountMappings.json"
EDGAR_STANDARD = ROOT / "edgar" / "finance" / "mapperData" / "standardAccounts.json"
EDINET_MAPPER = ROOT / "edinet" / "finance" / "mapper.py"


def analyze():
    # ── 1. DART 매핑 분석 ──
    with open(DART_MAPPINGS, encoding="utf-8") as f:
        dart_raw = json.load(f)

    dart_map: dict[str, str] = dart_raw.get("mappings", dart_raw)
    total_dart = len(dart_map)

    # 한글 계정명 vs 영문 계정명
    kor_keys = [k for k in dart_map if any(ord(c) > 0x1100 for c in k)]
    eng_keys = [k for k in dart_map if not any(ord(c) > 0x1100 for c in k)]

    # snakeId 종류
    dart_snakeIds = set(dart_map.values())

    print("=" * 60)
    print("1. DART accountMappings.json 분석")
    print(f"   총 매핑: {total_dart:,}개")
    print(f"   한글 키: {len(kor_keys):,}개")
    print(f"   영문 키: {len(eng_keys):,}개")
    print(f"   고유 snakeId: {len(dart_snakeIds)}개")

    # ifrs-full_ 관련 영문 키
    ifrs_keys = [k for k in eng_keys if k.lower().startswith("ifrs")]
    print(f"   ifrs 관련 영문 키: {len(ifrs_keys)}개")

    # ── 2. EDGAR 매핑 분석 ──
    with open(EDGAR_STANDARD, encoding="utf-8") as f:
        edgar_data = json.load(f)

    edgar_accounts = edgar_data.get("accounts", [])
    edgar_snakeIds = {a["snakeId"] for a in edgar_accounts}
    edgar_tags = set()
    for a in edgar_accounts:
        for tag in a.get("commonTags", []):
            edgar_tags.add(tag)

    print(f"\n2. EDGAR standardAccounts.json 분석")
    print(f"   계정 수: {len(edgar_accounts)}개")
    print(f"   고유 snakeId: {len(edgar_snakeIds)}개")
    print(f"   공통 태그: {len(edgar_tags)}개")

    # ── 3. DART ↔ EDGAR snakeId 교집합 ──
    shared_snakeIds = dart_snakeIds & edgar_snakeIds
    print(f"\n3. DART ↔ EDGAR snakeId 교집합")
    print(f"   공유 snakeId: {len(shared_snakeIds)}개")
    print(f"   DART 전용: {len(dart_snakeIds - edgar_snakeIds)}개")
    print(f"   EDGAR 전용: {len(edgar_snakeIds - dart_snakeIds)}개")

    # ── 4. EDINET CORE_MAP 커버리지 ──
    from dartlab.engines.company.edinet.finance.mapper import CORE_MAP

    edinet_snakeIds = set(CORE_MAP.values())
    covered_by_dart = edinet_snakeIds & dart_snakeIds
    covered_by_edgar = edinet_snakeIds & edgar_snakeIds

    print(f"\n4. EDINET CORE_MAP 분석")
    print(f"   CORE_MAP 항목: {len(CORE_MAP)}개")
    print(f"   고유 snakeId: {len(edinet_snakeIds)}개")
    print(f"   DART에도 존재하는 snakeId: {len(covered_by_dart)}개")
    print(f"   EDGAR에도 존재하는 snakeId: {len(covered_by_edgar)}개")

    # DART/EDGAR 양쪽에 없는 EDINET 고유 snakeId
    edinet_only = edinet_snakeIds - dart_snakeIds - edgar_snakeIds
    print(f"   EDINET 고유 (DART/EDGAR에 없음): {len(edinet_only)}개")
    if edinet_only:
        for sid in sorted(edinet_only):
            print(f"     - {sid}")

    # ── 5. DART에서 EDINET으로 이식 가능한 IFRS 계정 ──
    # K-IFRS(한국) = IFRS(일본)이므로 한글→일본어 매핑 후보
    # 핵심 재무제표 snakeId 기준으로 DART 한글명 수집
    core_financial_snakeIds = [
        "revenue", "operating_profit", "net_profit", "total_assets",
        "current_assets", "current_liabilities", "noncurrent_assets",
        "noncurrent_liabilities", "cash_and_cash_equivalents",
        "cost_of_sales", "selling_and_administrative_expenses",
        "operating_cashflow", "investing_cashflow",
        "owners_of_parent_equity", "basic_earnings_per_share",
    ]

    print(f"\n5. 핵심 재무 snakeId — DART 한글명 → EDINET 일본어명 대응")
    for sid in core_financial_snakeIds:
        dart_names = [k for k, v in dart_map.items() if v == sid and any(ord(c) > 0x1100 for c in k)]
        dart_names_short = dart_names[:3]
        print(f"   {sid}: DART 한글명 {len(dart_names)}개 — {dart_names_short}")

    # ── 6. 주요 snakeId 중 EDINET CORE_MAP에 누락된 것 ──
    # 상위 30개 빈출 snakeId (DART 기준)
    from collections import Counter
    dart_freq = Counter(dart_map.values())
    top30 = [sid for sid, _ in dart_freq.most_common(30)]

    missing = [sid for sid in top30 if sid not in edinet_snakeIds]
    print(f"\n6. DART 상위 30 snakeId 중 EDINET CORE_MAP 누락")
    print(f"   누락 {len(missing)}개:")
    for sid in missing:
        print(f"     - {sid} (DART {dart_freq[sid]}건)")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    analyze()
