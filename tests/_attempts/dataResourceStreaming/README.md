# Data Resource Streaming Attempt

카테고리: DART와 EDGAR company-sharded parquet 전체를 Data Workbench resource asset에서 page 단위로 읽는 순수 프로토타입이다.

## 가설

1. Python에서 회사를 하나씩 `loadData`로 여는 대신 전체 shard file list를 native columnar reader 하나로 열 수 있다.
2. projection과 predicate를 DuckDB relation 또는 Arrow Dataset scanner에 전달해 raw text와 불필요한 column을 읽지 않는다.
3. `batch_readahead=1`, `fragment_readahead=1`과 전역 row, byte budget으로 반환 메모리를 제한한다.
4. 기본 `integrityMode="full"`은 모든 file bytes의 SHA-256을 정렬해 절대 local path와 무관한 source pin을 만든다.
5. `integrityMode="footerFast"`는 benchmark 전용 metadata pin이다. payload integrity나 continuation을 보장하지 않는다.
6. `startRow`, 이전 full source pin, query pin이 모두 맞아야 재개하며 DuckDB와 Arrow가 같은 row sequence를 반환한다.
7. virtual filename은 root 상대 `sourcePath`로 정규화해 batch row를 원래 company shard까지 추적한다.

## 프로토타입 경계

- 공개 axis는 추가하지 않는다. 최종 위치는 기존 `dartlab.data("query")`의 resource projection executor다.
- 이 attempt는 표준 owner payload를 읽지 않고 local parquet를 read-only로 사용한다.
- 전체 shard는 manifest와 native Dataset fragment로 들어가지만 반환은 최대 50,000행, 16MiB로 제한한다.
- 기본 backend는 DuckDB RecordBatchReader다. Arrow Dataset backend도 동형 계약으로 남겨 결과 parity를 검사한다.
- `contentRaw`는 panel 기본 projection에서 제외한다. 본문 payload paging은 더 작은 별도 byte cap이 필요하다.
- production 기본 source pin은 전체 payload bytes hash다.
- benchmark 표의 manifest 시간은 명시적 `footerFast` 모드다. 이 pin으로 continuation을 열 수 없다.
- resume query는 `startRow`, `expectedSourcePin`, `expectedQueryPin`을 모두 요구한다. source 또는 projection, predicate, company selection이 바뀌면 실패한다.

## 실행

```bash
bash tests/test-lock.sh tests/_attempts/dataResourceStreaming -q
uv run python -X utf8 tests/_attempts/dataResourceStreaming/benchmarkLocalResources.py --resource dart.panel --integrity-mode footerFast
uv run python -X utf8 tests/_attempts/dataResourceStreaming/benchmarkLocalResources.py --resource dart.finance --integrity-mode footerFast
uv run python -X utf8 tests/_attempts/dataResourceStreaming/benchmarkLocalResources.py --resource edgar.panel --integrity-mode footerFast
uv run python -X utf8 tests/_attempts/dataResourceStreaming/benchmarkLocalResources.py --resource edgar.finance --integrity-mode footerFast
```

각 benchmark는 allocator 잔존 영향을 피하도록 별도 process에서 실행한다.

## 성공 기준

- manifest에 네 resource의 local parquet 전체가 포함된다.
- 같은 bytes를 다른 absolute root로 옮겨도 source pin이 같다.
- full mode entry digest가 실제 full-file SHA-256과 같다.
- projection 밖 column이 batch schema에 나타나지 않는다.
- predicate 결과만 반환하고 sourcePath가 보존된다.
- batch 합계가 maxRows와 maxBytes를 넘지 않는다.
- 1 page의 `nextRow`로 연 2 page가 중복과 누락 없이 이어지고 두 backend가 동일하다.
- footerFast, source pin drift, query pin drift에서는 resume이 차단된다.
- 전체 resource manifest와 bounded scan의 시간, RSS, 행 수가 기록된다.

## 결과

- 날짜: 2026-07-22
- 표본: DART panel/finance, EDGAR panel/finance 전체 24,489 shard, 18.668GiB

| Resource | Files | Size GiB | Footer-fast manifest sec | 50k scan sec | Result MiB | RSS delta MiB |
|---|---:|---:|---:|---:|---:|---:|
| `dart.panel` | 2,930 | 10.972 | 0.850 | 0.826 | 4.168 | 25.523 |
| `dart.finance` | 2,932 | 0.532 | 0.582 | 0.571 | 4.997 | 28.211 |
| `edgar.panel` | 1,260 | 6.491 | 0.361 | 0.465 | 4.496 | 20.578 |
| `edgar.finance` | 17,367 | 0.673 | 4.356 | 3.076 | 4.969 | 75.254 |

- 합계: footerFast manifest 6.149초, bounded scan 4.938초, 반환 200,000행, Arrow logical result 18.630MiB
- 모든 scan은 25 RecordBatch와 50,000행에서 정확히 절단됐다.
- panel scan은 `contentRaw`를 읽지 않고 metadata 4개 column만 projection했다.
- `edgar.finance` 비교 실측: Arrow 단일 thread 43.166초와 RSS 증가 125.934MiB, Arrow native threads 33.840초와 401.863MiB, DuckDB 첫 실행 8.593초와 45.520MiB였다. 정식 반복 실측은 3.025초와 61.848MiB였다.
- 잠금 pytest 9개는 full-file integrity, pinned resume, 상대 sourcePath, DuckDB와 Arrow Dataset parity를 함께 검증했다.

### Full integrity 비용

| Resource | Full SHA-256 manifest sec | Source pin prefix |
|---|---:|---|
| `dart.panel` | 6.500 | `resource-source-full:e85d9b...` |
| `dart.finance` | 2.022 | `resource-source-full:3cfd7b...` |
| `edgar.panel` | 3.532 | `resource-source-full:2854d9...` |
| `edgar.finance` | 11.507 | `resource-source-full:7bb78e...` |

전체 18.668GiB payload bytes를 읽은 full manifest 합계는 23.561초였다. 8개 bounded hash worker를 쓰며 같은 payload에서 source pin은 반복 실행마다 동일했다. full manifest를 page마다 다시 계산하지 않고 query session에서 재사용하는 것이 승격 조건이다.

## 승격 순위

1. `resource.edgar`: 첫 pageable owner executor다. 실제로 17,367개 CIK company shard인데 현재 catalog에서 bulk로 분류된다. structured numeric schema라 raw text 위험 없이 효과가 가장 크다.
2. `resource.finance`: DART finance 2,932개 company shard다. 기존 단일 subject payload와 별도로 전시장 page query를 제공할 가치가 크다.
3. `resource.edgarFinanceStmt`: 동일한 structured company shard이며 terminal 표준 schema라 두 번째 구현 묶음에 적합하다.
4. `resource.edgarPanel`, `resource.panel`: metadata projection과 pinned continuation은 검증됐다. `contentRaw` payload를 opt-in으로 제한하고 더 작은 byte cap을 정한 뒤 승격한다.

결론: Python 회사별 load는 필요 없다. full-file SHA-256 manifest에 query pin과 row offset을 결박하고, sorted file list를 DuckDB에 한 번 넘긴 뒤 RecordBatchReader를 전역 row, byte budget으로 감싸는 경로가 승격 가능하다.
