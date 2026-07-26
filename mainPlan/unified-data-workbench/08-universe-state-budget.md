# 08. 전종목 continuation state 예산 구조 결함

상태: **해소 완료** (2026-07-26). 아래는 진단과 수정 설계의 기록이다.

실측 결과 state 는 713,285 에서 5,911 bytes 로 줄었고 한도의 1.1% 다. KR 2,661 과
US 7,683 을 한 query 로 등록해 partition 34 개와 continuation 을 발급한다.

## 1. 증상

SKILL.md 와 README 가 대표 예제로 내세우는 KR 과 US 두 시장 동시 등록이 실제 universe
에서 즉시 실패한다. 문서에 적힌 budget 값을 그대로 써도 같다.

```text
KR 단독  2,661 종목 -> status=partial, continuation 발급     정상
US 단독  7,683 종목 -> status=partial, continuation 발급     정상
KR + US  혼합       -> status=failed, CONTINUATION_STATE_BUDGET
```

이 예제는 DataHub 정체성 문장인 "종목별 반복 호출 없이 한 query 로 전시장을 등록한다"
를 증명하는 자리다. 그 자리가 비어 있었다.

## 2. 원인 실측

`ownerPagingState._encodeSession` 이 만드는 raw JSON 이 한도를 넘는다.

```text
MAX_STATE_BYTES            524,288 bytes   (pagingRuntime.py)
혼합 query owner 세션      713,285 bytes   한도의 1.36 배
엔티티 수                  10,344 개       KR 2,661 + US 7,683
엔티티당                   약 69 bytes
```

`_OwnerTask.entities` 가 `_EntityRef(entityId, sourceEntityId, params)` 전량을 세션에
직렬화한다. entityId 만이면 약 145KB 인데 `sourceEntityId` 와 `params` 가 나머지를 채운다.

## 3. 핵심 관찰

이 목록은 **저장할 이유가 없다.** 이미 재개 시점에 재구성되고 있다.

`ownerPagingSource._currentSourcePins` 는 resume 마다 다음을 수행한다.

1. universe 를 재해소한다.
2. `_entities(membership, ...)` 로 `expectedEntities` 를 다시 만든다.
3. `expectedEntities != task.entities` 로 비교한다.

즉 목록은 매번 도출되고, 저장본은 그 도출값과 같은지 확인하는 데만 쓰인다. 순수 중복이다.

도출 가능성을 보장하는 pin 이 이미 task 에 전부 있다.

| pin | 역할 |
|---|---|
| `membershipDigest` | universe membership 이 그대로인지 |
| `descriptor` | `_entityParamMap` 입력이 그대로인지 |
| `ownerCodePin` | `_entities` 구현 바이트코드가 그대로인지 |

셋이 모두 같으면 `_entities` 는 결정적이므로 같은 목록이 나온다. 목록 저장은 그 사실을
바꾸지 않는다.

## 4. 수정 설계

### 4.1 상태에서 목록 제거

- `ownerPagingState._taskTree` 에서 `entities` 를 빼고 `entityCount` 만 남긴다.
- `_decodeTask` 는 `entities=()` 로 task 를 만들고 `entityCount` 를 함께 복원한다.

### 4.2 재개 경로에서 재수화

`_currentSourcePins` 가 이미 `expectedEntities` 를 계산하므로 같은 자리에서 task 를
재수화해 반환한다. 반환 타입을 pin 하나에서 pin 과 재수화된 task 묶음으로 넓힌다.

검증은 목록 비교 대신 다음으로 바꾼다.

- `membership.provider == task.provider`
- `membership.membershipDigest == task.membershipDigest`
- `len(expectedEntities) == task.entityCount`

셋 중 하나라도 어긋나면 기존과 동일하게 `CONTINUATION_SOURCE_STALE` 이다.

### 4.3 소비자 무변경

`task.entities` 소비처는 15 곳이며 전부 재수화 이후에 실행된다. 재수화 지점을 decode 와
첫 소비 사이에 두면 소비처는 한 줄도 바꾸지 않는다.

| 파일 | 소비 |
|---|---|
| `ownerPagingEntity.py` | 115, 185 |
| `ownerPagingResults.py` | 30, 34, 42, 61, 64, 85 |
| `ownerPagingSchedule.py` | 58, 144, 265, 331, 357 |
| `ownerPagingSource.py` | 110 |
| `ownerPagingState.py` | 393 |

## 5. 검증

- 혼합 KR 과 US query 가 continuation 을 발급하고 완주한다.
- 혼합 세션 raw state 가 한도의 절반 아래로 떨어진다.
- universe 가 바뀐 뒤 재개하면 여전히 `CONTINUATION_SOURCE_STALE` 이다.
- descriptor 나 owner code 가 바뀐 뒤 재개하면 기존 pin 검증이 그대로 차단한다.
- 기존 owner paging 회귀 전수와 composite outer chain 회귀가 통과한다.

## 6. 하지 않을 것

- `MAX_STATE_BYTES` 상향. 한도를 올리면 시장이 늘어날 때 같은 자리에서 다시 터진다.
- 상태 압축만 추가. 압축은 배수 여유일 뿐 선형 증가를 없애지 못한다. composite 계층에
  이미 있는 압축을 owner 로 옮기는 것은 이 수정 뒤에 별도로 판단한다.

## 7. 판단 근거

이 수정 뒤 세션 크기는 엔티티 수와 무관해진다. 시장을 더 붙여도 상태는 커지지 않는다.
지금 구조는 universe 가 커지면 반드시 다시 실패하므로 한도 조정으로는 닫히지 않는다.
