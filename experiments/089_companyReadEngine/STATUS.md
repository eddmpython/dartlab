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
| 010 | report trace dual-source | 6/6 | `report + docs` 조합 trace dict가 exact, 3.66x~4.74x faster | **trace 확정** |
| 009 | report trace source audit | 공식 확인 | `trace("majorHolder")`의 docs/report source 구성요소가 모두 lightweight 경로와 6/6 일치 | 구조 확인 |
| 010 | report trace dual-source | 6/6 | `trace("majorHolder")` full dict exact, 3.32x~5.18x faster, heavy cache 0건 | **report trace 후보** |
| 011 | report block index from retrievalBlocks | 0/6 | `(rawTitle, blockIdx, blockType)` dedupe로는 blockless `show("majorHolder")` 복원 실패 | 기각 |

## 핵심 수치

- baseline
  - `show("BS")`: `5.468~7.748s`, peak `688.3~908.3MB`
  - `trace("BS")`: `6.810~9.686s`, peak `973.7~1362.0MB`
  - `show("companyOverview")`: `5.875~7.553s`, peak `691.6~964.0MB`
  - `topics`: `6.104~8.093s`, peak `714.4~902.9MB`

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

- 007 Report public semantics
  - 대표 report topic은 `6/6` 모두 `majorHolder`
  - public `show("majorHolder")`: `6/6` 모두 block index `Nx4`
  - block index source 분포: `docs N개 + report 1개`
  - `show("majorHolder", reportBlock)` payload는 direct `_showReportTopic("majorHolder")`와 `6/6` exact
  - public `trace("majorHolder")`: `6/6` 모두 `primarySource=report`, `fallbackSources=["docs"]`

- 008 Report block index fusion
  - raw docs latest block index + synthetic report row: exact `0/6`
  - 속도는 `22.69~62.90x` 빨랐지만 baseline docs block 수를 크게 과소계산
  - `majorHolder`는 latest-only docs 경로로는 public block identity를 맞출 수 없음

- 009 Report trace source audit
  - docs source 공식: `rows/payloadRef/summary`가 `6/6` 모두 exact
  - report source 공식: 006 direct report trace helper와 `rows/payloadRef/summary`가 `6/6` 모두 exact
  - `trace("majorHolder")`는 source별로 lightweight exact reconstruction이 가능함

- 010 Report trace dual-source
  - `trace("majorHolder")`: exact `6/6`
  - 속도: baseline 대비 `3.66~4.74x`
  - candidate 경로는 `_sections`, `_profileFacts`, `retrievalBlocks` cache 생성 `0건`
  - candidate peak RSS: `568.7~920.4MB`

- 011 Report block index from retrievalBlocks
  - `show("majorHolder")` blockless index: exact `0/6`
  - `(rawTitle, blockIdx, blockType)` 최신 우선 dedupe는 종목별로 block 수가 과소/과다 모두 발생
  - `retrievalBlocks`만으로는 public block identity key가 부족함

- 003 Topic-scoped docs
  - docs `show()` exact `0/12`
  - 속도는 `40.81~97.58x` 빨라졌지만 block identity가 baseline과 다름

- 004 PyArrow
  - exact `6/30`, 전부 `availableApiTypes`
  - 002보다 실용성이 낮음

- 005 DuckDB
  - exact `6/30`, 전부 `availableApiTypes`
  - 005930 docs/meta에서는 peak `882~887MB`로 오히려 악화

## 결론

1. **지금 당장 승자는 002 방향이고, 006이 finance authoritative path, 010이 report trace fast path를 확정했다.**
   `full sections`를 안 만드는 route split 자체는 맞았고, finance `show()/trace()`와 report `trace("majorHolder")` exact path가 입증됐다.

2. **정확히 같은 결과가 이미 입증된 구간**
   - `availableApiTypes`
   - finance `show()` 6종
   - finance `trace()` 5종
   - report `trace("majorHolder")`

3. **report topic의 현재 public semantics**
   - blockless `show("majorHolder")`는 direct report payload가 아니라 `docs block index + report row`
   - `show("majorHolder", reportBlock)`는 direct report payload와 exact
   - `trace("majorHolder")` exact 재현에는 `report + docs fallback` 둘 다 필요하고, 그 경로는 010에서 exact가 확인됐다

4. **아직 exact가 아닌 구간**
   - `topics`
   - `index`
   - docs `show()`
   - report blockless `show()`
   - `majorHolder` 외 report `trace()`

5. **의미 있는 기술 결론**
   - 이 repo 병목은 parquet scan보다 **그 뒤의 Python 재구성**이다.
   - 그래서 Arrow/DuckDB를 넣어도 002보다 좋아지지 않았다.
   - report topic은 `trace()`와 `show()`의 난이도가 다르다. `trace()`는 source 공식이 비교적 단순하지만, blockless `show()`는 docs block identity가 핵심 병목이다.
   - 다음 단계는 `topics/index/docs/report blockless show()`의 exact reconstruction 규칙을 실험에서 더 좁히는 것이다.
