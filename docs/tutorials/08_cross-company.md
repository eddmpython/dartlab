---
title: "8. Cross-Company Comparison"
---

# 8. 기업 간 비교 — 섹터, 인사이트, 순위

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/08_cross_company.ipynb)

DartLab의 분석 엔진을 활용해 기업을 섹터별로 분류하고, 7영역 인사이트 등급을 부여하고, 시장 내 순위를 확인하는 방법을 다룬다.

- 섹터 분류 (WICS 11개 섹터)
- 섹터별 벤치마크 파라미터
- 인사이트 등급 (7영역 A~F)
- 이상치 탐지
- 시장 내 순위
- 종합 비교 테이블

시계열 생성과 재무비율 비교는 [3. 시계열 분석](./timeseries)과 [4. 재무비율](./ratios)에서 다뤘으므로, 여기서는 분석 엔진에 집중한다.

---

## 준비

```python
import dartlab
```

---

## 섹터 분류

DartLab은 WICS(WiseFn Industry Classification Standard) 11섹터 체계로 기업을 자동 분류한다. 같은 섹터 내 기업끼리 비교해야 의미 있는 분석이 된다 — 반도체와 은행의 부채비율을 비교하는 건 무의미하다.

```python
from dartlab.engines.sector import classify

for code in ["005930", "000660", "035420", "051910"]:
    info = classify(code)
    print(f"{info.corpName}: {info.sector} > {info.industryGroup} (신뢰도: {info.confidence})")
```

분류는 3단계로 이루어진다:
1. **오버라이드 매핑** — 수동 지정된 기업 (삼성전자→정보기술 등)
2. **키워드 매칭** — 기업명/사업내용에서 키워드 추출
3. **KSIC 코드 매핑** — 한국표준산업분류 코드 기반

### 11개 섹터

| 섹터 | 예시 기업 |
|------|----------|
| 에너지 | SK이노베이션, S-Oil |
| 소재 | LG화학, POSCO |
| 산업재 | 현대건설, 두산 |
| 경기소비재 | 현대차, 삼성물산 |
| 필수소비재 | 농심, CJ제일제당 |
| 건강관리 | 삼성바이오, 셀트리온 |
| 금융 | KB금융, 삼성생명 |
| 정보기술 | 삼성전자, SK하이닉스 |
| 커뮤니케이션서비스 | NAVER, 카카오 |
| 유틸리티 | 한국전력, 한국가스 |
| 부동산 | 신한알파리츠 |

### 섹터별 벤치마크

각 섹터는 고유한 벤치마크 파라미터를 가진다. 밸류에이션 모델에서 할인율, 성장률, PER 멀티플을 섹터에 맞게 적용할 때 사용한다.

```python
from dartlab.engines.sector import getParams

params = getParams("005930")
print(f"섹터: {params.sector}")
print(f"할인율: {params.discountRate}%")
print(f"성장률: {params.growthRate}%")
print(f"PER 멀티플: {params.perMultiple}x")
```

---

## 인사이트 등급

7개 영역을 A~F로 등급화하여 기업의 강점과 약점을 한눈에 파악한다. 30개 이상의 재무 지표를 자동 분석한다.

```python
from dartlab.engines.insight import analyze

for code in ["005930", "000660", "035420"]:
    result = analyze(code)
    if result is None:
        continue
    grades = result.grades()
    grade_str = " / ".join(f"{k}:{v}" for k, v in grades.items())
    print(f"{result.company.corpName} [{result.profile}]: {grade_str}")
```

### 7개 등급 영역

| 영역 | 평가 항목 | A등급 기준 (예시) |
|------|----------|-----------------|
| **performance** | 매출/영업이익 성장률 | 매출 20%+ 성장, 이익 30%+ 성장 |
| **profitability** | 영업이익률, ROE | 영업이익률 15%+, ROE 15%+ |
| **health** | 부채비율, 유동비율 | 부채비율 50% 이하, 유동비율 200%+ |
| **cashflow** | 영업CF, FCF | 안정적인 영업CF, FCF 흑자 |
| **governance** | 최대주주 지분, 감사의견 | 안정적 지배구조, 적정 감사의견 |
| **risk** | 이상치, 우발부채, 관계자거래 | 이상치 없음, 우발부채 소규모 |
| **opportunity** | 성장 포텐셜 | 성장률 + 수익성 조합 우수 |

등급은 A(최우수) ~ F(심각한 문제)의 6단계다.

### 프로파일

기업의 전반적 성격을 한 마디로 요약한다.

```python
result = analyze("005930")
print(result.profile)   # "안정형", "성장형", "위험형" 등
```

### 이상치 탐지

재무 지표에서 통계적 이상치(Z-score 기반)를 자동 탐지한다.

```python
result = analyze("005930")
for anomaly in result.anomalies:
    print(f"  {anomaly.metric}: Z-score {anomaly.zscore:.1f} ({anomaly.direction})")
```

예를 들어 재고자산회전율이 갑자기 급락했거나, 매출채권 회수기간이 비정상적으로 길어졌다면 이상치로 탐지된다. 이는 분식회계, 재고 적체, 부실채권 등의 경고 신호일 수 있다.

---

## 시장 내 순위

전체 상장사 중 해당 기업의 위치를 확인한다. 매출, 자산 기준 전체 순위와 섹터 내 순위를 모두 제공한다.

```python
from dartlab.engines.rank import getRankOrBuild

for code in ["005930", "000660", "035420"]:
    rank = getRankOrBuild(code)
    if rank is None:
        continue
    print(f"\n{rank.corpName} ({rank.sector})")
    print(f"  매출 순위: {rank.revenueRank}/{rank.revenueTotal} (섹터 내 {rank.revenueRankInSector}/{rank.revenueSectorTotal})")
    print(f"  자산 순위: {rank.assetRank}/{rank.assetTotal}")
    print(f"  규모: {rank.sizeClass}")
```

`sizeClass`는 기업 규모를 대/중/소로 구분한다. 이를 활용해 "같은 섹터, 비슷한 규모" 기업끼리 비교하는 게 가장 의미 있다.

---

## 종합 비교 예시

여러 지표를 하나의 테이블로 정리하는 패턴이다.

```python
import polars as pl
import dartlab
from dartlab.engines.dart.finance import getTTM, getLatest
from dartlab.engines.sector import classify

codes = ["005930", "000660", "035420", "051910", "006400"]
rows = []

for code in codes:
    c = dartlab.Company(code)
    r = c.ratios
    sector = classify(code)
    if r is None:
        continue
    rows.append({
        "기업": c.corpName,
        "섹터": sector.sector if sector else "",
        "매출(억)": round(r.revenueTTM / 1e8) if r.revenueTTM else None,
        "영업이익률(%)": round(r.operatingMargin, 1) if r.operatingMargin else None,
        "ROE(%)": round(r.roe, 1) if r.roe else None,
        "부채비율(%)": round(r.debtRatio, 1) if r.debtRatio else None,
        "FCF(억)": round(r.fcf / 1e8) if r.fcf else None,
    })

df = pl.DataFrame(rows)
print(df)
```

---

## 다음 단계

- [계정 표준화와 시계열](../api/timeseries) — 7단계 매핑, snakeId 목록, 정규화 방식 상세
- [섹터 분류](../api/sector) — 분류 기준과 벤치마크 파라미터
- [인사이트 등급](../api/insight) — 7영역 등급 기준과 이상치 탐지
- [시장 순위](../api/rank) — 전체/섹터 내 순위 산출


