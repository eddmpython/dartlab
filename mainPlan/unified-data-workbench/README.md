# DartLab Unified Data Workbench

상태: 구현과 hardening 진행. 355개 catalog, 172개 queryable asset, DART와 EDGAR 원천 및 계산 owner paging, mixed outer continuation, immutable generation과 receipt 기반 재생을 검증했다. 2026-07-26에는 universe 계획 중 원천 자동 갱신을 제거하고 local-only snapshot 경계를 추가했다. 통합 회귀 637개를 수집해 634개 통과, 환경 의존 3개 skip을 확인했다. 별도 프로세스 격리 감사 21개도 통과했고 owner child 50회에서 zero-live 50회와 artifact residue 0개를 확인했다. 작업대 순수성 검사는 계층 역전과 원천 직독 0건을 확인했다.

## 한 문장 정의

**DartLab Data Workbench는 L1, L1.5, L2가 소유한 모든 데이터 자산과 계산 capability를 하나의 카탈로그와 질의 계약으로 발견하고, PIT, 계보, 가시성, 예산을 보존한 채 외부 프로세스와 simulator에 동일하게 제공하는 독립 데이터 플랫폼 엔진이다.**

팩터 스토어는 이 제품의 정체성이 아니다. scalar-compatible observation을 `factor` 형태로 투영하는 한 가지 query projection이다.

## 최상위 결정

1. 실제 엔진 폴더 `src/dartlab/data/`와 공개 진입점 `dartlab.data(...)`를 만든다.
2. 공개 axis는 `catalog`, `query` 두 개로 고정한다.
3. asset identity는 `AssetRef`, 데이터 표현은 typed projection으로 분리한다.
4. `factor`, `native`, `records`, `graph`, `narrative`, `resource`는 새 axis가 아니라 query projection이다.
5. lineage, coverage, gap, snapshot, receipt는 데이터와 같은 `DataResult`에 결박한다.
6. 원천 취득과 도메인 계산은 기존 owner가 계속 소유한다. data는 복제 저장소나 계산 god module이 아니다.
7. data는 L1, L1.5, L2 위, simulate와 story 아래의 플랫폼 계층이다.
8. simulator는 같은 query 계약을 소비한다. data가 simulate를 import하는 역방향은 금지한다.
9. 자동 발견은 중앙 엔진 손 목록이 아니라 owner-declared metadata provider로 수행한다.
10. 전체 호출은 전체 RAM 적재를 뜻하지 않는다. catalog, plan, bounded materialization, continuation이 단일 진입점에서 끝난다는 뜻이다.
11. 한 query의 `DataRequest`마다 서로 다른 projection을 지정해 factor, narrative, graph, native view를 같은 result envelope로 받을 수 있다.
12. partition은 구조화 lineage, quality assertion과 Arrow transport를 제공한다.
13. catalog `snapshotId`와 실제 반환 content의 `dataSnapshotId`를 분리하고 partition마다 `contentHash`를 둔다.
14. 전종목 continuation은 첫 `DataResult`의 `iterPages()` 또는 `iterAllArrowBatches()`가 자동 소비한다.
15. feature registry, observation, vintage, PIT query는 data 공통 계약이며 simulator와 외부 소비자가 같은 의미 규칙을 쓴다.
16. 전종목 원천 paging과 계산된 전종목 factor paging은 구분한다. `analysis.dartFinancialFeatures`와 `analysis.edgarFinancialFeatures`는 각 시장의 현재 상장 universe를 계산형 owner continuation으로 순회한다.
17. pageable resource, 계산 owner, 일반 eager asset을 한 query에 섞어도 외부에는 outer continuation 하나만 노출한다. 일반 eager owner는 fresh child에서 한 번 실행해 content seal로 고정한다.
18. `runtime`, `reuse`, `refresh`, `offline` materialization 정책은 기존 `query` axis에 속한다. 별도 factor-store axis를 만들지 않는다.
19. immutable generation은 asset, source, query, universe, contract, schema의 exact pin 여섯 개로 식별한다. READY 전 세대는 보이지 않고 receipt 재생은 owner와 source를 호출하지 않는다.
20. cold `refresh`는 terminal generation을 동기적으로 완성한 뒤 첫 page와 receipt를 반환한다. warm `reuse`와 receipt 기반 `offline`은 저장된 page를 바로 읽는다.
21. Data Workbench query는 universe를 해소하는 동안 source를 갱신하지 않는다. 이미 존재하는 owner snapshot을 읽어 pin하며, 갱신은 gather와 pipeline이 소유한다.

## 공개 계약

```python
import dartlab

catalog = dartlab.data(
    "catalog",
    query=CatalogQuery(layers=("L1", "L1.5", "L2"), search="quality"),
)

result = dartlab.data(
    "query",
    assets=("quant.quality", "scan.ratio"),
    query=DataQuery(
        subjects=("005930",),
        projection=FactorProjection(measures=("qmj", "roe"), unit="percent"),
    ),
)
```

같은 진입점에서 `analysis.edgarFinancialFeatures`를 `knownAt`과 `FactorProjection`으로 요청하면 실제 filing cutoff를 보존한 revision-aware feature row를 얻는다. 현재 retained companyfacts의 이력 한계 때문에 이 자산은 `latestRetained`, `periodOnly`, `conditional`로 정직하게 반환한다.

DART와 EDGAR 현재 상장 universe 전체도 호출자가 ticker를 반복하지 않고 한 query로 등록한다.

```python
first = dartlab.data(
    "query",
    query={
        "requests": [
            {
                "assetId": "analysis.dartFinancialFeatures",
                "requestId": "krListedPit",
                "universe": {"markets": ["KR"], "membership": "listed"},
                "projection": {
                    "kind": "factor",
                    "measures": [
                        "financial.revenue",
                        "financial.operatingMargin",
                    ],
                },
                "time": {"knownAt": "20260723"},
            },
            {
                "assetId": "analysis.edgarFinancialFeatures",
                "requestId": "usListedPit",
                "universe": {"markets": ["US"], "membership": "listed"},
                "projection": {
                    "kind": "factor",
                    "measures": [
                        "financial.revenue",
                        "financial.operatingMargin",
                    ],
                },
                "time": {"knownAt": "20260723"},
            }
        ],
        "budget": {
            "maxRows": 100000,
            "maxBytes": 64 * 1024 * 1024,
            "timeoutMs": 120000,
            "maxAssets": 4,
            "maxSubjects": 20000,
            "maxConcurrency": 2,
        },
    },
)

for page in first.iterPages():
    consume(page)
```

한 query는 전체 작업과 universe를 고정한다는 뜻이며, 전체 회사를 첫 응답에 한꺼번에 계산하거나 RAM에 적재한다는 뜻이 아니다. owner별 한 page의 종목 시도 상한은 8이고 row, byte, time 예산이 더 작으면 page도 더 작아진다. 종목 실패는 gap으로 남고 cursor는 다음 종목으로 진행한다.

실제 읽기 전용 전수 감사에서 DART strict PIT factor는 2,661개 중 2,352개, 88.3878%가 성공했다. EDGAR full-state strict는 7,669개 중 632개, 8.24097%였다. revenue와 operating margin만 요청해 불필요한 stock state 의존을 제거한 production flow-only 경로는 3,136개, 40.8919%가 성공했다. 이 개선은 PIT cutoff, 4분기 연속성, 동일 accession lineage, revision 충돌 검증을 낮추지 않았다. 공식 감사 실행 구간은 loader와 network 호출 0회였고 시작과 종료 source snapshot이 같았다.

감사 준비 단계에서 잘못 실행한 loader가 DART 원천 파일 1개를 갱신한 사고와 eager 실현 가능성 probe가 macro, news 파일을 갱신한 사고는 각각 [DART 전수 감사 기록](../../tests/_attempts/dataWorkbenchDartScale/README.md)과 [process deadline 기록](../../tests/_attempts/dataWorkbenchProcessDeadline/README.md)에 이전 관측값, 현재 digest, 영향 경로를 분리해 남겼다. 이 사고는 공식 감사 구간의 불변 판정에 포함시키지 않으며, 원천 전체가 세션 내내 한 번도 변하지 않았다고 주장하지 않는다.

같은 query를 다른 프로세스가 factor-store처럼 재사용해야 하면 materialization 정책만 추가한다.

```python
built = dartlab.data(
    "query",
    query={
        "requests": [...],
        "budget": {...},
        "materialization": {"mode": "refresh"},
    },
)
receipt = built.materializationReceipt

offline = dartlab.data(
    "query",
    query={
        "materialization": {
            "mode": "offline",
            "receipt": receipt,
        }
    },
)
```

`refresh`는 현재 source와 contract를 다시 해소해 exact generation을 만들거나 이미 같은 generation이 READY면 재사용한다. `reuse`는 같은 logical query의 최신 READY generation을 먼저 찾고 없으면 cold build한다. `offline`은 receipt의 exact generation만 읽는다. 세 모드는 같은 `DARTLAB_HOME`을 보는 다른 Python 프로세스에서 쓸 수 있다. 원격 다중 노드 서비스나 네트워크 권한 계층을 뜻하지 않는다.

`DataResult`는 최소한 `status`, `partitions`, `assets`, `snapshotId`, `dataSnapshotId`, `contractHash`, `coverage`, `gaps`, `lineageRefs`, `executionReceipts`, `continuation`, `materializationReceipt`를 함께 가진다. schema와 실제 값의 `contentHash`는 각 partition이 보존한다.

## 문서 지도

1. [00-product-charter.md](00-product-charter.md): 범위, 비목표, 계층, 사용자 가치, 불변식
2. [01-current-state-and-debate.md](01-current-state-and-debate.md): 실제 코드와 데이터 자산, 전문가 토론, 기각안
3. [02-contract-and-architecture.md](02-contract-and-architecture.md): 타입, catalog, query, PIT, 계보, 자동 발견, 의존 방향
4. [03-migration-deletion-rollback.md](03-migration-deletion-rollback.md): Universe와 Mirror 선별 승격, simulator 전환, 삭제와 롤백
5. [04-verification-progress-ledger.md](04-verification-progress-ledger.md): 단계, 테스트, 실데이터 matrix, fatal gate, 진행 원장
6. [05-signature-data-prism.md](05-signature-data-prism.md): 공식 외부 조사, 공통 evidence spine, 혼합 query, 용도별 설계
7. [06-full-certification-and-hardening.md](06-full-certification-and-hardening.md): 170개 전수 실행 결과, concurrency, 빈 결과, 성능 등급, 남은 owner 상태

## 기존 계획과의 관계

- `mainPlan/dartlab-universe/`의 U0부터 U4까지에서 범용 catalog, identity, provenance, admission 계약을 선별 재사용한다.
- Universe의 blog, media, RAG, spatial 기능은 data core가 아니라 data를 소비하는 상위 제품으로 남긴다.
- `mainPlan/scenario-simulator/18-workbench-mirror-design.md`의 Mirror는 검증된 folding prototype이었다. 순수 folding kernel은 `data.factorKernel`로 흡수했고, 사용처가 없던 `simulate.mirror` 드라이버는 제거했다.
- `mainPlan/_done/data-workbench-ssot/`는 UI transport와 cache plane이다. Python semantic Data Workbench와 역할이 다르며 우회하지 않는다.
- AI Workbench는 agent 실행 loop, pipeline은 build orchestration이다. 이 둘을 semantic Data Workbench로 부르지 않는다.

## 완료 판정

문서 작성이나 root export만으로 완료하지 않는다. L1, L1.5, L2 전수 catalog, 진짜 PIT 전달과 fail-closed, typed projection, bounded 실행, simulator 소비, 외부 설치 smoke, Skill OS와 생성 산출물 동기화, 레거시 caller 0과 실데이터 parity가 모두 증명돼야 한다.
