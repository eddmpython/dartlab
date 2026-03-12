---
title: "7. Advanced Analysis"
---

# 7. Advanced Analysis — 고급 분석

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/07_advanced.ipynb)

K-IFRS 주석(Notes) 통합 접근, 유형자산 변동표, 관계기업 분석, 거버넌스 분석 등 심화 모듈을 다룬다.

- Notes 통합 접근 (12개 항목)
- 미등록 키워드 직접 조회 (23개)
- 유형자산 변동표
- 관계기업·공동기업 투자
- 이사회와 감사제도
- 거버넌스·리스크 분석
- 여러 종목 비교 분석
- Result 객체와 전체 일괄 조회

---

## 준비

```python
import dartlab

c = dartlab.Company("005930")
```

---

## K-IFRS 주석 — Notes

`c.notes`로 12개 K-IFRS 주석 항목에 통합 접근한다. 영문 속성과 한글 키 모두 지원한다.

### 영문 속성으로 접근

```python
c.notes.inventory          # 재고자산 DataFrame
c.notes.receivables        # 매출채권
c.notes.borrowings         # 차입금
c.notes.tangibleAsset      # 유형자산 변동표
c.notes.intangibleAsset    # 무형자산
c.notes.provisions         # 충당부채
c.notes.eps                # 주당이익
c.notes.lease              # 리스
c.notes.investmentProperty # 투자부동산
c.notes.affiliates         # 관계기업
c.notes.segments           # 부문정보
c.notes.costByNature       # 비용의 성격별 분류
```

### 한글 키로 접근

```python
c.notes["재고자산"]         # c.notes.inventory와 동일
c.notes["차입금"]           # c.notes.borrowings와 동일
c.notes["유형자산"]         # c.notes.tangibleAsset과 동일
```

### 전체 조회

```python
c.notes.keys()       # ['receivables', 'inventory', 'tangibleAsset', ...]
c.notes.keys_kr()    # ['매출채권', '재고자산', '유형자산', ...]
c.notes.all()        # 모든 항목을 dict로 반환
```

---

## 미등록 키워드 직접 조회

12개 주요 키워드 외에도 23개 키워드를 지원한다. Notes에 등록되지 않은 키워드는 `get()`으로 직접 호출한다.

```python
# 법인세
result = c.get("notesDetail", keyword="법인세")
print(result.tableDf)

# 특수관계자
result = c.get("notesDetail", keyword="특수관계자")
print(result.tableDf)
```

### 전체 23개 키워드

`재고자산`, `주당이익`, `충당부채`, `차입금`, `매출채권`, `리스`, `투자부동산`, `무형자산`, `법인세`, `특수관계자`, `약정사항`, `금융자산`, `공정가치`, `이익잉여금`, `금융부채`, `기타포괄손익`, `사채`, `종업원급여`, `퇴직급여`, `확정급여`, `재무위험`, `우발부채`, `담보`

### 연도별 상세 테이블

Notes는 DataFrame만 반환하지만, 원본 Result를 통해 연도별 상세 테이블도 접근 가능하다.

```python
result = c.get("notesDetail", keyword="재고자산")
for year, periods in result.tables.items():
    for p in periods:
        print(f"[{year}] {p.period} (패턴: {p.pattern})")
        for item in p.items[:3]:
            print(f"  {item.name}: {item.values}")
```

---

## 유형자산 변동표

Notes에서도 접근 가능하고, `get()`으로 전체 Result를 받을 수 있다.

```python
# Notes 경유
c.notes.tangibleAsset   # 카테고리별 기초/기말 시계열 DataFrame

# get()으로 전체 Result
result = c.get("tangibleAsset")
print(f"신뢰도: {result.reliability}")  # "high" 또는 "low"
if result.warnings:
    print(f"경고: {result.warnings}")
print(result.movementDf)   # 카테고리별 기초/기말 시계열
```

### 연도별 상세 변동

```python
for year, movements in result.movements.items():
    for m in movements:
        print(f"[{year}] {m.period}")
        print(f"  카테고리: {m.categories}")
        for row in m.rows:
            print(f"  {row}")
```

---

## 관계기업·공동기업

Notes에서도 접근 가능하다.

```python
# Notes 경유
c.notes.affiliates   # 변동 시계열 DataFrame

# get()으로 전체 Result
result = c.get("affiliates")
for year, profiles in result.profiles.items():
    for p in profiles:
        print(f"[{year}] {p.name}: {p.ratio}%, 장부가 {p.bookValue}")
```

---

## 이사회

```python
c.boardOfDirectors
# year | totalDirectors | outsideDirectors | meetingCount | avgAttendanceRate
```

위원회 구성도 확인 가능하다.

```python
result = c.get("boardOfDirectors")
print(result.boardDf)       # 이사회 시계열
print(result.committeeDf)   # 위원회 구성 (committeeName, composition, members)
```

---

## 감사제도

```python
c.auditSystem
# name | role | detail
```

감사활동 내역도 확인 가능하다.

```python
result = c.get("auditSystem")
print(result.committeeDf)   # 감사위원 구성
print(result.activityDf)    # 감사활동 내역 (date, agenda, result)
```

---

## 내부통제

```python
c.internalControl
# year | opinion | auditor | hasWeakness
```

---

## 거버넌스·리스크 종합

```python
# 관계자거래
c.relatedPartyTx
# year | entity | sales | purchases

# 우발부채
c.contingentLiability
# year | totalGuaranteeAmount

# 제재 현황
c.sanction
# year | date | agency | action | amount

# 위험관리
c.riskDerivative
# currency | upImpact | downImpact
```

### 관계자거래 상세

```python
result = c.get("relatedPartyTx")
print(result.revenueTxDf)    # 매출입 거래
print(result.guaranteeDf)    # 채무보증
print(result.assetTxDf)      # 자산 거래
```

### 우발부채 상세

```python
result = c.get("contingentLiability")
print(result.guaranteeDf)    # 채무보증
print(result.lawsuitDf)      # 소송 현황
```

---

## 여러 종목 비교

property 접근으로 간결하게 비교 분석할 수 있다.

### 재무 비교

```python
import polars as pl

codes = ["005930", "000660", "035420"]
rows = []

for code in codes:
    c = dartlab.Company(code)
    bs = c.BS
    if bs is not None:
        # 마지막 연도 자산총계 확인
        cols = [col for col in bs.columns if col != "account"]
        last_year = cols[-1]
        row = bs.filter(pl.col("account") == "자산총계")
        if row.height > 0:
            rows.append({
                "기업": c.corpName,
                "자산총계": row[last_year][0],
            })

print(pl.DataFrame(rows))
```

### 배당 비교

```python
dividends = []
for code in codes:
    c = dartlab.Company(code)
    div = c.dividend
    if div is not None:
        last = div.row(-1, named=True)
        dividends.append({
            "기업": c.corpName,
            "DPS": last.get("dps"),
            "배당수익률": last.get("dividendYield"),
            "배당성향": last.get("payoutRatio")
        })

print(pl.DataFrame(dividends))
```

---

## Result 객체 접근

property는 대표 DataFrame 하나를 반환한다. 모듈의 전체 데이터가 필요하면 `get()`을 사용한다.

```python
# property → 대표 DataFrame
c.audit   # opinionDf만 반환

# get() → 전체 Result 객체
result = c.get("audit")
result.opinionDf   # 감사의견
result.feeDf       # 감사보수
```

---

## 전체 일괄 조회

```python
d = c.all()

# 재무제표
d["BS"], d["IS"], d["CF"]

# 정기보고서
d["dividend"], d["employee"], d["majorHolder"]

# K-IFRS 주석
d["notes"]["inventory"], d["notes"]["borrowings"]
```

---

## 다음 단계

- [8. 기업 간 비교](./cross-company) — 섹터 분류, 인사이트 등급, 시장 순위
- [API Overview](../api/overview) — property 전체 목록과 파라미터 상세
- [계정 표준화와 시계열](../api/timeseries) — 7단계 매핑, snakeId, 정규화 방식


