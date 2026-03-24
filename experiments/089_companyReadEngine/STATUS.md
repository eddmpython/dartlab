# 089 Company Read Engine

## 목표

`Company` 읽기 경로에서 **결과 완전 동일성**을 유지하면서 속도와 메모리를 함께 줄일 수 있는지 검증한다.

## 결과 요약

| 실험 | 대상 | exact | 핵심 결과 | 판정 |
|---|---|---:|---|---|
| 001 | baseline harness | 기준선 | `show/trace/topics/docs`가 대체로 700MB~1.3GB | 기준선 |
| 002 | Polars-only route split | 21/60 | `availableApiTypes`, `trace("BS")`, 일부 `show("BS")`는 exact + 26x~79x + 큰 메모리 절감 | **부분 채택** |
| 003 | topic-scoped docs only | 0/12 | docs `show()`는 40x~98x 빨라졌지만 payload 불일치 | 기각 |
| 004 | PyArrow scanner | 6/30 | exact는 `availableApiTypes`만, 002보다 느리고 무거움 | 기각 |
| 005 | DuckDB parquet_scan | 6/30 | exact는 `availableApiTypes`만, 005930 docs/meta는 baseline보다 peak 더 큼 | 기각 |
| 006 | authoritative follow-up | 66/78 | finance `show()` 36/36 exact, finance `trace()` 30/30 exact, report `show/trace`는 구조 불일치 | **finance 확정** |
| 007 | report public semantics | 구조 확인 | blockless `show("majorHolder")`는 docs block index + report row, `trace("majorHolder")`는 report+docs dual-source | 구조 확인 |
| 008 | report block index fusion | 0/6 | latest docs + synthetic report row는 22.69x~62.90x 빠르지만 docs block identity가 안 맞음 | 기각 |
| 009 | report trace source audit | 6/6 source 공식 | docs/report source row의 `rows/payloadRef/summary`가 모두 exact | 구조 확인 |
| 010 | report trace dual-source | 6/6 | `trace("majorHolder")` full dict exact, 3.32x~5.18x faster, heavy cache 0건 | **report trace 확정** |
| 011 | report block index from retrievalBlocks | 0/6 | `(rawTitle, blockIdx, blockType)` dedupe로는 blockless `show("majorHolder")` 복원 실패 | 기각 |
| 012 | topic-scoped sections exact | 18/18 | `companyOverview`, `businessOverview`, blockless `majorHolder` show exact | **docs/report show 후보 확정** |
| 013 | report hybrid generalization | 48/60 | `dividend/employee/majorHolder`는 show/trace exact, `executive` show와 `audit` trace는 실패 | 부분 채택, 014로 대체 |
| 014 | report hybrid paths v2 | 60/60 | report 대표 topic 5종 `show/trace` 전부 exact, heavy cache 0건 | **report representative path 확정** |
| 015 | current metadata rebaseline | 구조 확인 | `topics`는 이미 light, `index`만 `_sections`를 만들어 무거움 | 구조 확인 |
| 016 | index source audit | 구조 확인 | `index`의 heavy path는 docs rows이고, report rows는 `_sections`를 안 만짐 | 구조 확인 |
| 017 | index docs meta streaming | 0/6 | no-sections이지만 topic/chapter ordering이 틀려 exact 실패 | 기각 |
| 018 | index docs sections sort clone | 6/6 | `sections` 정렬 공식을 metadata-only로 복제하면 full `index` exact | **exact 확보** |
| 019 | index exact fresh rebaseline | 6/6 | fresh subprocess 기준 `1.28~2.79x`, peak `29.1~36.3%` 절감, `_sections` 0건 | **현재 최종 승자** |

## 핵심 수치

- 002 Polars-only route split
  - `availableApiTypes`: exact `6/6`, `26.44~37.08x`, peak `54.0~76.7%` 절감
  - `trace("BS")`: exact `6/6`, `45.34~78.99x`, peak `81.7~87.1%` 절감
  - `show("BS")`: exact `3/6`, `36.03~56.54x`, peak `75.9~80.6%` 절감
  - `topics`: exact `0/6`, 그래도 `6.60~10.41x`, peak `58.2~66.3%` 절감
  - `_sections` cache: `60/60`에서 생성 안 됨

- 006 Authoritative follow-up
  - finance `show()` 6종(`BS`, `IS`, `CF`, `CIS`, `SCE`, `ratios`): exact `36/36`
  - finance `trace()` 5종(`BS`, `IS`, `CF`, `CIS`, `SCE`): exact `30/30`
  - finance candidate 경로는 `_sections`, `_profileFacts`, `retrievalBlocks` 생성 `0건`
  - report `show()` 대표 topic(`majorHolder`): exact `0/6`
  - report `trace()` 대표 topic(`majorHolder`): exact `0/6`

- 012 Topic-scoped sections exact
  - `companyOverview`, `businessOverview`, `majorHolder`: exact `18/18`
  - topic별 속도는 `0.93~1.51x`, peak RSS는 대략 `314~545MB`

- 014 Report hybrid paths v2
  - 전체 `60/60` exact, heavy cache 3종 생성 `0건`
  - `show`: `30/30`, `0.85~1.53x`
  - `trace`: `30/30`, `2.43~5.00x`
  - `dividend/employee/majorHolder/executive/audit` 모두 `show/trace` exact

- 015 Current metadata rebaseline
  - `topics`: `0.074~0.087s`, peak `164.6~166.7MB`, `_sections` `0/6`
  - `index`: `3.002~4.902s`, peak `542.6~810.4MB`, `_sections` `6/6`

- 016 Index source audit
  - `finance` rows: `0.130~0.185s`, peak `185.9~198.5MB`, `_sections` `0/6`
  - `docs` rows: `3.188~5.935s`, peak `490.2~786.4MB`, `_sections` `6/6`
  - `report` rows: `0.136~0.184s`, peak `254.3~288.4MB`, `_sections` `0/6`

- 017 Index docs meta streaming
  - exact `0/6`, shape는 `6/6` 일치
  - no-sections이지만 topic/chapter ordering을 못 맞춰 기각

- 018 Index docs sections sort clone
  - exact `6/6`
  - `topicChapter + topicFirstSeq + _topicRowSortKey` 복제로 docs rows exact
  - `_sections/_profileFacts/retrievalBlocks` 생성 `0건`

- 019 Index exact fresh rebaseline
  - exact `6/6`
  - 속도: baseline 대비 `1.28~2.79x`
  - peak RSS 절감: `29.1~36.3%`
  - baseline `_sections` `6/6`, candidate `_sections` `0/6`

## 결론

1. **지금까지의 최종 승자는 `full sections`를 안 만드는 route split이다.**
   Arrow/DuckDB 교체보다, 필요한 경로만 exact semantics로 재구성하는 쪽이 이 repo에 맞았다.

2. **실험으로 exact가 확보된 구간**
   - `availableApiTypes`
   - finance `show()` 6종
   - finance `trace()` 5종
   - docs `show("companyOverview")`
   - docs `show("businessOverview")`
   - report blockless `show()` 대표 5종(`dividend`, `employee`, `majorHolder`, `executive`, `audit`)
   - report `trace()` 대표 5종
   - `topics`는 이미 light path
   - `index`는 019에서 exact + fresh subprocess 기준 실성능 개선까지 확보

3. **가장 중요한 구조 결론**
   - 현재 `index` 병목은 report가 아니라 docs rows였다
   - naive metadata-only path는 017처럼 ordering semantics에서 틀린다
   - `docs.sections`를 통째로 만들지 않아도, `topicChapter + topicFirstSeq + rowOrder + _topicRowSortKey`만 복제하면 exact metadata를 만들 수 있다

4. **실용적 의미**
   - `topics`는 건드릴 필요가 없다
   - `index`는 019 후보가 현재 가장 강한 흡수 대상이다
   - representative report path는 014, metadata/index path는 019가 현재 기준 실험 최종안이다

5. **남은 여지**
   - report rows를 raw report metadata만으로 exact화하면 `index`를 더 줄일 여지는 있다
   - 다만 지금도 019가 이미 `exact + no-sections + 1.28~2.79x + 29.1~36.3%`를 확보했으므로, 우선순위는 낮다
