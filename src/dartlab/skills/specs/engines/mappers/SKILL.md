---
id: engines.mappers
title: Mappers (계정 정규화)
kind: curated
scope: builtin
status: observed
category: engines
purpose: Mappers 는 DART/EDGAR 원문 계정명을 공통 snake_id 로 정규화하는 *내부 모듈* 이다. 사용자 직접 호출 capability 가 아니라, Company.panel / scan 결과 안에서 자동 적용. 본 skill 은 매핑 규칙을 *AI 가 컬럼 정규화에 활용* 할 때 참조한다. 트리거 — '항목 매핑', '컬럼 정규화', 'snake_id 변환'.
whenToUse:
  - mappers
  - 계정 정규화
  - snake_id
  - 컬럼 매핑
  - 한글 → 영문
  - rawName → standardName
inputs:
  - 한국어 계정명 (예 — 총자산)
  - topic (BS · IS · CF · CIS · SCE)
outputs:
  - snake_id (예 — total_assets)
  - 매핑 metadata (category · type · confidence)
capabilityRefs: []
toolRefs:
  - EngineCall
  - RunPython
knowledgeRefs:
  - start.dartlabSkillOs
  - engines.company
  - engines.dataHub.foundation
sourceRefs:
  - dartlab://skills/engines.mappers
requiredEvidence:
  - topic
  - rawName
  - snakeId
  - source
  - executionRef
  - sourceRef
expectedOutputs:
  - 정규화된 snake_id
  - 매핑 신뢰도 (정확/부분/실패)
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
failureModes:
  - snake_id 추측 (반드시 `normalizeColumn(topic, hint)` 또는 `columnsFor(topic)` 결과 인용)
  - topic 누락 — 같은 한글 이름이 BS/IS/CF 에 다 있을 수 있음 ("당기순이익" 등)
  - rawName 의 한자/영문 변형 (`(주)` · `(연결)` · ` ` 공백) 미정규화
forbidden:
  - 매핑 결과 없이 한글 계정명을 직접 컬럼명으로 사용 금지.
  - 매핑 신뢰도 낮을 때 (`confidence < 0.8`) 답변에 그대로 쓰지 않는다.
examples:
  - 총자산 → total_assets 정규화
  - 당기순이익 (topic=IS) → net_income
  - normalizeColumn 으로 RunPython 안에서 동적 정규화
  - 새 사업보고서 항목 매핑 추가
procedure:
  - RunPython prelude 의 `normalizeColumn(topic, hint)` 사용 — 한글/snake/alias → 표준 snake_id.
  - 가능 컬럼 목록은 `columnsFor(topic)` — snake_id · label · aliases.
  - topic 자체는 `availableTopics()` (BS/IS/CF/CIS/SCE).
  - 매핑 정의는 `src/dartlab/reference/data/accountMappings.json` 단일 SSOT (DART mappings/layers + EDGAR edgar 구획 통합).
  - 신규 매핑 추가는 운영자 트리거 발화 ("매퍼 정리"/"mapping refresh") → `src/dartlab/skills/specs/operation/mappingRefresh.md` 4 단계 — 관측 ledger → `src/dartlab/reference/mapping/mappingLedgerCompact.py` → `src/dartlab/reference/mapping/mappingReview.py` confirm/reject/alias/defer → `src/dartlab/reference/mapping/mappingPromote.py` apply.
  - prod JSON 단독 권한 진입점은 `src/dartlab/reference/mapping/mappingPromote.py` 만. atomic write + `_metadata.{lastUpdate,addedCount,promoteCommit}` 갱신 + `AccountMapper.release()` 자동 호출.
linkedSkills:
  - engines.company
  - engines.dataHub.foundation
source:
  type: manual_skill
  format: markdown
lastUpdated: '2026-05-16'
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## 엔진 역할

`mappers` 는 사용자 capability 가 아니라 *내부 모듈* 이다. DART 사업보고서·재무제표·주석의 한글 계정명을 dartlab 공통 snake_id 로 정규화한다. EDGAR 측은 SEC GAAP 태그 → 같은 snake_id (양쪽 SSOT 동등).

AI 가 직접 쓸 자리는 `RunPython` 안의 prelude 헬퍼 — `normalizeColumn(topic, hint)`, `columnsFor(topic)`, `availableTopics()`. 매핑 자체 편집은 운영자 절차 (`src/dartlab/mappers/{topic}.json` 직접 수정).

## 공개 호출 방식

```python
# RunPython 안에서 — prelude 자동 노출
import dartlab
c = dartlab.Company("005930")
bs = c.panel("BS", freq="Q")

# 한글 → snake_id 정규화 (추측 금지)
col = normalizeColumn("BS", "총자산")        # → "total_assets"
col2 = normalizeColumn("IS", "영업")          # → "operating_profit"

# 가능 컬럼 목록 (snake_id · label · aliases)
cols = columnsFor("BS")
print(cols)

# 가능 topic
print(availableTopics())   # BS / IS / CF / CIS / SCE
```

## 강행 호출 룰 (agent 답변 품질 회귀 차단)

mappers 는 *내부 정규화 모듈* — Company.panel / scan 결과 안에서 자동 적용. 다음 3 룰 강행:

1. **mappers 단독 EngineCall 금지** — `EngineCall(apiRef="mappers")` 호출 없음. Company.panel / scan 결과의 `snake_id` 컬럼은 이미 정규화 완료.
2. **snake_id 임의 추측 금지** — `normalizeColumn(topic, hint)` 또는 `columnsFor(topic)` RunPython 안에서 호출해 정확 매칭 후 사용. "total_equity" 같은 추측 키로 dict 접근 시 KeyError (P5 RunPython 회귀 사례).
3. **`-표준계정코드 미사용-|...` fallback 데이터는 표준화 후보로 표기** — Company.panel 결과 dict 의 nonstd_ 컬럼은 매핑 미완. 답변 본문에 "표준화 미완 N 건" 명시 + 임의 합산 금지.

## 호출 동작

`normalizeColumn(topic, hint)` — `topic` 안에서 `hint` 와 매칭되는 표준 snake_id 반환. 매칭 실패 시 `None` (또는 ValueError, 구현 따라). 한글 풀네임 · 부분 키워드 · snake_id 자기 자신 모두 받음.

`columnsFor(topic)` — 해당 topic 의 모든 표준 컬럼 list. 각 항목은 `snake_id` · `label` (한글) · `aliases` (한글/영문 변형) · `category` · `type`.

매핑 데이터는 `src/dartlab/mappers/{topic}.json` 의 `_metadata.description` + `key:value` (한글 → 영문 canonical) + `category/type` 분류.

## 6 매퍼 (topic 별)

| topic | 파일 | 책임 |
| --- | --- | --- |
| BS | `bs.json` | 재무상태표 — 자산·부채·자본 계정 |
| IS | `is.json` | 손익계산서 — 매출·비용·이익 계정 |
| CF | `cf.json` | 현금흐름표 — 영업·투자·재무 활동 |
| CIS | `cis.json` | 포괄손익계산서 — OCI 항목 |
| SCE | `sce.json` | 자본변동표 — 자본 구성 변동 |
| ratios | `ratios.json` | 재무비율 — ROE · 부채비율 등 파생 |

공통 유틸 (`mappers/common.py`) 가 모든 파서·매퍼에서 공유. 한자/영문/공백/괄호 변형 정규화.

## 대표 반환 형태

```text
normalizeColumn("BS", "총자산")
→ "total_assets"  (str)

columnsFor("BS")
→ list[dict]
   snake_id : str
   label : str         # 한글 표시명
   aliases : list[str] # 변형 ("총 자산", "자산총계", "Total Assets")
   category : str      # "asset" / "liability" / "equity"
   type : str          # "current" / "non-current" / "total"
```

## evidence 기준

매핑 결과는 `topic` · `rawName` · `snakeId` · `confidence` · `source` (DART/EDGAR) 를 남긴다. confidence 낮으면 답변에 명시.

## 기본 검증

매핑 정의 변경은 본 skill 의 6 매퍼 표 동시 갱신. 신규 매핑 추가 시 `category` · `type` 메타 함께 — AI 가 새 항목을 자동 분류하는 학습 데이터로 작동.

## 학습 파이프라인 (반자동 사이클)

### 저장 위치 (SSOT 인덱스)

| 자산 | 경로 | 내용 | 갱신 방식 |
|---|---|---|---|
| 계정 매핑 SSOT (DART+EDGAR) | `src/dartlab/reference/data/accountMappings.json` | standardAccounts + mappings + layers(5) + edgar | `mappingPromote.py --layer` 또는 직접 편집 + `release()` |
| 단일 소유 엔진 | `src/dartlab/core/accounts/` | data·normalize·edgar·labels·aliases (L0) | — |
| Notes 구조 학습 | `src/dartlab/reference/data/notesStructure.json` | 2,700 종목 notes 항목 `{type, category, frequency}` | `scanAll()` 자동 갱신 |
| 로더 | `src/dartlab/core/accounts/data.py::loadAccounts` (옛 `labels._loadAccountMappings` 위임) | SSOT 단일 로더 (lru_cache) | — |
| 캐시 무효화 | `src/dartlab/core/accounts/data.py::release` (옛 `AccountMapper.release` 위임) | JSON 직접 편집 후 호출 | — |

**2026-06 통합**: DART·EDGAR 매핑이 단일 파일 `accountMappings.json` + 단일 소유 엔진
`core/accounts/` 로 통합 (옛 EDGAR 별도 `mapperData/` 흡수, 5 in-code dict 흡수). 옛
mapper.py·labels.py 는 위임 facade. 구조·관리 정본은 [operation.mappingRefresh](/skills/operation.mappingRefresh) §0.

### 사이클 4 단계 — 운영자 트리거 발동 (cron 없음, 직접 박는 정공)

본 절차의 핵심: mapper 의 34,000+ 매핑은 *모두 운영자가 미커버 한글명을
보고 직접 standardAccounts.snakeId 와 짝지어 박은 결과*. 자동 학습 X.
파이프라인은 그 수동 박기를 효율화하는 도구이며 최종 매핑 결정은 사람.

```
1. polars lazy + anti-join 전수 미커버 추출 (Bash inline, ~2.5 초)
   pl.scan_parquet('data/dart/finance/*.parquet').filter(...)
     .with_columns(nm_n=norm(account_nm), id_n=stripPrefix(account_id))
     .join(mappingsKeys, on='account_id', how='anti')
     .join(mappingsKeys, on='id_n',       how='anti')
     .join(mappingsKeys, on='account_nm', how='anti')
     .join(mappingsKeys, on='nm_n',       how='anti')
     .group_by(['account_id','account_nm','sj_div']).agg(occ, stockCodes)
   → 미커버 그룹 ≈ 33k (false-positive 약 33% 포함)

2. mapper.map() Python 더블체크 (~0.2 초)
   AccountMapper.get().map(accountId, accountNm) 12 단계 fallback 호출
   (사전 hit 우선 → synonym 정규화 → 공백/괄호/하이픈 역인덱스 → 액 suffix).
   None 반환 행만 진짜 미커버 — anti-join 으로 못 잡은 synonym/정규화 단계
   false-positive 제거.
   → 진짜 미커버 ≈ 22k.
   sj_div 분포: SCE 4,107 (별도 buildSceMatrix 흐름이라 무시),
                BS/IS/CF/CIS 18,000+ 그룹.

3. SA korName substring 매칭 후보 추출
   강한 후보 filter (occ ≥ 5, disp ≥ 3) ≈ 1.8k.
   각 후보의 account_nm 정규화 → standardAccounts.korName 정규화와
   양방향 substring + 길이 비율 score 계산. score ≥ 0.70 후보 top 1 추출.

4. 운영자 박기 — 액션 단어 보존 검토 후 batch JSON patch
   stdout 후보 list 사람이 한 줄씩 검토:
     OK 패턴 — prefix (유동·장기·외화), 숫자 (1./V.), suffix (조정·등·순액),
               오타 (지배지업 ← 지배기업), 잘림 (당기손익측정금융자)
     SKIP 패턴 — 액션 빠진 환각 (자산 처분손실 → 자산 자체),
                의미 반대 (장기사채 → 단기사채)
   확정 매핑을 accountMappings.json::mappings 에 batch 추가 (atomic write,
   single-line 보존 separators=(',', ':')). _metadata.addedCount 누적.
   AccountMapper.release() + lru_cache.cache_clear() 호출.
```

운영자 트리거 발화 ("매퍼 정리해줘" / "nonstd 정리" / "mapping refresh") 시
운영 SSOT `src/dartlab/skills/specs/operation/mappingRefresh.md` 절차서가
4 단계 inline Bash 실행. 각 단계 사이 운영자 결정 필수 — 어떤 자동화도
prod JSON 을 직접
수정하지 않는다. cycle 당 30~80 매핑 추가, 추가율은 cycle 마다 둔화
(신중도 증가). 본 사이클 138 매핑 박은 결과 카카오 035720 nonstd 행
66 → 28 (58% 감소).

### 안전 자동학습의 정의 (5 신호)

"자동 제안 가능" 의 객관 기준은 `mappingSignals.evaluate` 의
`S1 ∧ S2 ∧ (S3 ∨ 유효 S4) ∧ ¬S5` (`autoEligible: true`):

| 신호 | 기준 | 거부 시그널 |
|---|---|---|
| S1 빈도 | occurrenceCount ≥ 5 | < 5 = singleton 노이즈 |
| S2 회사 분산 | 고유 stockCode ≥ 3 | 1 사 전용 = 사내 계정 |
| S3 한글 정규화 매칭 | standardAccounts.korName Levenshtein 유사도 ≥ 0.85 | < 0.85 = 의미 모호 |
| S4 IFRS 동의어 1 hop | accountId/accountNm 정규화 후 mappings 직 hit | 1 hop 안에 없음 |
| S5 오타 거부 | jamo 분해 → 1 자모 차이 IFRS korName 존재 시 거부 | 오타 의심 = false + suggestedFix 노출 |

`autoEligible=True` 도 *자동 반영* 이 아니다 — 운영자 `mappingReview.py
confirm` 후 `mappingPromote.py apply` 까지 사람 결정 2 번 필요.

### 사용자 호출 (학습은 내부, 호출은 prelude)

학습 결과 활용은 위 "공개 호출 방식" 의 `normalizeColumn(topic, hint)` / `columnsFor(topic)` — RunPython prelude 자동 노출. 직접 JSON 편집은 운영자 절차.

### 검증

```python
from dartlab.reference.mappers.accountMapper import AccountMapper
mapper = AccountMapper()
print(mapper.stats())  # MapperStats(name='account', totalEntries=34249, coverage=1.0, lastUpdated='2026-03-09')
print(mapper.lookup("매출액"))  # {'snakeId': 'sales', ...}
# 본 lookup() 은 본진 providers/dart/finance/mapper.py::AccountMapper.map() 위임 —
# 12 단계 fallback (사전 hit 우선 + synonym + 변형 흡수) 일관 적용. SSOT 단일화.
```
