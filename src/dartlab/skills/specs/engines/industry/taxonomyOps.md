---
id: engines.industry.taxonomyOps
title: Industry — Taxonomy 운영 (taxonomyOps)
category: engines
kind: curated
scope: builtin
status: observed
purpose: 산업 분류 데이터 (taxonomy.json + nodes.json) 운영자 수동 갱신 절차서 — 신생 산업 추가 / 신규 상장 종목 매핑 / stage 분류 정합성 확인. accountMappings (mappingRefresh) 와 분리된 industry 측 SSOT.
whenToUse:
  - taxonomy 갱신
  - nodes.json 추가
  - 신규 상장 종목 산업 매핑
  - 신생 산업 추가
  - 산업 분류 운영
  - industry 매핑 갱신
  - taxonomyOps
sourceRefs:
  - dartlab://skills/engines.industry.taxonomyOps
capabilityRefs:
  - industry
knowledgeRefs:
  - engines.industry
  - operation.mappingRefresh
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
linkedSkills:
  - engines.industry
  - operation.mappingRefresh
---

## 엔진 역할

`industry` 엔진의 *taxonomy 운영* sub-axis. 산업 분류 데이터 두 파일 (`taxonomy.json` = 산업·stage 정의 / `nodes.json` = 종목→stage 매핑) 의 운영자 수동 갱신 절차서. accountMappings 측은 `operation.mappingRefresh` SSOT — 본 spec 은 *industry 측 데이터* 전용.

## 공개 호출 방식

```python
import dartlab

# 갱신 후 확인 (호출 형태는 base SKILL 과 동일)
guide = dartlab.industry()
# → 신규 산업 추가 시 목록에 등장
nodes = dartlab.industry("새산업ID")
# → 신규 종목 매핑 확인

c = dartlab.Company("신규종목코드")
print(c.industry())
# → {chainId, stage, confidence, ...} 또는 None
```

## 호출 동작

본 spec 은 데이터 갱신 *절차서* — 코드 호출 동작은 base SKILL `engines.industry` 그대로. 갱신 자체는 운영자 수동.

## 갱신 절차

### 1. 신규 산업 추가

`src/dartlab/industry/taxonomy.json` 직접 편집:

```json
{
  "신규산업ID": {
    "name": "한글 산업명",
    "stages": [
      {"id": "stageId", "name": "한글 공정명", "stream": "upstream"},
      ...
    ]
  }
}
```

- `stages` 순서 = 밸류체인 흐름 순 (upstream → midstream → downstream).
- `stream` enum: `upstream` / `midstream` / `downstream` 3 종만 (engines.industry.supplyChain SSOT).
- stage `id` 는 camelCase 영문, 산업 내 unique.

### 2. 종목 매핑 추가

`src/dartlab/industry/nodes.json` 편집:

```json
{
  "종목코드6자리": {
    "chainId": "산업ID",
    "stage": "stageId",
    "confidence": 0.85,
    "matches": ["매칭 키워드 1", "키워드 2"],
    "products": ["주요 제품 1", "제품 2"],
    "role": "한글 역할 (제조 / 설계 / 장비 / ...)"
  }
}
```

- `confidence` 0~1, 0.5 미만 = 신뢰 한계 명시 (Company.industry() 답변에서 표기).
- `matches` 는 사업보고서·제품군에서 추출한 정성 근거.
- 같은 종목이 여러 stage 후보 — primary 1 개만 등록 (secondary 매핑은 별도 트랙).

### 3. 갱신 후 확인 (운영자 수동)

```bash
# 1. taxonomy 로드 검증
uv run python -X utf8 -c "from dartlab.industry import loadTaxonomy; print(loadTaxonomy().keys())"

# 2. 신규 산업 가이드
uv run python -X utf8 -c "import dartlab; print(dartlab.industry())"

# 3. 신규 종목 매핑
uv run python -X utf8 -c "import dartlab; print(dartlab.Company('신규코드').industry())"

# 4. capability 카탈로그는 docstring 라이브 빌드 — 재생성 단계 없음 (loadCapabilities 자동 반영).
#    (Skill OS 6 JSON 동기화는 수동 artifactSync --write, 자동 빌드 금지)
```

## 대표 반환 형태

본 spec 은 절차서 — 반환 형태는 base SKILL `engines.industry` 참조. 갱신 후 동작은 동일.

## 갱신 빈도

- **신규 상장 종목**: 분기 1 회 일괄 (KRX listing 변경 cron 후속).
- **신생 산업 추가**: 운영자 판단 시점 (산업 분류 trend 변동 시).
- **stage 분류 정정**: 사용자 피드백 또는 사업보고서 검토 후 즉시.

자동 매핑 도구·LLM 추론 매핑 금지 (`operation.code` docstring·매핑 사람 작성 SSOT와 동일 사상).

## 기본 검증

- `taxonomy.json` JSON 파싱 정상 + 모든 stage 의 `stream` enum 안.
- `nodes.json` 의 모든 `chainId` 가 `taxonomy.json` 에 정의됨.
- 같은 stage `id` 가 산업 내 unique.
- 모든 종목코드 6 자리 string.

## 관련

- [engines.industry](/skills/engines.industry) — base SKILL
- [engines.industry.supplyChain](/skills/engines.industry.supplyChain) — stream enum SSOT
- [operation.mappingRefresh](/skills/operation.mappingRefresh) — accountMappings 측 절차 (직교)
