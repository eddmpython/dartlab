# 00. 제품 헌장과 불변식

## 1. 해결할 문제

DartLab에는 데이터와 계산이 부족한 것이 아니다. L1의 gather와 providers, L1.5의 scan, frame, synth, reference, L2의 analysis, macro, quant, industry, credit가 각자의 올바른 자산을 소유한다. 문제는 외부 사용자와 상위 제품이 이 전체를 같은 식별자, 시간, 계보, 예산 계약으로 발견하고 조회하는 독립 표면이 없다는 점이다.

현재 소비자는 각 엔진의 반환형, target 위치, period 표현, 오류, 캐시, 계보를 따로 알아야 한다. simulator의 Mirror는 일부 축을 정규화하지만 전체 데이터 플랫폼이 아니라 6개 엔진용 내부 물질화 도구다. Universe attempts는 더 넓은 control plane을 증명했지만 simulator가 사용할 수 없는 상위 제품으로 설계됐다.

Data Workbench는 이 두 장점을 합치되 둘의 잘못된 경계를 승계하지 않는다.

## 2. 범위

| 레이어 | owner | 작업대가 제공할 것 |
|---|---|---|
| L1 | gather, providers | 원천 source, provider data product, 공시, 재무, 가격, 수급, 뉴스와 resource descriptor |
| L1.5 | scan, frame, synth, reference | 횡단 table, panel과 narrative view, 정적 reference, 시나리오와 공유 가공 계약 |
| L2 | analysis, macro, quant, industry, credit | owner가 선언한 분석 output과 axis capability |

상위의 simulate, story, Universe, AI, MCP, UI는 소비자다. 이들을 data core의 source owner로 역수입하지 않는다.

## 3. 사용자 가치

### 3.1 외부 Python 사용자

`dartlab.data` 하나로 자산을 찾고, 여러 owner의 자산을 한 query에 묶고, factor 또는 native 형태로 받는다. 각 엔진의 내부 import 경로나 parquet 위치를 알 필요가 없다.

### 3.2 simulator

같은 asset ID와 PIT 계약으로 state input을 고정한다. latest 값을 과거값처럼 재라벨링하지 않으며, 재구성 불가능하면 명시적 gap으로 기권한다.

### 3.3 운영자와 감사자

값과 같은 result에 snapshot, source revision, execution receipt, coverage, gap, visibility, license를 확인한다.

### 3.4 미래 제품

Universe, story, AI, UI가 서로 다른 내부 reader를 만들지 않고 같은 semantic query plane을 사용한다.

## 4. 제품 불변식

### D01. owner truth

원천 수집은 gather, provider 변환과 load는 providers, 횡단 가공은 scan, 도메인 계산은 각 L2 owner가 정본이다. data에서 이를 재구현하지 않는다.

### D02. 한 catalog, 분산 소유

통합 catalog는 owner descriptor의 projection이다. 기존 registry를 하나의 대형 registry 파일로 복사하거나 삭제하지 않는다.

### D03. axis 두 개

공개 axis는 `catalog`, `query`뿐이다. asset 수와 projection 종류가 늘어도 공개 axis가 늘지 않는다.

### D04. 표현 다형성

문서, graph, narrative, table을 모두 scalar long으로 접지 않는다. `native`는 owner schema를 보존하고, `records`는 tagged union, `factor`는 scalar-compatible observation에만 허용한다.

### D05. PIT fail-closed

`knownAt` 또는 historical revision을 재구성할 수 없는 자산은 `PIT_UNSUPPORTED` 또는 `VINTAGE_UNAVAILABLE`로 거부한다. 현재 값을 과거 `asOf` 라벨로 바꾸지 않는다.

### D06. data와 lineage의 원자성

lineage는 별도 후속 호출이 아니다. 같은 snapshot의 result에 포함한다. 상세 graph는 같은 query의 projection option으로 요청한다.

### D07. bounded by default

모든 query는 row, byte, time, concurrency budget과 continuation을 가진다. no-arg나 wildcard가 300GB 원천을 물질화하지 않는다.

### D08. 가시성과 라이선스

private locator, token, 제한 source는 정책을 통과하지 못하면 결과나 오류 메시지에 노출하지 않는다.

### D09. 장애 정직성

단일 asset의 정상 결손과 provider 전체 장애를 같은 partial gap으로 숨기지 않는다. systemic failure는 query status를 실패로 올린다.

### D10. 단방향 의존

`simulate, story, universe, ai -> data -> L2 -> L1.5 -> L1 -> L0` 방향을 지킨다. data가 simulate, story, AI를 import하면 실패다.

## 5. 비목표

- 모든 원천을 새 DB로 복사하는 data lake
- persistent factor warehouse를 기본값으로 만드는 것
- 모든 내부 함수를 공개 capability로 승격하는 것
- blog, media, RAG, 3D spatial을 data core에 포함하는 것
- simulator result를 data core가 직접 등록해 양방향 의존을 만드는 것
- 외부 공개를 이유로 private data를 노출하는 것
- 전 엔진 호출 결과를 한 DataFrame으로 강제 concat하는 것

## 6. 계층 결정

Data Workbench는 제품상 최상위 데이터 표면이고 코드상 L2와 simulate 사이의 platform layer다. 레이어 숫자는 제품 등급이 아니라 import 방향이다.

```text
L1 gather/providers
  -> L1.5 scan/frame/synth/reference
  -> L2 analysis/macro/quant/industry/credit
  -> data platform
  -> simulate/story/Universe
  -> ai/mcp/UI
```

기존 문서의 `data는 엔진이 아니다`, `simulate가 Universe를 import하면 kill`, `개별 데이터 작업대를 폐기하고 engine verb만 쓴다`는 결정은 본 ADR이 현재 요구 범위에 한해 supersede한다. 원문은 이력으로 보존하되 현재 정본 링크를 본 계획으로 바꾼다.
