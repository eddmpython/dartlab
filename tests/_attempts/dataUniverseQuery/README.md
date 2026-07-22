# Data Universe Query Attempt

카테고리: 기존 `dartlab.data("query")` 안에서 DART와 EDGAR 전시장 universe를 한 번에 계획하는 순수 프로토타입이다.

## 가설

1. 공개 axis는 `catalog`, `query` 둘만 유지한다.
2. `UniverseSelection(markets, membership, explicitIds)`로 전시장과 직접 entity 목록을 같은 계약에서 표현한다.
3. owner가 market bulk를 지원하면 시장당 한 task로 pushdown하고, 미지원 owner만 snapshot 기반 subject fanout을 사용한다.
4. KR DART와 US EDGAR coverage는 합계로 뭉개지 않고 asset과 market별로 반환한다.
5. 같은 의미의 입력은 순서와 중복이 달라도 같은 task 순서와 `planId`를 만든다.
6. explicit ID 필터를 처리하지 못하는 bulk owner는 전시장 over-fetch 대신 `OWNER_FILTER_UNSUPPORTED`로 실패한다.

## 계약 의미

- `markets`: `KR`, `US` 같은 시장 범위다.
- `membership`: `active`, `allKnown`, `explicit` 중 하나다.
- `explicitIds`: `KR:005930`, `US:0000320193`처럼 시장 접두를 가진 entity ID다. `active` 또는 `allKnown`과 함께 쓰면 membership 교집합 필터다.
- `UniverseSnapshot`: DART와 EDGAR membership을 같은 revision ID에 결박한다.
- `OwnerCapability.bulkMemberships`: owner가 실제 전시장 연산을 한 번에 수행할 수 있는 market과 membership 쌍이다.
- `OwnerCapability.fanoutMarkets`: bulk가 없을 때 subject별 실행이 가능한 market이다.

이 폴더의 planner는 표준 라이브러리만 사용한다. 네트워크, 파일, owner 엔진을 호출하지 않으며 `src/dartlab`을 수정하지 않는다.

## 실행

```bash
uv run python -X utf8 tests/_attempts/dataUniverseQuery/universePlanner.py
bash tests/test-lock.sh tests/_attempts/dataUniverseQuery -q
```

## 성공 기준

- KR 3종목과 US 2종목을 bulk asset은 2 task, fanout asset은 5 task로 계획한다.
- 네 개 asset-market coverage row가 모두 complete다.
- canonical 입력 순서와 plan hash가 반복 실행에서 동일하다.
- explicit filter와 membership 결손이 machine-readable gap으로 남는다.

## 결과

- 날짜: 2026-07-22
- 표본: KR DART 3종목, US EDGAR 2종목, owner asset 2개
- 핵심 수치: 7 tasks, owner bulk 2, subject fanout 5, asset-market coverage 4/4 complete
- 결정성: 동등 입력의 task, coverage, `planId`가 모두 동일
- 검증: 잠금 pytest 8 passed, ruff passed, em dash와 en dash 0
- 결론: planning contract는 승격 가능하다. 공개 axis를 늘리지 않고 전시장 query를 표현하며, explicit filter over-fetch와 market 결손도 차단한다.
- 다음 단계 후보: DataQuery selector와 descriptor capability로 치환하고 실제 DART, EDGAR owner bulk 실행을 검증
