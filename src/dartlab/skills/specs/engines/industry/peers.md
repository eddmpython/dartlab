---
id: engines.industry.peers
title: Industry — Peers 추출 (peers)
category: engines
kind: curated
scope: builtin
status: observed
purpose: 단일 종목의 같은 산업·같은 공정 stage peer 종목 추출 SSOT — analysis/scan/quant 등 다른 엔진에 peer universe 를 전달할 때 본 spec 의 두 형식 (코드 list / dict list) 중 하나만 사용.
whenToUse:
  - peers
  - peer 그룹
  - peer 종목
  - 동종업종
  - peer universe
  - same stage peer
  - peer 추출
  - peer 비교
sourceRefs:
  - dartlab://skills/engines.industry.peers
capabilityRefs:
  - industry
  - Company.industry
knowledgeRefs:
  - engines.industry
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
linkedSkills:
  - engines.industry
  - engines.scan
  - engines.analysis
  - engines.quant
---

## 엔진 역할

`industry` 엔진의 *peer 추출* sub-axis. 단일 종목의 같은 산업·같은 공정 stage peer 종목 list 를 두 형식으로 노출. analysis/scan/quant/credit 등 *다른 엔진으로 peer universe 전달* 시 본 spec 의 형식 규약 그대로 따른다 (전체 dict 통째 전달 금지 — `engines.industry` forbidden 룰).

## 공개 호출 방식

```python
import dartlab

# 1. Company-bound (코드 list)
c = dartlab.Company("005930")
peer_codes = c.industry().peers
# → ["000660", "042700", ...]  (같은 stage 종목코드)

# 2. industryBadge (dict list, 자동 부착)
result = c.panel("IS")
peer_dicts = result.data.industryBadge.peers
# → [{"stockCode": "000660", "corpName": "SK하이닉스"}, ...]

# 3. 산업·stage 직접 추출
nodes = dartlab.industry("semiconductor", stage="fab")
peer_codes = nodes["종목코드"].to_list()
```

## 호출 동작

1. `Company.industry()` → dict 반환의 `peers` 는 코드 list — 다른 엔진 호출 직접 사용.
2. `Company.panel(...).data.industryBadge.peers` → dict list — UI/문서 표시 (corpName 포함).
3. 두 형식 SSOT 는 동일 매칭 — `nodes.json` 의 같은 stage 종목 (확률 0.5 이상 신뢰 매칭).
4. peer 가 0 개면 산업·stage 분류 미등록 — 빈 list 반환 (None 아님). 추측 금지.

## 대표 반환 형태

```text
Company("005930").industry().peers
→ list[str]                 # ["000660", "042700", ...]  같은 stage 종목코드
```

```text
Company("005930").industry()["peers"]
→ list[dict]
   stockCode : str          # 6 자리
   corpName : str           # 한글
```

```text
dartlab.industry("semiconductor", stage="fab")
→ DataFrame                  # 종목코드 컬럼 포함 — engines.industry 본 SKILL 참조
```

## 기본 실행 순서

1. **다른 엔진 호출** — `c.industry().peers` 코드 list 만 추출 → `dartlab.analysis(...peers=...)` 또는 `dartlab.scan(...universe=...)` 직접 전달.
2. **UI/답변 표시** — `industryBadge.peers` dict list 그대로 (corpName 동행).
3. **산업 전체 같은 stage peer** — `dartlab.industry(industryId, stage=...)` 의 종목코드 컬럼 사용.
4. peer 매칭 신뢰도 (`Company.industry().confidence`) 가 0.5 미만이면 peer list 도 신뢰 한계 명시.

## 기본 검증

- 두 형식 peer list 의 길이 일치 (industryBadge.peers ↔ Company.industry().peers).
- 모든 peer 종목코드가 6 자리 string.
- peer 0 개 = 빈 list (None 아님).
- self code (호출 종목 자체) 가 peers 에 포함되지 않음 (자기 제외).

본 spec 은 공개 실행 문서다. peer 형식·추출 룰이 변경되면 본 파일을 같은 변경에서 갱신한다.

## 관련

- [engines.industry](/skills/engines.industry) — base SKILL (forbidden 룰: 전체 dict 통째 전달 금지)
- [engines.scan](/skills/engines.scan) — universe 인자로 peer list 받음
- [engines.analysis](/skills/engines.analysis) — peer benchmark percentile
- [engines.quant](/skills/engines.quant) — peer 횡단면 factor 계산
