# Macro

시장 레벨 매크로 분석 엔진. Company 없이 경제 환경을 해석한다.
dartlab의 4가지 비교 가능성 중 "시장 내/시장 간 비교"를 담당한다.

| 항목 | 내용 |
|------|------|
| 레이어 | L2 |
| 진입점 | `dartlab.macro()` |
| 소비 | gather(L1) — FRED/ECOS 매크로 데이터 |
| 생산 | ai(L3)가 매크로 환경 판단에 소비 |
| 축 | 6축: 사이클, 금리, 자산, 심리, 유동성, 종합 |

## 설계 원칙

- **Company 불필요** — 시장 레벨 분석이므로 종목코드 없이 동작
- **macro ↛ analysis, analysis ↛ macro** — 같은 L2지만 상호 import 금지
- 해석의 조합은 AI(L3)의 몫 — "이 매크로 환경에서 이 기업은?"은 AI가 macro + analysis를 결합
- market 파라미터로 KR/US 지원
- L0 순수 함수(macroCycle, sentiment, liquidity)를 조합하여 해석 제공

## 단일 진입점 + API

```python
import dartlab

dartlab.macro()                       # 가이드 (축 목록)
dartlab.macro("사이클")               # 경제 사이클 4국면 판별
dartlab.macro("금리")                 # 금리 방향 + 고용/물가
dartlab.macro("자산")                 # 5대 자산 종합 해석
dartlab.macro("심리")                 # 공포탐욕 + VIX 구간
dartlab.macro("유동성")               # M2 + 연준 B/S + 신용스프레드
dartlab.macro("종합")                 # 전체 종합 판정

dartlab.macro("사이클", market="KR")  # 한국 사이클
dartlab.macro("사이클", market="US")  # 미국 사이클 (기본값)
```

한글/영문 양방향 alias:
```python
dartlab.macro("cycle")      # 영문
dartlab.macro("사이클")     # 한글 — 동일 결과
```

## 축 설계

| 축 | key | 설명 |
|------|------|------|
| 사이클 | cycle | 경제 사이클 4국면(확장/둔화/침체/회복) 판별 + 전환 시퀀스 감지 |
| 금리 | rates | 단기/장기 금리 해석 + 고용/물가 동향 + 금리 방향 판단 |
| 자산 | assets | 5대 자산(단기금리/장기금리/환율/금/VIX) 심층 해석 |
| 심리 | sentiment | 시장 공포탐욕 근사 + VIX 구간 + 분할매수 신호 |
| 유동성 | liquidity | M2 + 연준 B/S + 신용스프레드 종합 유동성 환경 |
| 종합 | summary | 전체 축 결과를 하나의 종합 매트릭스로 조합 |

## 데이터 소스

| market | 소스 | 데이터 |
|--------|------|--------|
| US | FRED | 국채 금리, CPI, 고용, M2, 연준 B/S, VIX, 신용스프레드 |
| KR | ECOS | 기준금리, 국채, 소비자물가, 통화량, 경기 선행/동행지수 |

gather(L1)가 원시 데이터를 수집하고, macro(L2)가 해석을 올린다.

## L0 순수 함수

macro 엔진은 core/finance의 순수 함수를 조합한다:

| 파일 | 함수 | 역할 |
|------|------|------|
| macroCycle.py | classifyCycle | 사이클 4국면 판별 |
| macroCycle.py | interpretAssets | 5대 자산 종합 해석 |
| macroCycle.py | calcMultipleBand | PER/PBR 밴드 계산 |
| macroCycle.py | rateOutlook | 금리 방향 + 고용/물가 분해 |
| sentiment.py | fearGreed 등 | 공포탐욕 근사, 금리기대, 고용, 물가 |
| liquidity.py | analyzeLiquidity 등 | M2, 연준 B/S, 신용스프레드 |

## analysis와의 관계

analysis에는 기업에 종속된 매크로 축만 남아 있다:
- **매크로민감도**: 외생변수 6축 회귀 + 매출 방향 (Company-bound)
- **밸류에이션밴드**: PER/PBR 정규분포 밴드 현재 위치 (Company-bound)

시장 레벨 해석(사이클 판별, 자산 해석)은 macro 엔진으로 이동했다.
AI가 "이 매크로 환경에서 삼성전자는?"이라는 질문에 답할 때 macro + analysis 양쪽을 조합한다.

## 관련 코드

| 경로 | 역할 |
|------|------|
| `src/dartlab/macro/` | 매크로 분석 엔진 (6축) |
| `src/dartlab/macro/__init__.py` | Macro 클래스, 축 레지스트리, alias |
| `src/dartlab/macro/cycle.py` | 사이클 분석 |
| `src/dartlab/macro/rates.py` | 금리 분석 |
| `src/dartlab/macro/assets.py` | 자산 분석 |
| `src/dartlab/macro/sentiment.py` | 심리 분석 |
| `src/dartlab/macro/liquidity.py` | 유동성 분석 |
| `src/dartlab/macro/summary.py` | 종합 판정 |
| `src/dartlab/core/finance/macroCycle.py` | L0 순수 함수 (사이클/자산/밴드/금리) |
| `src/dartlab/core/finance/sentiment.py` | L0 순수 함수 (공포탐욕/금리기대) |
| `src/dartlab/core/finance/liquidity.py` | L0 순수 함수 (M2/B-S/스프레드) |
