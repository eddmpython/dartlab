---
id: recipes.fundamental.quality.piotroskiLite
title: Piotroski F-Score 7 항목 횡단 점수카드
category: recipes
kind: recipe
scope: builtin
status: unverified
purpose: Piotroski (2000) F-Score 의 9 항목 중 dartlab ratio 로 가능한 7 항목을 횡단 계산해 저평가 종목군에서 우량 회사를 골라내는 점수카드 절차. 트리거 — 'F-Score', 'Piotroski 7 항목', '저평가 우량 발굴'.
whenToUse:
  - Piotroski F-Score
  - 가치주 함정 회피
  - 저PBR 우량 회사 선별
  - 수익성 + 재무건전성 + 효율성 점수
  - F-Score 5 점 이상
  - 가치주 quality 점수카드
linkedSkills:
  - engines.scan
  - recipes.fundamental.valuation.qualityValueScreen
  - recipes.fundamental.valuation.grahamDeepValue
  - engines.analysis
toolRefs:
  - EngineCall
  - RunPython
requiredEvidence:
  - skillRef
  - tableRef
  - valueRef
  - dateRef
  - executionRef
  - sourceRef
visualRefs:
  - "engines.viz.financialStructureCharts"
  - "engines.viz.cashflowWaterfall"
  - "engines.viz.mermaidDiagram"
visualGuidance:
  - "재무제표 구조는 engines.viz.financialStructureCharts를 사용하고 IS/BS/CF 원표와 결산기·연결 기준이 맞을 때만 emit한다."
  - "현금흐름·배당·자본배분 bridge는 engines.viz.cashflowWaterfall을 사용하고 CF 원표와 부호 convention을 검산한다."
  - "메커니즘 diagram은 engines.viz.mermaidDiagram으로 8노드 이하만 만들고 모든 edge에 문장·수치·sourceRef 근거를 둔다."

forbidden:
  - F-Score 9 항목 중 7 항목 사용 결과를 풀-Piotroski 결과로 단정 금지 — 학술 근사.
  - 가치주 universe (BM 상위 quintile) 외에 F-Score 적용 단정 금지 — 가치주 한정.
  - F-Score 단일 점수만으로 매수 추천 단정 금지.
  - 1976-1996 미국 표본 thresholds 를 KR 시장 동일 적용 금지.
failureModes:
  - 9 항목 중 2 항목 (CFO 부호 / 외부자금조달) 누락 시 score 분포 변동
  - F-Score 의 산업 (제조업 vs 서비스업) 적용성 차이
  - 가치주 universe 정의 (PBR 상위 quintile vs 하위) 임의 선택
  - 시계열 (4Q / 8Q) 빈도 차이로 점수 변동
  - 일회성 손익 (M&A / 매각) 의 항목별 영향 미보정
examples:
  - KR 가치주 F-Score 7 항목
  - F-Score 5+ 우량 가치주 후보
  - 가치주 + F-Score + 매수
  - F-Score + Piotroski 사후 검토
gap:
  primary:
    - scan
    - analysis
lastUpdated: '2026-05-13'
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: limited
  pyodide:
    status: limited
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## 학술 근거

Joseph Piotroski, *"Value Investing: The Use of Historical Financial Statement Information to Separate Winners from Losers"* (Journal of Accounting Research, 2000): 저-PBR (가치주) 유니버스 안에서 9 가지 fundamental 신호로 점수화. 1976-1996 미국 백테스트:

- 고-점수 (8-9 점) 가치주 연 13.4% vs 저-점수 (0-1 점) 5.9%.
- 점수 0 → 1 단위 상승 시 평균 +1.5%p 초과수익.
- 가치주 (BM 상위 quintile) 안에서 작동, 성장주에서는 약함.

원전 9 항목 중 dartlab ratio 13 종으로 가능한 7 항목만 사용 (lite). 신주발행 (자본금 변동) 과 ΔassetTurnover 는 한국 회계 특이성으로 노이즈 큼 → 제외. 미국 적용 시 둘 추가 가능.

## 7 항목 (각 1 점, 합계 0~7)

| 번호 | 항목 | dartlab 계산 |
|---|---|---|
| 1 | ROA &gt; 0 | `roa > 0` |
| 2 | CFO &gt; 0 | `operatingCfMargin > 0` |
| 3 | ΔROA &gt; 0 | 당년 `roa` − 전년 `roa` &gt; 0 |
| 4 | CFO &gt; NI | `operatingCfMargin > netMargin` (accrual quality) |
| 5 | ΔdebtRatio &lt; 0 | 당년 `debtRatio` − 전년 `debtRatio` &lt; 0 |
| 6 | ΔcurrentRatio &gt; 0 | 당년 `currentRatio` − 전년 `currentRatio` &gt; 0 |
| 7 | ΔgrossMargin &gt; 0 | 당년 `grossMargin` − 전년 `grossMargin` &gt; 0 |

원전 9 점 → 7 점 변환 시 임계는 5 점 이상 (≈ 원전 7 점) 을 권장.

## 공개 호출 방식

```python
import dartlab
import polars as pl

# 1) 7 ratio 모두 freq="Y" 로 fetch (당년 + 전년 컬럼 자동)
def fScore() -> pl.DataFrame:
    ratios = ["roa", "operatingCfMargin", "netMargin", "debtRatio", "currentRatio", "grossMargin"]
    frames = [dartlab.scan("ratio").rename({"2025": f"{r}_25", "2024": f"{r}_24"}) for r in ratios]
    df = frames[0]
    for f in frames[1:]:
        df = df.join(f, on="stockCode", how="inner")
    return df.with_columns([
        (pl.col("roa_25") > 0).cast(pl.Int8).alias("p1_roa"),
        (pl.col("operatingCfMargin_25") > 0).cast(pl.Int8).alias("p2_cfo"),
        (pl.col("roa_25") > pl.col("roa_24")).cast(pl.Int8).alias("p3_dRoa"),
        (pl.col("operatingCfMargin_25") > pl.col("netMargin_25")).cast(pl.Int8).alias("p4_accrual"),
        (pl.col("debtRatio_25") < pl.col("debtRatio_24")).cast(pl.Int8).alias("p5_dDebt"),
        (pl.col("currentRatio_25") > pl.col("currentRatio_24")).cast(pl.Int8).alias("p6_dCurrent"),
        (pl.col("grossMargin_25") > pl.col("grossMargin_24")).cast(pl.Int8).alias("p7_dGm"),
    ]).with_columns(
        pl.sum_horizontal("p1_roa","p2_cfo","p3_dRoa","p4_accrual","p5_dDebt","p6_dCurrent","p7_dGm").alias("fScore")
    )

# 2) 가치주 유니버스 (저PBR) 안에서 5 점 이상 추출
value = dartlab.scan("valuation")
result = (
    fScore()
    .join(value.select(["stockCode", "pbr", "per", "grade"]), on="stockCode")
    .filter((pl.col("pbr") <= 1.5) & (pl.col("fScore") >= 5))
    .sort("fScore", descending=True)
)
```

## 호출 동작

1. `scanRatio(r, freq="Y")` 6 회 (roa·operatingCfMargin·netMargin·debtRatio·currentRatio·grossMargin) — 컬럼 `"2025"`, `"2024"`.
2. polars join 으로 한 wide 테이블.
3. 7 항목 binary cast → `fScore` 합산.
4. `scan("valuation")` 결합 → `pbr ≤ 1.5` + `fScore ≥ 5`.
5. `fScore` 내림차순 정렬.

## 대표 반환 형태

`result : pl.DataFrame` — 컬럼:
- `stockCode`, `corpName`
- `p1_roa` ~ `p7_dGm : int8` — 7 항목 통과 여부 (0 또는 1)
- `fScore : int` — 0~7 합계
- `pbr`, `per : float` — 시장 multiple
- `grade : str` — valuation grade

## 한계

- **원전 9 → 7 변환** — 신주발행 항목과 ΔassetTurnover 제외. 한국 자본금 변동은 무상증자·주식배당 등 노이즈로 학술 신호 약함.
- **freq="Y" 만 의존** — 분기 데이터로 ΔROA 등 더 민감한 신호도 가능하나 본 recipe 는 연간 표준.
- **5 기간 일관성 미점검** — 단일 연도 변화만 봄. 5 년 일관성 (compounderCandidates) 또는 학술적 ΔROA 5 년 평균은 별도 확장.
- **PBR 1.5 임계는 조정 가능** — 한국 chaebol discount 시장에서는 1.0 이하로 더 빡빡하게 가능.

## 한국 / 미국 시장 차이

- **한국**: 저-PBR 가치주 풀이 미국보다 큼 (KOSPI 평균 PBR ≈ 1.0). 본 lite 7 점 모델로 함정 회피 효과 강함. 단 chaebol 계열사 (지주회사·금융 자회사) 회계 특이성 주의.
- **미국**: 원전 검증 시장. 신주발행 항목 추가로 9 점 만점 권장. PBR 1.5 → 2.0 까지 완화 가능 (S&P 500 평균 ≈ 4).

## 연계 절차

1. 본 recipe 로 후보 발굴 → `tableRef` 에 fScore 분포 표.
2. fScore 6-7 점 종목에 대해 `recipes.fundamental.valuation.qualityValueScreen` 의 GP/A 게이트 추가 통과 여부 확인.
3. `recipes.fundamental.credit.distressFilter` 로 위험 종목 제외.
4. `engines.analysis` — CFO/NI 비율 시계열 정합성 점검.
5. `engines.story` 로 후보별 narrative 생성.

## 기본 검증

- 점수 분포 — 평균 3-4 점이 정상. 평균 6 점 이상 = 게이트 의심 (PBR 1.5 너무 느슨).
- 5 점 이상 후보 수 — 50~150 개가 정상 범위 (KOSPI 약 2400 종목 중 2~6%).
- ΔROA·ΔdebtRatio 등 변화 항목이 한쪽으로 쏠리면 시장 사이클 영향 — 매크로 환경 함께 해석.
- "F-Score = 7 = 매수" 단정 X — 점수카드는 후보 발굴 도구. 단일 회사 심층 검증 필수.
