# 01. 현재 상태, 전수 조사, 전문가 토론

## 1. 저장소 실측

2026-07-22 런타임 기준:

| 항목 | 실측 |
|---|---:|
| `dartlab.capabilities()` | 226 |
| 현재 capability builder가 반사하는 axis | 125 |
| analysis의 별도 실존 axis | 22 |
| 실존 axis 합계 | 147 |
| DATA_RELEASES | 42, public 32, private 10 |
| extraction concepts | 88 |
| Company capability | 64 |

현재 axis 125의 분포는 quant 48, scan 27, gather 18, macro 15, industry 9, credit 8이다. analysis 22는 별도 registry에 실재하지만 capability builder의 중앙 6엔진 목록에 빠져 있다.

패키지 규모도 단순 6엔진 mirror로 설명되지 않는다.

| layer | package | Python 파일 |
|---|---|---:|
| L1 | gather | 181 |
| L1 | providers | 245 |
| L1.5 | scan | 92 |
| L1.5 | frame | 11 |
| L1.5 | synth | 46 |
| L1.5 | reference | 25 |
| L2 | analysis | 183 |
| L2 | credit | 39 |
| L2 | industry | 24 |
| L2 | macro | 85 |
| L2 | quant | 117 |

모든 public-looking function을 바로 executable asset으로 승격하지 않는다. 전수 catalog에서는 owner와 상태를 분류하고, 실행은 owner-declared descriptor와 schema를 통과한 것만 허용한다.

## 2. Mirror 평가

강점:

- 손 axis 목록 없이 current capability 125축을 반사한다.
- wide, dict, scalar 등 shape family를 11열 canonical long으로 접는다.
- 접을 수 없는 데이터와 계약 오류를 gap으로 표면화한다.
- 공개 engine call만 사용하고 직접 parquet 접근을 금지한다.

한계:

- analysis 22축, frame, synth, reference, providers data product를 빠뜨린다.
- canonical 11열에 unit, currency, frequency, eventAt, availableAt, knownAt, revision, evidence, derivation이 없다.
- `materialize(asOf=...)`가 asOf를 engine call에 넘기지 않고 결과 period label에만 쓴다.
- graph와 nested narrative를 nonTabular gap으로 격리해 의미 있는 typed output으로 제공하지 못한다.
- 전체 결과를 concat하므로 거대 data center의 streaming plane이 될 수 없다.
- 현재 purity guard는 `simulate/mirror.py` 한 파일만 검사한다.

판정: folding prototype으로 재사용하되 data platform 정본으로 그대로 승격하지 않는다.

## 3. Universe attempts 평가

tracked U0부터 U4는 catalog, identity, temporal, provenance, CAS, receipt, sandbox, graph, query와 evidence pack을 이미 구현했다. targeted `testKernel.py` 3건도 현재 green이다.

재사용 후보:

- canonical ID와 version ID
- valid time, known time, revision, visibility 계약
- resource, object, evidence catalog
- capability admission, bounded output, receipt, replay
- graph statement와 source locator
- coverage와 snapshot digest

data core에서 제외:

- blog AST와 media retrieval
- AI hybrid retrieval와 answer flow
- simulator receipt adapter
- U5 spatial, layout, tile, 3D

특히 simulator adapter를 data core로 옮기면 `simulate -> data`와 `data -> simulate`가 동시에 생긴다. 이는 즉시 실패다.

ignored U5 사용자 작업은 Python source 19개 규모의 실작업이다. cleanup 대상이 아니다. stash, reset, clean, attempts 일괄 삭제를 금지한다.

## 4. 전문가 토론

### 4.1 공통 합의

세 관점 모두 다음에 동의했다.

- 사용자 요구 범위는 일부 분석 엔진이나 AI가 아니라 L1, L1.5, L2 전체다.
- data는 독립 public engine이어야 한다.
- factor store는 projection이다.
- simulator와 외부 프로세스가 같은 계약을 사용해야 한다.
- 기존 owner의 source와 계산 소유권은 유지해야 한다.
- Universe control plane과 Mirror folding을 선별 결합해야 한다.

### 4.2 API 논쟁

검토한 안:

1. `data("quant.quality", query=...)`
2. `data("catalog" | "query" | "factor" | "lineage", ...)`
3. `data("catalog" | "query", assets=..., projection=...)`

채택은 3번이다.

asset-first 안은 단일 자산에는 편하지만 asset이 data axis처럼 보여 capability와 data product identity가 섞이고, 다중 asset과 타입 명세가 약해진다.

4축 안은 factor와 lineage를 query와 같은 작업 차원으로 오인한다. factor, graph, narrative가 늘 때 axis가 계속 증가하고, lineage를 별도 호출하면 data와 snapshot이 어긋날 수 있다.

두 축 안은 axis를 고정하고 asset과 projection을 typed query 안에 둔다. 자동 흡수, 타입 안정성, 외부 JSON schema, 기존 engine-axis 계약을 동시에 만족한다.

## 5. 과거 답변이 좁아진 원인

현재 `reference/capability/builder.py`가 scan, macro, gather, industry, credit, quant만 중앙 tuple로 반사하고 Mirror가 그 결과만 소비한다. 코드가 보이는 범위를 올바른 제품 범위로 잘못 일반화한 것이 원인이다. 이 한계를 설계로 정당화하지 않고 discovery 구조 자체를 고친다.
