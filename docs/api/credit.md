---
title: Credit (신용평가)
---

# Credit — dartlab 독립 신용평가 (dCR)

공시 데이터만으로 재현 가능한 독립 신용등급. 20단계(dCR-AAA ~ dCR-D).

## 사용법

```python
import dartlab

# 루트 함수
dartlab.credit("005930")                # 등급 종합
dartlab.credit("005930", "채무상환")     # 축별 접근

# Company-bound
c = dartlab.Company("005930")
c.credit()                              # 등급 종합
c.credit("채무상환")                     # 축별
c.credit(detail=True)                   # 7축 상세 + 서사 + 지표 시계열
```

## 등급 체계

```
투자적격: dCR-AAA, AA+, AA, AA-, A+, A, A-, BBB+, BBB, BBB-
투기등급: dCR-BB+, BB, BB-, B+, B, B-
부실:     dCR-CCC, CC, C, D
```

- 현금흐름등급: eCR-1(최상) ~ eCR-6(최하)
- 등급 전망: 안정적 / 긍정적 / 부정적

## 7축 평가 체계

| 축 | 비중 | 핵심 지표 |
|------|:---:|---------|
| 채무상환능력 | 25% | FFO/Debt, Debt/EBITDA, EBITDA/이자비용 |
| 자본구조 | 20% | 부채비율, 차입금의존도, 순차입금/EBITDA |
| 유동성 | 15% | 유동비율, 현금비율, 단기차입금비중 |
| 현금흐름 | 15% | OCF/매출, FCF/매출, OCF 추세 |
| 사업안정성 | 10% | 매출CV, 이익CV, 규모, 부문다각화 |
| 재무신뢰성 | 10% | Beneish M, Piotroski F, 감사의견 |
| 공시리스크 | 5% | 우발부채, 리스크 키워드 |

## 결과 구조

```python
cr = c.credit(detail=True)

cr["grade"]              # "dCR-AA"
cr["score"]              # 6.64 (0=AAA, 100=D)
cr["pdEstimate"]         # 0.02 (1년 부도확률 %)
cr["eCR"]                # "eCR-1"
cr["outlook"]            # "안정적"
cr["axes"]               # 7축 상세 [{name, score, weight, metrics}]
cr["narratives"]         # 서사 {overall, profile, trend, borrowings, axes[]}
cr["metricsHistory"]     # 16개 지표 8개년 시계열
```

## AI 연동

AI가 `c.credit(detail=True)`를 호출하면 로데이터 + 서사를 한 번에 받아서
산업 맥락과 인과관계를 직접 판단한다.

```python
dartlab.ask("삼성전자 신용평가 분석해줘")
# → AI가 c.credit(detail=True) 호출 → 신용분석가 수준 해석
```

## 보고서 발간

```python
from dartlab.credit.publisher import publishReport

publishReport("005930")             # docs/credit/reports/에 저장
publishBatch(["005930", "000660"])   # 배치 발간
```

발간 보고서: `docs/credit/reports/{종목코드}_{기업명}.md`

## 업종별 차등

같은 부채비율이라도 업종에 따라 다르게 평가한다.

| 업종 | 부채비율 AA급 | 특수 처리 |
|------|:---:|---------|
| 제조업 | ~80% | 기본 기준 |
| 금융업 | ~400% | 레버리지 구조 다름 |
| 유틸리티 | ~200% | 높은 부채 허용 |
| IT | ~60% | 무형자산 비중 높아 엄격 |
| 자동차 | ~200% | 캡티브금융 자동 감지 |
| 반도체 | ~120% | 사이클 CAPEX 허용 |

## 설계 원칙

1. **재현 가능성** — 같은 입력 → 같은 등급
2. **투명성** — 모든 파라미터/가중치 공개
3. **보수주의** — 의심스러우면 낮게
4. **독립성** — 신평사 등급을 정답으로 보지 않는다
