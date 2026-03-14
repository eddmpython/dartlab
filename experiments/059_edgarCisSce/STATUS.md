# 059 EDGAR CIS/SCE 태그 커버리지

## 목표
SEC XBRL에서 CIS(포괄손익계산서)와 SCE(자본변동표) 태그의 존재 여부와 구조를 파악하여, 현재 IS/BS/CF 3개만 처리하는 파이프라인에 추가할 가치가 있는지 판단.

## 실험 목록

| # | 실험 | 결과 |
|---|------|------|
| 001 | CI/EQ 키워드 커버리지 (500개 샘플) | CI 73.8%, EQ 95.4% |
| 002 | AAPL CI/EQ 태그 값 구조 분석 | CI=duration, EQ=footnote 세부 |

## 핵심 발견

### CI (포괄손익계산서) — 추가 가치 있음
- 73.8% 기업이 CI 관련 태그 보유
- ComprehensiveIncomeNetOfTax: 57.2% 보유 (핵심)
- **duration 기반** → IS와 동일한 standalone 추출 가능
- 핵심 태그 3개면 CIS 기본 행 복원 가능:
  1. `ComprehensiveIncomeNetOfTax` (당기순이익 + OCI)
  2. `OtherComprehensiveIncomeLossNetOfTaxPortionAttributableToParent`
  3. `OtherComprehensiveIncomeLossAvailableForSaleSecuritiesAdjustmentNetOfTax`

### SCE (자본변동표) — 추가 불가
- EQ 키워드 95.4%는 착시 — 대부분 BS 잔액(stockholdersEquity 92.4%)
- 순수 EQ 태그 62개 중 50+개가 ShareBasedCompensation footnote 세부
- SEC XBRL은 자본변동표를 **행렬(period × equity component)로 제출하지 않음**
- DART SCE 매트릭스와 구조적으로 다름 → 매트릭스 복원 불가

## 다음 단계
- CI 핵심 태그를 mapper/pivot에 추가하는 실험 (003)
- standardAccounts.json CI 섹션 보강
- SCE는 향후 10-K HTML 파싱(docs 경로)으로 접근
