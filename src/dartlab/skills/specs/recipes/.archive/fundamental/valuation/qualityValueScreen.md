---
id: recipes.fundamental.valuation.qualityValueScreen
title: Quality + Value 횡단 스크리닝 (Novy-Marx GP/A 기반)
category: recipes
kind: recipe
scope: builtin
status: unverified
purpose: Novy-Marx (2013) gross profitability factor (Gross Profit / Total Assets) 와 단순 가치 (PER/PBR) 를 결합해 한국 chaebol discount 트랩을 회피한 quality value 후보를 횡단으로 발굴하는 절차. 트리거 — 'gross profitability', 'Novy-Marx 2013', 'quality value 횡단'.
whenToUse:
  - 저평가 종목 함정 회피
  - quality value 결합 스크리닝
  - Novy-Marx gross profitability
  - 한국 PBR 1 이하 함정 거름
  - chaebol discount 회피
  - 횡단 quality + value 후보 발굴
linkedSkills:
  - engines.scan
  - recipes.fundamental.credit.distressFilter
  - recipes.fundamental.valuation.check
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
  - "engines.viz.peerMatrix"
  - "engines.viz.tableBackedChart"
  - "engines.viz.priceChart"
visualGuidance:
  - "동종 비교는 engines.viz.peerMatrix를 사용하고 universe·peerCount·metric 결손률을 답변에 함께 노출한다."
  - "표 기반 순위·추세는 engines.viz.tableBackedChart만 사용하고 tableRef/evidenceBinding이 없으면 차트 대신 검산 표로 낮춘다."
  - "가격·수급 반응은 engines.viz.priceChart로만 그리며 OHLCV 기간·벤치마크·latestAsOf가 맞지 않으면 본문 차트로 쓰지 않는다."

forbidden:
  - GP/A 한 지표만으로 quality 단정 금지 — value (PER / PBR) 결합.
  - Novy-Marx 2013 미국 결과를 KR 시장 동일 가정으로 인용 금지.
  - chaebol discount 트랩 회피 (지주사 분리) 누락 시 결과 단정 금지.
  - PBR ≤ 1 가치주 선별 결과를 자동 매수 추천으로 단정 금지.
failureModes:
  - GP/A 분모 (총자산 vs 영업자산) 정의 모호
  - 한국 지주사 (holding) 의 PBR 디스카운트로 false positive
  - 산업별 정상 GP/A 분포 차이 무시
  - 일회성 손익 (M&A) 의 GP 영향 미보정
  - quality + value 결합 가중치 (50:50) 임의 선택
examples:
  - KR quality value 후보
  - Novy-Marx GP/A + 가치 결합
  - chaebol discount 회피 + 우량
  - quality + value + distress 필터
gap:
  primary:
    - scan
    - analysis
testUniverse:
  market: KR
  stockCodes:
    - "005930"
  asOfPolicy: latest
falsifier:
  description: "quality 근거 없이 valuation snapshot 만으로 후보를 통과시키면 recipe 실패로 본다."
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
---

## 학술 근거

Robert Novy-Marx, *"The Other Side of Value: The Gross Profitability Premium"* (Journal of Financial Economics, 2013): **Gross Profit / Total Assets** (GP/A) 가 ROE·ROA·ROIC 보다 강력한 quality factor. 핵심 발견:

- GP/A 는 가치 (B/M) 와 음(−) 상관 → 둘을 결합하면 hedge 효과로 위험 추가 없이 초과수익.
- 1963-2010 미국에서 GP/A 상위 quintile 이 하위 quintile 대비 연 4-5%p 초과수익 (Fama-French 3-factor 보정 후).
- 다른 quality 지표 (ROE·earnings growth) 가 가치 (low P/E·P/B) 와 양 상관 → 결합 시 quality 와 value 가 같은 방향, 분산 효과 약함.

dartlab 의 ratio 13 종에 GP/A 직접은 없지만 `grossMargin × totalAssetTurnover ≈ GP/A` 로 분해 근사 가능 (DuPont 식). 한국 시장에서는 chaebol governance discount 로 단순 저-PBR 가 함정인 경우 흔하므로, GP/A 게이트가 그 함정 회피에 특히 유효.

## 공개 호출 방식

```python
import dartlab
import polars as pl

target = "005930"
c = dartlab.Company(target)

def latest_period(df):
    if hasattr(df, "columns"):
        for col in df.columns:
            if str(col)[:4].isdigit():
                return str(col)
    return "latest"

def compact(obj):
    if isinstance(obj, pl.DataFrame):
        return {"type": "DataFrame", "rows": obj.height, "columns": obj.width}
    if isinstance(obj, dict):
        return {"type": "dict", "keys": list(obj.keys())[:8]}
    return {"type": type(obj).__name__}

quality = c.analysis("earningsQuality")
profitability = c.analysis("profitability")
valuation = c.analysis("valuation")
valuation_scan = dartlab.scan("valuation")
rows = valuation_scan.head(5).to_dicts() if isinstance(valuation_scan, pl.DataFrame) else []
bs = c.panel("BS", freq="Y")

emit_result(
    table=rows or [
        {"axis": "quality", "result": compact(quality)},
        {"axis": "profitability", "result": compact(profitability)},
        {"axis": "valuation", "result": compact(valuation)},
    ],
    values={"target": target, "candidateCount": len(rows), "hasQualityCheck": bool(quality)},
    date=latest_period(bs),
)
```

## 호출 동작

1. `scan("screen", spec=...)` — grossMargin 30% + totalAssetTurnover 0.5 + ROE 10% 동시 통과 종목.
2. `scan("valuation")` — KR 시장 snapshot (PBR 기준 grade 분류).
3. polars join — stockCode 키로 quality + value 결합.
4. grade 가 저평가/적정 인 것만.
5. `gpaApprox = grossMargin × totalAssetTurnover` 로 정렬.

기준값 (30 / 0.5 / 10) 은 한국 KOSPI 분포 기반 보수적 임계. 미국 시장 적용 시 시장 분포 percentile 을 따로 계산해 조정.

## 대표 반환 형태

`candidates : pl.DataFrame` — 컬럼:
- `stockCode : str` — 6 자리 종목 코드 (KR)
- `corpName : str` — 회사명
- `finance.ratio.grossMargin : float` — 매출총이익률 (%)
- `finance.ratio.totalAssetTurnover : float` — 총자산회전율
- `finance.ratio.roe : float` — ROE (%)
- `per`, `pbr`, `psr : float` — 시장 multiple
- `grade : str` — 저평가/적정/고평가/과열
- `gpaApprox : float` — GP/A 근사 (높을수록 강한 quality)

## 한계

- **GP/A 직접 컬럼 부재** — `grossMargin × totalAssetTurnover` 근사. 정확한 GP/A 는 `gross_profit / total_assets` (account 직접) 으로 확장 가능하나 본 recipe 는 ratio 만 사용.
- **valuation snapshot 은 KR 전용** — `dartlab.scan("valuation")` 은 한국 종목 한정. 미국 EDGAR 종목은 별도 경로 (Company.panel("FQ") + market cap 수동 결합) 필요.
- **임계값 (30/0.5/10) 은 보수적 절대치** — 산업별 분포 차이 큼 (반도체 grossMargin 50% vs 통신 20%). 산업 percentile 기반 게이트로 확장 가능.

## 한국 / 미국 시장 차이

- **한국**: chaebol governance discount 로 KOSPI 평균 PBR 약 1.0. 단순 PBR ≤ 1 만으로는 함정 너무 많음. GP/A 게이트가 진짜 quality 종목 골라내는 데 결정적. Value-up 프로그램 대상 종목과 겹치는 경우 추가 catalyst.
- **미국**: GP/A 학술 검증의 본 시장. S&P 500 평균 grossMargin 약 35%, totalAssetTurnover 약 0.6. 본 recipe 임계값 그대로 미국 적용 가능하나 valuation snapshot 부재로 PER/PBR 별도 fetch.

## 연계 절차

1. 본 recipe 로 후보 발굴 → `tableRef` 에 묶음.
2. 상위 5~10 종목에 대해 `recipes.fundamental.valuation.check` 로 단일 회사 가치평가 (DCF + valuation band) 심층.
3. `recipes.fundamental.credit.distressFilter` 로 부도 위험 종목 제외.
4. `engines.analysis` 로 발생주의 신호 점검 (CFO/NI 비율).
5. `engines.story` 로 6 막 인과 보고서 조합.

## 기본 검증

- 후보 수 &lt; 30 → 게이트 너무 빡빡 (임계값 완화).
- 후보 수 &gt; 200 → 게이트 너무 느슨 (totalAssetTurnover 0.7, grossMargin 35% 등 조정).
- `gpaApprox` 분포 확인 — 상위 10% 와 평균 격차 2 배 이상이어야 quality factor 작동.
- 단일 종목 결론 X — 본 recipe 는 후보 발굴 단계. 투자 결정은 단일 회사 심층 + valuation band + governance 점검 후.

## AI 직접 사용 방식

1. `ReadSkill` 에서 사용자 질문과 `whenToUse`를 맞춰 이 recipe를 고른다.
2. `GetSkillBody` 로 본문 전체를 읽고 `linkedSkills` 순서대로 먼저 필요한 엔진 skill을 확인한다.
3. `## 공개 호출 방식`의 첫 Python 블록을 target만 바꿔 `ValidateRecipe(..., capture=False)`로 smoke 실행한다.
4. 실행 결과의 `skillRef`, `tableRef`, `valueRef`, `dateRef`, `executionRef` 중 누락된 근거가 있으면 답변을 작성하지 말고 호출 또는 근거 요구를 보강한다.
5. 답변은 결론, 핵심 근거, 메커니즘, 반례·한계, 후속 모니터링 순서로 작성하고 `falsifier.description`이 있으면 반례 단락에서 반드시 확인한다.
