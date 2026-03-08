---
title: "3. Disclosure Text"
---

# 3. Disclosure Text — 공시 텍스트 분석

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/03_disclosure.ipynb)

숫자 뒤에 숨겨진 텍스트를 읽는다. 이 튜토리얼에서 다루는 내용은 다음과 같다.

- 사업의 내용 (섹션별 분류, 변경 탐지)
- 경영진단 및 분석의견 (MD&A)
- 회사의 개요 (설립일, 신용등급, 중소기업 여부)
- 회사 기본정보 (설립일, 상장일, 대표이사)
- 원재료·설비투자 현황

## 준비

```python
from dartlab import Company

c = Company("005930")
```

## 사업의 내용

사업보고서의 "사업의 내용" 섹션을 구조적으로 분류한다. property는 섹션 리스트를 반환한다.

```python
sections = c.business

for s in sections:
    print(f"[{s.key}] {s.title} ({s.chars}자)")
    print(s.text[:200])
    print("---")
```

주요 섹션 key 목록은 다음과 같다.

| key | 설명 |
|-----|------|
| `overview` | 사업 개요 |
| `products` | 주요 제품·서비스 |
| `materials` | 원재료·가격변동 |
| `sales` | 매출·수주 현황 |
| `risk` | 위험 요인 |
| `rnd` | 연구개발 현황 |
| `financial` | 재무 관련 사항 |
| `etc` | 기타 참고사항 |

### 연도별 변경 탐지

텍스트 변경량을 연도별로 추적한다. `get()`으로 전체 Result를 받아야 접근 가능하다.

```python
result = c.get("business")
for change in result.changes:
    print(f"{change.year}: 변경 {change.changedPct:.1%} | +{change.added}자 -{change.removed}자 | 총 {change.totalChars}자")
```

## 경영진단 및 분석의견 (MD&A)

이사의 경영진단 및 분석의견의 개요 텍스트를 반환한다.

```python
c.mdna   # 사업 개요 텍스트
```

전체 섹션은 `get()`으로 접근한다.

```python
result = c.get("mdna")
for section in result.sections:
    print(f"[{section.category}] {section.title}")
    print(f"  텍스트 {section.textLines}줄, 테이블 {section.tableLines}줄")
    print(section.text[:200])
    print("---")
```

주요 category 목록은 다음과 같다.

| category | 설명 |
|----------|------|
| `overview` | 개요 |
| `forecast` | 전망 |
| `financials` | 재무 상태 |
| `liquidity` | 유동성·자금 |

## 회사의 개요 (정량)

설립일, 주소, 신용등급 등 정량 데이터를 추출한다. Result 객체를 반환한다.

```python
result = c.overview

result.founded          # 설립 연도
result.address          # 소재지
result.homepage         # 홈페이지
result.subsidiaryCount  # 종속회사 수
result.isSME            # 중소기업 여부
result.isVenture        # 벤처기업 여부
result.listedDate       # 상장일
```

### 신용등급

```python
for cr in result.creditRatings:
    print(f"{cr.agency}: {cr.grade}")
```

### 파싱 상태

원문에서 찾지 못한 항목과 파싱 실패 항목을 확인한다.

```python
print(f"원문에 없음: {result.missing}")
print(f"파싱 실패: {result.failed}")
```

## 회사 기본정보 (companyOverviewDetail)

설립일, 상장일, 대표이사, 본점소재지 등을 dict로 반환한다. 산문형 문서도 regex fallback으로 추출한다.

```python
info = c.companyOverviewDetail

info["foundedDate"]    # "1969-01-13"
info["listedDate"]     # "1975-06-11"
info["ceo"]            # 대표이사
info["address"]        # 본점소재지
info["mainBusiness"]   # 주요사업
info["website"]        # 홈페이지 URL
```

## 원재료·설비투자

원재료 매입, 유형자산 기말잔액, 설비투자 현황이다. Result 객체를 반환한다.

```python
result = c.rawMaterial
```

### 원재료 매입

```python
for m in result.materials:
    print(f"{m.item}: {m.amount}백만원 ({m.ratio}%) — 공급처: {m.supplier}")
```

### 유형자산 기말잔액

```python
eq = result.equipment
print(f"토지: {eq.land}, 건물: {eq.buildings}, 기계: {eq.machinery}")
print(f"합계: {eq.total}, 감가상각: {eq.depreciation}, CAPEX: {eq.capex}")
```

### 설비투자

```python
for item in result.capexItems:
    print(f"{item.segment}: {item.amount}백만원")
```

## 회사 연혁

```python
c.companyHistory
# date | event
```

주요 연혁 이벤트를 날짜별로 정리한 DataFrame이다.

## 다음 단계

- [4. Advanced Analysis](./advanced) — K-IFRS 주석, 유형자산 변동, 관계기업
- [API Overview](../api/overview) — property 전체 목록
