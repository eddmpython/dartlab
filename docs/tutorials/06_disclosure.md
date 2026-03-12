---
title: "6. Disclosure Text"
---

# 6. Disclosure Text — 공시 텍스트 분석

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/06_disclosure.ipynb)

숫자 뒤에 숨겨진 텍스트를 읽는다. 이 튜토리얼에서 다루는 내용은 다음과 같다.

- 사업의 내용 (섹션별 분류, 변경 탐지)
- 경영진단 및 분석의견 (MD&A)
- 회사의 개요 (설립일, 신용등급, 중소기업 여부)
- 회사 기본정보 (설립일, 상장일, 대표이사)
- 원재료·설비투자 현황
- 회사 연혁

---

## 준비

```python
import dartlab

c = dartlab.Company("005930")
```

---

## 사업의 내용

사업보고서의 "사업의 내용" 섹션을 구조적으로 분류한다. property는 섹션 리스트를 반환한다.

```python
sections = c.business

for s in sections:
    print(f"[{s.key}] {s.title} ({s.chars}자)")
    print(s.text[:200])
    print("---")
```

### 주요 섹션 key

| key | 설명 | 주요 내용 |
|-----|------|-----------|
| `overview` | 사업 개요 | 회사 소개, 주요 사업 영역 |
| `products` | 주요 제품·서비스 | 제품별 매출 비중, 가격 동향 |
| `materials` | 원재료·가격변동 | 주요 원재료, 조달 현황 |
| `sales` | 매출·수주 현황 | 부문별 매출, 수주 잔고 |
| `risk` | 위험 요인 | 산업 리스크, 회사 고유 리스크 |
| `rnd` | 연구개발 현황 | R&D 투자, 연구 인력 |
| `financial` | 재무 관련 사항 | 재무 건전성, 자금 조달 |
| `etc` | 기타 참고사항 | 그 밖의 중요 사항 |

### 특정 섹션 찾기

```python
# 사업 개요만 읽기
overview = next((s for s in c.business if s.key == "overview"), None)
if overview:
    print(overview.text[:500])
```

### 연도별 변경 탐지

텍스트 변경량을 연도별로 추적한다. `get()`으로 전체 Result를 받아야 접근 가능하다.

```python
result = c.get("business")

# 변경 이력
for change in result.changes:
    print(f"{change.year}: 변경 {change.changedPct:.1%} | +{change.added:,}자 -{change.removed:,}자 | 총 {change.totalChars:,}자")
```

> 변경률이 높은 해에는 사업 구조 변경, 신사업 진출, 위험 요인 추가 등이 있을 수 있다.

---

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

### 주요 category

| category | 설명 | 포함 내용 |
|----------|------|-----------|
| `overview` | 개요 | 사업 현황 요약 |
| `forecast` | 전망 | 향후 사업 전망 |
| `financials` | 재무 상태 | 재무제표 분석 |
| `liquidity` | 유동성·자금 | 자금 조달, 현금 흐름 |

---

## 회사의 개요 (정량)

설립일, 주소, 신용등급 등 정량 데이터를 추출한다. Result 객체를 반환한다.

```python
result = c.overview

print(f"설립: {result.founded}")
print(f"소재지: {result.address}")
print(f"홈페이지: {result.homepage}")
print(f"종속회사: {result.subsidiaryCount}개")
print(f"중소기업: {result.isSME}")
print(f"벤처기업: {result.isVenture}")
print(f"상장일: {result.listedDate}")
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

---

## 회사 기본정보 (companyOverviewDetail)

설립일, 상장일, 대표이사, 본점소재지 등을 dict로 반환한다.

```python
info = c.companyOverviewDetail

print(f"설립일: {info['foundedDate']}")
print(f"상장일: {info['listedDate']}")
print(f"대표이사: {info['ceo']}")
print(f"소재지: {info['address']}")
print(f"주요사업: {info['mainBusiness']}")
print(f"홈페이지: {info['website']}")
```

---

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

---

## 회사 연혁

```python
c.companyHistory
# date | event
```

주요 연혁 이벤트를 날짜별로 정리한 DataFrame이다.

---

## 다음 단계

- [7. 고급 분석](./advanced) — K-IFRS 주석, 유형자산 변동, 관계기업
- [8. 기업 간 비교](./cross-company) — 섹터, 인사이트, 순위

