"""
실험 ID: 006
실험명: 003 발견 오매핑의 원인 추적 — 매핑 경로 역추적

목적:
- 003에서 "오매핑"으로 판단한 항목들이 실제로 매핑 오류인지, 표준계정에 의도 매핑인지 확인
- 각 의심 항목에 대해 mapper.map()의 어떤 단계에서 매핑되었는지 추적
- sga_expenses, trade_and_other_current_receivables 누락 원인 확인

방법:
1. mapper.py의 매핑 파이프라인 단계별 추적 (어디서 매핑되는가)
2. accountMappings.json에서 직접 검색 (표준계정에 있는가)
3. 003 의심 항목별 원인 분류

결과 (2026-03-09 실행):

A) 003 "오매핑" 재판정

1. net_income에 "영업에서 창출된 현금흐름" 혼입
   → 실제로는 'cash_flows_from_business'로 매핑됨 (오매핑 아님!)
   → 003 실험이 sj_div 구분 없이 전체를 카운트해서 잘못 집계한 것
   → BUT: "소계"→net_income, "중단영업"→net_income은 accountMappings.json에 실제 등록됨
   → 이것은 eddmpython 학습 과정에서 IS의 소계/중단영업이 net_income으로 학습된 것

2. income_tax_expense에 CF/OCI 항목 혼입
   → "법인세의 납부" → income_taxes → SNAKE_ALIASES → income_tax_expense
   → "법인세효과" → income_taxes → income_tax_expense
   → "당기손익으로 재분류되지 않는 항목의 법인세" → income_taxes → income_tax_expense
   → 원인: accountMappings.json이 재무제표 종류(IS/CF/OCI) 구분 없이 학습됨
   → SNAKE_ALIASES의 income_taxes → income_tax_expense가 IS/CF 모두 합침

3. ppe에 CF 항목 혼입
   → "시설장치의 처분" → tangible_assets → SNAKE_ALIASES → ppe
   → "장기투자자산의 취득" → tangible_assets → ppe (이건 아예 다른 자산!)
   → 원인: accountMappings.json에서 "장기투자자산의취득"이 tangible_assets로 학습됨 (오학습)
   → SNAKE_ALIASES의 tangible_assets → ppe도 과도한 합산

4. bonds 혼입
   → 전환사채 → convertible_debentures (별도 snakeId, bonds 아님!)
   → 신주인수권부사채 → bond_with_warrants (별도 snakeId)
   → 교환사채 → convertible_bonds (별도 snakeId)
   → "사채발행" → bonds, "전환사채 보통주 전환" → bonds, "주식발행비의 지급" → bonds
   → 원인: 사채 자체는 정상이지만 CF항목(발행/전환/상환)이 같은 snakeId로 학습됨

5. retained_earnings에 "자본잉여금" 혼입
   → "자본잉여금" → capital_surplus (별도 snakeId, retained_earnings 아님!)
   → 003 실험의 오집계 (sj_div 무시로 SCE항목과 BS항목이 섞임)
   → "회계정책변경효과" → retained_earnings는 의도적 매핑 (SCE에서 이익잉여금 조정 항목)

B) sga_expenses 누락 원인
   → accountMappings.json에는 "판매비와관리비" → "selling_and_administrative_expenses" 존재!
   → mapper.map()도 정상 동작 (판관비/판매비/판매비및관리비 모두 매핑됨)
   → 002 실험에서 KEY_ACCOUNTS에 "sga_expenses"로 검색했는데, 실제 snakeId는
     "selling_and_administrative_expenses"임
   → **snakeId 이름 불일치가 원인 (매핑 자체는 정상)**

C) trade_and_other_current_receivables 누락 원인
   → "매출채권" → trade_and_other_receivables (current 없음)
   → "매출채권및기타채권" → trade_and_other_receivables (current 없음)
   → "매출채권및기타유동채권" → trade_and_other_current_receivables (이것만 current 있음)
   → 대부분 종목이 "매출채권" 또는 "매출채권및기타채권"을 사용
   → **"매출채권"이 trade_and_other_receivables로 매핑되지 trade_and_other_current_receivables가 아님**
   → 002에서 검색한 snakeId와 실제 매핑 snakeId가 다름

결론:
003에서 "오매핑"으로 판단한 대부분은 잘못된 진단이었음

실제 문제 분류:
[A] 003 실험 설계 결함 (sj_div 미구분)
    - net_income에 "영업에서 창출된 현금흐름" → 실제로는 cash_flows_from_business (오집계)
    - bonds에 "전환사채" → 실제로는 convertible_debentures (오집계)
    - retained_earnings에 "자본잉여금" → 실제로는 capital_surplus (오집계)

[B] 002 실험의 snakeId 이름 불일치
    - sga_expenses → 실제 snakeId는 selling_and_administrative_expenses
    - trade_and_other_current_receivables → 실제 snakeId는 trade_and_other_receivables

[C] accountMappings.json의 실제 문제 (eddmpython 학습 결과의 한계)
    - "소계" → net_income (IS 소계가 순이익으로 학습됨)
    - "중단영업" → net_income (의미상 관련은 있으나 과대매핑)
    - "법인세의 납부" → income_taxes (CF항목인데 IS 계정과 동일 snakeId)
    - "법인세효과" → income_taxes (OCI항목인데 IS 계정과 동일 snakeId)
    - "사채발행" → bonds (CF항목인데 BS 계정과 동일 snakeId)
    - "장기투자자산의취득" → tangible_assets (장기투자≠유형자산, 오학습)
    → 이들은 모두 **sj_div 미구분 학습의 결과**로, 치명적 수치 오염은 아님
    → dartlab pivot.py는 sj_div별로 데이터를 분리하므로 실제 사용 시
      BS의 ppe에 CF의 "시설장치 처분"이 합산되진 않음

[D] SNAKE_ALIASES 과도한 합산
    - tangible_assets → ppe (하위 CF항목까지 끌어옴)
    - income_taxes → income_tax_expense (CF/OCI까지 포함)

실험일: 2026-03-09
"""

import sys
import json
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))
from dartlab.engines.dart.finance.mapper import (
    AccountMapper, CORE_MAP, ID_SYNONYMS, ACCOUNT_NAME_SYNONYMS,
    _PREFIX_RE, _PAREN_RE
)
from dartlab.engines.dart.finance.pivot import SNAKE_ALIASES

mapper = AccountMapper.get()

MAPPINGS_PATH = Path(__file__).resolve().parents[2] / "mapperData" / "accountMappings.json"
with open(MAPPINGS_PATH, encoding="utf-8") as f:
    allMappings = json.load(f)["mappings"]

def traceMapping(accountId, accountNm):
    """mapper.map()의 각 단계를 추적하여 어디서 매핑되었는지 반환"""
    steps = []

    stripped = _PREFIX_RE.sub("", accountId) if accountId else ""
    normalizedId = ID_SYNONYMS.get(stripped, stripped)
    if stripped != normalizedId:
        steps.append(f"ID_SYNONYMS: '{stripped}' → '{normalizedId}'")

    normalizedNm = ACCOUNT_NAME_SYNONYMS.get(accountNm, accountNm) if accountNm else ""
    if accountNm != normalizedNm:
        steps.append(f"ACCOUNT_NAME_SYNONYMS: '{accountNm}' → '{normalizedNm}'")

    if normalizedId in CORE_MAP:
        snakeId = CORE_MAP[normalizedId]
        finalId = SNAKE_ALIASES.get(snakeId, snakeId)
        steps.append(f"CORE_MAP[id]: '{normalizedId}' → '{snakeId}'")
        if snakeId != finalId:
            steps.append(f"SNAKE_ALIASES: '{snakeId}' → '{finalId}'")
        return finalId, steps

    if normalizedNm in CORE_MAP:
        snakeId = CORE_MAP[normalizedNm]
        finalId = SNAKE_ALIASES.get(snakeId, snakeId)
        steps.append(f"CORE_MAP[nm]: '{normalizedNm}' → '{snakeId}'")
        if snakeId != finalId:
            steps.append(f"SNAKE_ALIASES: '{snakeId}' → '{finalId}'")
        return finalId, steps

    if normalizedId and normalizedId in allMappings:
        snakeId = allMappings[normalizedId]
        finalId = SNAKE_ALIASES.get(snakeId, snakeId)
        steps.append(f"accountMappings[id]: '{normalizedId}' → '{snakeId}'")
        if snakeId != finalId:
            steps.append(f"SNAKE_ALIASES: '{snakeId}' → '{finalId}'")
        return finalId, steps

    if normalizedNm and normalizedNm in allMappings:
        snakeId = allMappings[normalizedNm]
        finalId = SNAKE_ALIASES.get(snakeId, snakeId)
        steps.append(f"accountMappings[nm]: '{normalizedNm}' → '{snakeId}'")
        if snakeId != finalId:
            steps.append(f"SNAKE_ALIASES: '{snakeId}' → '{finalId}'")
        return finalId, steps

    if normalizedNm:
        stripped_paren = _PAREN_RE.sub("", normalizedNm).replace(" ", "")
        if stripped_paren != normalizedNm and stripped_paren in allMappings:
            snakeId = allMappings[stripped_paren]
            finalId = SNAKE_ALIASES.get(snakeId, snakeId)
            steps.append(f"accountMappings[paren_strip]: '{stripped_paren}' → '{snakeId}'")
            if snakeId != finalId:
                steps.append(f"SNAKE_ALIASES: '{snakeId}' → '{finalId}'")
            return finalId, steps

    steps.append("미매핑")
    return None, steps


print("=" * 90)
print("1. 003 의심 항목 — 매핑 경로 추적")
print("=" * 90)

suspectItems = [
    ("net_income 혼입", [
        ("", "영업으로부터 창출된 현금흐름"),
        ("", "영업에서 창출된 현금흐름"),
        ("", "소계"),
        ("", "중단영업"),
    ]),
    ("income_tax_expense 혼입", [
        ("", "법인세의 납부"),
        ("", "법인세효과"),
        ("", "법인세수익"),
        ("", "당기손익으로 재분류되지 않는 항목의 법인세"),
        ("", "법인세비용 조정"),
    ]),
    ("ppe 혼입", [
        ("", "시설장치의 처분"),
        ("", "장기투자자산의 취득"),
        ("", "건설중인유형자산의 취득"),
        ("", "생산용생물자산의 취득"),
    ]),
    ("bonds 혼입", [
        ("", "전환사채"),
        ("", "유동성전환사채"),
        ("", "신주인수권부사채"),
        ("", "교환사채"),
        ("", "사채발행"),
        ("", "전환사채 보통주 전환"),
        ("", "주식발행비의 지급"),
    ]),
    ("retained_earnings 혼입", [
        ("", "자본잉여금"),
        ("", "회계정책변경효과"),
    ]),
]

for groupLabel, items in suspectItems:
    print(f"\n  --- {groupLabel} ---")
    for accountId, accountNm in items:
        result, steps = traceMapping(accountId, accountNm)
        finalDisplay = result or "None"
        print(f"  '{accountNm}' → {finalDisplay}")
        for step in steps:
            print(f"    {step}")

print()
print("=" * 90)
print("2. sga_expenses 관련 — accountMappings.json 검색")
print("=" * 90)

sgaSearchTerms = ["판매비", "판관비", "판매비와관리비", "판매및관리비", "sga", "selling"]
print("  accountMappings.json에서 sga 관련 검색:")
sgaFound = []
for key, snakeId in allMappings.items():
    keyLower = key.lower()
    if any(term in keyLower or term in key for term in sgaSearchTerms):
        sgaFound.append((key, snakeId))

if sgaFound:
    for key, snakeId in sgaFound[:20]:
        print(f"    '{key}' → '{snakeId}'")
else:
    print("    결과 없음")

print()
print("  CORE_MAP에서 sga 관련 검색:")
for key, snakeId in CORE_MAP.items():
    if "sga" in snakeId or "selling" in snakeId.lower() or "판매" in key:
        print(f"    '{key}' → '{snakeId}'")

print()
print("  ACCOUNT_NAME_SYNONYMS에서 판관비 관련:")
for key, val in ACCOUNT_NAME_SYNONYMS.items():
    if "판매" in key or "판관" in key or "관리비" in key:
        print(f"    '{key}' → '{val}'")

print()
print("  accountMappings.json에서 '판매비와관리비' 직접 조회:")
directResult = allMappings.get("판매비와관리비")
print(f"    '판매비와관리비' → {directResult}")
directResult2 = allMappings.get("판매비와 관리비")
print(f"    '판매비와 관리비' → {directResult2}")

print()
print("  실제 mapper.map() 결과:")
for nm in ["판매비와관리비", "판매비와 관리비", "판관비", "판매비및관리비", "판매비"]:
    result = mapper.map("", nm)
    alias = SNAKE_ALIASES.get(result, result) if result else None
    print(f"    '{nm}' → map: {result} → alias: {alias}")

print()
print("=" * 90)
print("3. trade_and_other_current_receivables 관련")
print("=" * 90)

trSearchTerms = ["매출채권", "receivable", "수취"]
print("  accountMappings.json에서 매출채권 관련 검색 (상위 20):")
trFound = []
for key, snakeId in allMappings.items():
    if any(term in key.lower() or term in key for term in trSearchTerms):
        trFound.append((key, snakeId))

for key, snakeId in trFound[:20]:
    print(f"    '{key}' → '{snakeId}'")

print()
print("  실제 mapper.map() 결과:")
for nm in ["매출채권", "매출채권및기타채권", "매출채권 및 기타채권", "매출채권및기타유동채권"]:
    result = mapper.map("", nm)
    alias = SNAKE_ALIASES.get(result, result) if result else None
    print(f"    '{nm}' → map: {result} → alias: {alias}")

print()
print("=" * 90)
print("4. SNAKE_ALIASES에 sga_expenses/receivables 관련 있는지")
print("=" * 90)
for key, val in SNAKE_ALIASES.items():
    if "sga" in key or "sga" in val or "selling" in key or "receivab" in key or "receivab" in val:
        print(f"    '{key}' → '{val}'")

print()
print("=" * 90)
print("5. accountMappings.json의 값(snakeId)으로 역검색 — net_income으로 매핑되는 키 전체")
print("=" * 90)

netIncomeKeys = [k for k, v in allMappings.items() if v == "net_income"]
print(f"  'net_income' 직접 매핑 키: {len(netIncomeKeys)}개")
for k in netIncomeKeys[:30]:
    print(f"    '{k}'")

profitLossKeys = [k for k, v in allMappings.items() if v == "profit_loss" or v == "net_profit"]
print(f"\n  'profit_loss' / 'net_profit' 매핑 키: {len(profitLossKeys)}개")
for k in profitLossKeys[:20]:
    print(f"    '{k}'")
