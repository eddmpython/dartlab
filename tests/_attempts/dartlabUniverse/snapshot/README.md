# Snapshot attempts

> 상태: U0-S01 및 U0-W01 계약 완료, live DART exact replay 차단
> 책임: map, search, panel, finance, capability, recipe의 source version을 한 재현 단위로 묶는다.

## 가설

`SourceSnapshotSet`이 있으면 단일 map buildId보다 변화 재생과 share replay를 정직하게 판정할 수 있다.

## 실행 순서

1. U0-S01: source별 version, ETag, immutable path, dataAsOf 가용성을 센서스한다. 완료.
2. U0-S02: canonical snapshotSetId와 missing source의 `unreplayable` 표현을 검증한다. U0-S01 회귀 계약에 통합 완료.
3. U0-W01: append-only synthetic revision을 두 knownAt에서 재생하고 DART 30개 deterministic schema sample의 live readiness를 센서스한다. 완료.

## U0-S01 실행

```powershell
uv run python -X utf8 tests/_attempts/dartlabUniverse/snapshot/sourceSnapshotSetProbe.py
uv run python -X utf8 tests/_attempts/dartlabUniverse/snapshot/changeReplayProbe.py
uv run python -X utf8 tests/audit/docstring4Section.py tests/_attempts/dartlabUniverse/snapshot --strict
uv run python -X utf8 tests/audit/docstring9Section.py tests/_attempts/dartlabUniverse/snapshot --strict
```

Unit test는 repository test lock을 획득한 뒤 `testSourceSnapshotSetProbe.py` 단일 파일만 실행한다.

## U0-S01 결과

| 항목 | 실측 |
|---|---:|
| source | 10 |
| immutable HF source | 8 |
| immutable Git blob source | 1 |
| unreplayable source | 1, `capabilityCatalog` |
| missing dataAsOf | 1, `dartPanelSample` |
| missing redistribution receipt | 10 |
| 반복 canonical hash 일치 | 2/2 |
| unit regression | 8/8 PASS |
| docstring 4 및 9 section strict | 위반 0 |

Live snapshotSetId는 `sha256:4a68a0c0129884bc138223ef3d31672c1e7dd5bbbdac33a4816d0f953e54f73a`였다. map buildId는 `20260715-084444`, HF repository commit은 `c0260a60859f0ba5a30d452a7c05791d79e9bd1d`였다.

판정은 `revise`다. source identity 또는 명시적 `unreplayable` coverage는 100%라 U0-S01 계약은 완료했다. 그러나 live compiled capability 226개는 canonical output hash만 있고 immutable manifest가 없으므로 현재 public exact replay는 금지한다. panel dataAsOf 결손은 재현성 결손과 분리해 표시한다. redistribution receipt는 U0-P02에서 심사한다.

## U0-W01 결과

| 항목 | synthetic | live DART deterministic sample |
|---|---:|---:|
| 입력 | revision 8 | 정렬된 앞 30 parquet, 359,115 row |
| created | 1 | 판정 불가 |
| corrected | 1 | 판정 불가 |
| retracted | 1 | 판정 불가 |
| newlyKnown | 1 | 판정 불가 |
| stale | 1 | 판정 불가 |
| revision 보존 | 8/8, 100% | revisionId 0/30 |
| look-ahead | 0 | availableAt 0/30이라 exact 검증 불가 |
| evidence 결속 | 5/5, 100% | rowKey 0/30 |
| sourcePublishedAt | fixture 100% | 0/30 |
| filing ID | fixture 100% | rcept_no 30/30 |
| observed multi-receipt group | fixture 2개 lane | 0 |
| unit regression | 8/8 PASS | readiness false |

Synthetic fixture는 같은 input의 순서가 달라도 같은 replayHash를 만들고 query cutoff가 assertionId를 바꾸지 않는다. after knownAt보다 늦은 revision은 diff, VintageRef artifactHash, sourceRefs에 모두 들어가지 않는다. malformed timezone과 publication 순서도 fail closed다. Production `VintageRef`의 `revisionPolicy=asKnown`, `coverage=asOfExact` 계약을 그대로 통과했다.

Live 표본은 대표 표본이 아니라 파일명 정렬 뒤 앞 30개를 읽는 deterministic schema sample이다. `rcept_no`는 30/30이지만 `sourcePublishedAt`, `availableAt`, `revisionId`, `rowKey`는 모두 0/30이고 multi-receipt revision group도 0이다. `rcept_no` 앞 여덟 자리를 임의의 ISO timestamp로 확대하지 않는다.

판정은 `revise`다. U0-W01 replay contract는 완료했지만 현재 DART finance artifact로 exact live replay를 승인하지 않는다. Reviewed multi-filing fixture와 sourcePublishedAt, availableAt, revisionId, exact row locator가 보존될 때까지 public 변화 우주는 current atlas 또는 명시적 unavailable 상태만 허용한다.

## 합격

- 재현을 약속한 source의 version 누락 0
- 같은 set의 canonical hash 일치 100%
- revision 보존 100%
- look-ahead 0건
- before 및 after exact evidence 결속 95% 이상

## 기각

- 현재값의 과거 역주입 1건
- query knownAt에 따라 assertionId가 바뀌는 사례 1건
- source 하나가 바뀌었는데 같은 snapshotSetId가 나오는 사례 1건

## 산출물

- `sourceSnapshotSetProbe.py`, 완료
- `testSourceSnapshotSetProbe.py`, 완료
- `changeReplayProbe.py`, 완료
- `testChangeReplayProbe.py`, 완료
- 작은 synthetic fixture, 완료
- DART 30개 deterministic schema census, 완료
- reviewed multi-filing DART fixture, source field 결손으로 차단

production 코드는 이 경로를 import하지 않는다. 결과는 상위 attempts README와 mainPlan progress ledger에 기록한다.
