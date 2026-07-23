# DartLab Unified Data Workbench

상태: 구현, 전수 라우팅과 projection 인증, 170개 실제 물질화 감사, 171개 queryable catalog, 외부 설치 검증 완료. 2026-07-23 저장소 실측을 반영한다.

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
16. 전종목 원천 paging과 계산된 전종목 factor paging은 구분한다. 현재 EDGAR PIT feature는 subject 단위 callable이다.

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

`DataResult`는 최소한 `status`, `partitions`, `assets`, `snapshotId`, `dataSnapshotId`, `contractHash`, `coverage`, `gaps`, `lineageRefs`, `executionReceipts`, `continuation`을 함께 가진다. schema와 실제 값의 `contentHash`는 각 partition이 보존한다.

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
