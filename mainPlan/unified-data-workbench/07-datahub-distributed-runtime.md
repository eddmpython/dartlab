# 07. DataHub 분산·원격·비동기 최종 구조

## 제품 정의

DataHub는 factor store보다 상위다. L1 원천, L1.5 정규화·횡단 데이터, L2 분석 결과를 하나의 catalog, query, snapshot, lineage 계약으로 연합한다. factor는 별도 최상위 저장소가 아니라 같은 query의 `FactorProjection`이다.

```text
local Python / simulator / scan / strategy / AI
                    │
                    ├─ dartlab.dataHub("catalog" | "query")
                    │
external process ───┼─ DataHubClient / AsyncDataHubClient
                    │
                    ▼
          /api/dataHub/v1 control plane
                    │
          durable job ledger + private CAS
                    │ lease / heartbeat / epoch
          ┌─────────┼─────────┐
          ▼         ▼         ▼
       worker A  worker B  worker N
          │         │         │
          └──── DataHub query kernel ────┐
                                         ▼
              immutable generation / Arrow page
```

핵심은 종목별 API 반복이 아니다. 한 query가 여러 asset과 KR·US universe를 등록하고, DataHub가 owner lane, page, row·byte·time budget, continuation을 관리한다. 같은 결과는 content hash, data snapshot, lineage, execution receipt, materialization receipt로 봉인된다.

## 공개 계약

### 로컬

```python
import dartlab

catalog = dartlab.dataHub("catalog")
result = dartlab.dataHub("query", query={
    "requests": [
        {"assetId": "analysis.dartFinancialFeatures"},
        {"assetId": "analysis.edgarFinancialFeatures"},
    ],
    "universe": {"markets": ["KR", "US"], "membership": "listed"},
    "projection": {"kind": "factor"},
})
```

`dartlab.data`는 기존 호출자를 위한 호환 별칭이다. 신규 정본은 폴더, import, capability key, 문서 모두 `dataHub`다.

private runtime root는 `DARTLAB_HOME/dataHub` 하나만 쓴다. 별도 레거시 경로 선택이나 이중 경로 폴백은 두지 않는다.

### 원격 동기

```python
from dartlab.dataHub import DataHubClient

with DataHubClient("https://host", clientToken) as hub:
    job = hub.query(query, wait=False, idempotencyKey="daily-close-2026-07-26")
    result = hub.wait(job.jobId)
```

### 원격 비동기

```python
from dartlab.dataHub import AsyncDataHubClient

async with AsyncDataHubClient("https://host", clientToken) as hub:
    result = await hub.query(query)
```

동기·비동기 client 모두 `catalog`, `query`, `submit`, `job`, `cancel`, `result`, `wait`를 제공한다. callable 표면도 local과 같은 `catalog`·`query` 두 axis를 유지한다.

## control plane

API prefix는 `/api/dataHub/v1`이다.

| 역할 | endpoint | 의미 |
| --- | --- | --- |
| client | `POST /catalog` | metadata-only 자산 발견 |
| client | `POST /jobs` | 멱등 비동기 query 제출 |
| client | `GET /jobs/{id}` | durable 상태 조회 |
| client | `DELETE /jobs/{id}` | queued 또는 leased job 취소 |
| client | `GET /jobs/{id}/result` | 봉인된 DataResult 복원 |
| worker | `POST /workers/claims` | 우선순위 순 원자 lease |
| worker | `POST /workers/jobs/{id}/heartbeat` | lease 연장 |
| worker | `POST /workers/jobs/{id}/complete` | epoch 검증 후 결과 확정 |
| worker | `POST /workers/jobs/{id}/fail` | backoff 재시도 또는 terminal 실패 |

상태는 `queued → leased → succeeded|failed|cancelled`다. lease가 만료되면 시도 한도 안에서 다시 queue로 돌아간다. stale worker의 완료 요청은 lease epoch가 차단한다. 제출 payload와 결과 payload는 SHA-256 CAS에 저장하며 SQLite에는 digest, 상태, 수치, lease만 둔다.

비동기 job은 continuation 재개가 아닌 경우 기본 materialization을 `refresh`로 정규화한다. 따라서 worker 장애 뒤 재실행과 다른 process의 결과 소비가 runtime 임시 상태에만 의존하지 않는다.

## worker plane

각 머신은 같은 control plane을 향해 독립 worker를 실행한다.

```powershell
$env:DARTLAB_DATA_HUB_WORKER_TOKEN = "..."
python -m dartlab.dataHub.workerPlane `
  --base-url https://host `
  --worker-id node-a
```

worker는 pull 방식이므로 inbound worker port가 필요 없다. 여러 worker가 동시에 claim해도 ledger의 원자 lease 때문에 한 job은 한 epoch에서 한 worker만 실행한다. 실행 중 heartbeat가 끊기면 결과 확정을 포기하고 다른 worker가 재시도할 수 있다.

## 속도와 효율

- catalog는 값을 실행하지 않고 descriptor snapshot만 만든다.
- 동일 query는 idempotency key로 중복 job 생성을 막는다.
- 전시장 계산은 entity별 외부 호출 루프가 아니라 owner별 최대 64개 page와 continuation으로 처리한다.
- immutable generation warm replay는 catalog, owner, source 재실행 없이 receipt와 CAS page를 읽는다.
- Arrow 기반 wire codec은 DataFrame을 문자열이나 JSON row 배열로 축소하지 않는다.
- row, byte, time, asset, subject, page 예산이 전체 query 경계에서 fail-closed로 적용된다.
- 약한 PC는 모든 데이터를 RAM에 올리지 않고 bounded page를 순차 소비하며, 여러 머신이 worker 수평 확장으로 job을 나눠 가진다.

## 보장 범위

DataHub가 "모든 데이터"를 사용한다는 뜻은 저장소의 임의 파일을 무차별 읽는다는 뜻이 아니다. owner가 `dataProduct.py`로 등록한 공개 자산, catalog가 queryable로 판정한 자산, 요청한 projection과 PIT 계약을 만족하는 데이터가 대상이다. private·bulk payload, PIT 미지원, 예산 초과, owner 결손은 성공으로 가장하지 않고 구조화 gap 또는 고정 오류로 반환한다.

현재 구현의 분산 단위는 원격 worker plane이다. control plane ledger는 한 durable coordinator root의 SQLite와 private CAS를 사용한다. 여러 호스트 worker 수평 확장은 지원하지만 control plane 자체의 multi-primary 합의나 지역 간 active-active 복제는 이 계약에 포함하지 않는다. 그 단계가 필요하면 job ledger와 CAS를 외부 합의 저장소로 교체하되 공개 client, worker lease, DataResult wire 계약은 유지한다.

## 검증 게이트

- 같은 idempotency key와 같은 query는 같은 job을 반환하고 다른 query는 충돌한다.
- 8개 동시 worker claim에서 정확히 하나만 lease를 얻는다.
- lease 만료 후 재queue, 시도 한도 소진 후 terminal 실패를 검증한다.
- 취소 job은 결과를 노출하지 않고 stale complete를 받지 않는다.
- client token과 worker token은 서로 대체할 수 없다.
- 동기 client 제출, 원격 worker 실행, 결과 wait와 materialization receipt 복원을 end-to-end 검증한다.
- asyncio client의 제출과 취소가 event loop를 막지 않는 계약으로 동작한다.
- wire payload 변조와 digest 불일치는 결과 복원 전에 차단한다.
- 인증된 worker라도 올바른 DataResult wire가 아니면 성공 상태 전이를 거부한다.
