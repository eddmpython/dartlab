---
id: engines.viz.balanceStructureTrend
title: Viz - 자산·조달 구조 추이
kind: curated
scope: builtin
status: observed
category: engines
purpose: 재무상태표의 자산 배치와 부채+자본 조달 구조를 `balance-structure-trend` ChartSpec 으로 변환해 연도별 100% 누적 구조와 총자산 정합성을 함께 보여주는 시각화 실행 스킬이다.
whenToUse:
  - 자산구조 차트
  - 부채 자본 구조
  - balance structure trend
  - 재무상태표 시각화
  - 운전자산 비영업자산
  - 영업부채 차입금 자본
  - 자산 = 부채 + 자본
inputs:
  - BalanceStructureView dict
  - stockCode
  - corpName
  - periods
  - assetTrendParts / fundingTrendParts / equityTrendParts
outputs:
  - chartType balance-structure-trend ChartSpec
  - asset/funding/equity stacked series
  - totalAssetsSeries / totalFundingSeries
  - finance:BS evidenceBinding
toolRefs:
  - EngineCall
  - RunPython
knowledgeRefs:
  - engines.viz
  - engines.analysis.assetStructure
  - engines.dashboard
  - engines.mappers
sourceRefs:
  - dartlab://skills/engines.viz.balanceStructureTrend
requiredEvidence:
  - target
  - period
  - finance:BS
  - totalAssetsSeries
  - totalFundingSeries
  - evidenceBinding
  - executionRef
  - sourceRef
expectedOutputs:
  - balance-structure-trend spec
  - 자산 배치 변화 설명
  - 부채+자본 조달 구조 설명
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: supported
  pyodide:
    status: limited
    limitations:
      - 브라우저에서는 사전 구성된 BalanceStructureView 또는 landing dashboard model 이 노출한 view 만 사용한다.
failureModes:
  - 자산총계와 부채+자본 총계가 다른 기간을 섞어 비교함
  - 결손 계정을 0 으로 채워 구조 변화처럼 그림
  - 자본 세부 항목을 총자산 기준 share 와 자기자본 기준 share 로 혼동함
  - 단일 최신 분기만 보고 장기 자산구조 변화를 단정함
forbidden:
  - BS 원자료 또는 BalanceStructureView 없이 임의 stack 생성 금지
  - evidenceBinding 또는 finance:BS evidenceIds 없는 차트 emit 금지
  - 자산 = 부채 + 자본 정합성 검산 없이 해석 금지
examples:
  - 삼성전자 5년 자산 배치와 조달 구조
  - 현금·매출채권·재고·유형자산 비중 변화
  - 영업부채·차입금·기타부채·자본 조달 구성 변화
  - 이익잉여금이 자본 구조에서 차지하는 비중
linkedSkills:
  - engines.viz
  - engines.analysis.assetStructure
  - engines.dashboard
  - engines.mappers
source:
  type: manual_skill
  format: markdown
lastUpdated: '2026-05-13'
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## 엔진 역할

`engines.viz.balanceStructureTrend` 는 재무상태표를 단순 총액 표로 끝내지 않고, 같은 총자산을 두 관점으로 본다.

- 자산 배치: 현금, 매출채권, 재고, 유형자산, 무형자산, 기타/비영업 자산.
- 조달 구조: 영업부채, 차입금/사채, 기타부채, 자본.
- 자본 세부: 자본금, 자본잉여금, 이익잉여금, 자기주식, 기타자본.

렌더러는 `ChartRenderer` 의 `balance-structure-trend` 분기로 들어가며, shared chart 에서는 자산/조달/자본 band 를 연도별 100% stack 으로 표시한다. 회사 대시보드의 원본 `BalanceStructureTrend.svelte` 는 같은 view 로 총자산 추이, 자산 구성 100%, 조달 구성 100%, 최신 자산 증감을 함께 보여준다.

## 공개 호출 방식

```python
import dartlab
from dartlab.viz import emit_chart
from dartlab.viz.generators import specBalanceStructureTrend

c = dartlab.Company("005930")

# view 는 내부 dashboard/model 경로가 만드는 BalanceStructureView 다.
# periods, totalAssetsSeries, totalFundingSeries, assetTrendParts,
# fundingTrendParts, equityTrendParts 를 포함해야 한다.
# 공개 호출 계약이 아니다. 호출자가 이미 손에 쥔 view 를 넘긴다.

spec = specBalanceStructureTrend(
    view,
    stockCode="005930",
    corpName="삼성전자",
)

if spec is not None:
    emit_chart(spec)
```

대시보드 helper 가 없는 실행 환경에서는 BS 원자료에서 view dict 를 구성한 뒤 같은 generator 로 넘긴다. share 는 반드시 같은 기간의 `assets` 또는 `equity` denominator 로 계산한다.

```python
view = {
    "title": "삼성전자 자산 배치와 조달 구조",
    "periods": ["2023", "2024", "2025"],
    "totalAssetsSeries": [100.0, 120.0, 130.0],
    "totalFundingSeries": [100.0, 120.0, 130.0],
    "assetTrendParts": [
        {"id": "cash", "label": "현금", "values": [20, 24, 26], "shares": [20, 20, 20]},
        {"id": "tangible", "label": "유형자산", "values": [40, 48, 52], "shares": [40, 40, 40]},
    ],
    "fundingTrendParts": [
        {"id": "tradePayables", "label": "영업부채", "values": [15, 18, 20], "shares": [15, 15, 15]},
        {"id": "equity", "label": "자본", "values": [70, 84, 91], "shares": [70, 70, 70]},
    ],
    "equityTrendParts": [
        {"id": "retainedEarnings", "label": "이익잉여금", "values": [55, 66, 72], "shares": [78.6, 78.6, 79.1]},
    ],
    "debtRatio": 42.8,
    "sourceLabel": "finance/BS",
}
emit_chart(specBalanceStructureTrend(view, stockCode="005930", corpName="삼성전자"))
```

## 호출 동작

`specBalanceStructureTrend(view, ...)` 는 `BalanceStructureView` 형태를 흡수한다. `assetTrendParts`, `fundingTrendParts`, `equityTrendParts` 를 각각 `자산::`, `조달::`, `자본::` 이름을 가진 series 로 변환하고, 각 series 에 `data`, `shares`, `stack`, `tone`, `unit`, `missing` 을 보존한다.

`totalAssetsSeries` 와 `totalFundingSeries` 는 `options` 에 남긴다. 이 둘은 자산 총계와 부채+자본 총계가 같은 높이를 가져야 한다는 검산 근거다. 결손 계정은 0 으로 조작하지 않고 `missing=True`, `coverageNotes`, `None` 값으로 남긴다.

## 대표 반환 형태

```python
{
    "chartType": "balance-structure-trend",
    "title": "삼성전자 자산 구조 추이",
    "series": [
        {"name": "자산::현금", "data": [20.0, 24.0], "shares": [20.0, 20.0], "stack": "assetTrendParts", "type": "bar"},
        {"name": "조달::영업부채", "data": [15.0, 18.0], "shares": [15.0, 15.0], "stack": "fundingTrendParts", "type": "bar"},
        {"name": "자본::이익잉여금", "data": [55.0, 66.0], "shares": [78.6, 78.6], "stack": "equityTrendParts", "type": "bar"}
    ],
    "categories": ["2023", "2024"],
    "options": {
        "totalAssetsSeries": [100.0, 120.0],
        "totalFundingSeries": [100.0, 120.0],
        "debtRatio": 42.8
    },
    "evidenceIds": ["finance:BS"],
    "evidenceBinding": {
        "tableRef": "finance:BS:MIXED",
        "source": "finance",
        "stockCode": "005930",
        "topic": "BS",
        "periodKind": "MIXED",
        "periods": ["2023", "2024"]
    }
}
```

## 연계 절차

1. `ReadSkill("자산구조 시각화")` 로 이 skill 또는 `engines.analysis.assetStructure` 를 찾는다.
2. `engines.analysis.assetStructure` 로 BS 계정 의미와 빠진 항목을 먼저 확인한다.
3. 회사 대시보드 view 가 있으면 그 view 를 `specBalanceStructureTrend` 로 넘긴다.
4. view 가 없으면 BS 원자료에서 총자산, 부채, 자본, 세부 계정의 기간별 value/share 를 구성한다.
5. `totalAssetsSeries[i]` 와 `totalFundingSeries[i]` 의 차이가 material 한 기간은 해석 전에 coverage note 로 표시한다.
6. `emit_chart(spec)` 후 답변에는 최신 구조, 장기 변화, 결손/한계를 함께 쓴다.

## 기본 검증

- `periods` 가 2개 이상인지 확인한다.
- `assetTrendParts` 와 `fundingTrendParts` 가 모두 있는지 확인한다.
- 각 기간의 자산 share 합계와 조달 share 합계가 대체로 100% 인지 확인한다.
- `totalAssetsSeries` 와 `totalFundingSeries` 가 같은 기간 순서인지 확인한다.
- 자본 세부 `shares` 는 자기자본 denominator 로 계산될 수 있으므로 총자산 share 와 섞어 설명하지 않는다.
- `evidenceBinding.topic == "BS"` 또는 `evidenceIds` 에 `finance:BS` 가 있어야 한다.

## AI 직접 사용 방식

이 skill 은 사용자가 “자산구조”, “재무상태표를 그래프로”, “자산과 부채자본 구조를 한눈에”처럼 묻는 경우 먼저 고른다. 답변 전에 `engines.analysis.assetStructure` 를 읽어 계정 의미를 확인하고, 실행은 `RunPython` 에서 `specBalanceStructureTrend` 를 호출한다.

대상은 종목코드와 market 으로 고정한다. 기간은 기본 5년 또는 사용자가 말한 기간을 따른다. 결과 설명은 `자산 배치 변화 → 조달 구조 변화 → 자본 내부 변화 → 총자산 정합성/결손 한계` 순서로 조립한다. `falsifier` 는 총자산과 부채+자본이 맞지 않거나, 결손 계정이 큰데 구조 변화처럼 보이는 경우 즉시 확인한다.
