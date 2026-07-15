# Snapshot attempts

> 상태: 계획 확정, 미실행
> 책임: map, search, panel, finance, capability, recipe의 source version을 한 재현 단위로 묶는다.

## 가설

`SourceSnapshotSet`이 있으면 단일 map buildId보다 변화 재생과 share replay를 정직하게 판정할 수 있다.

## 실행 순서

1. U0-S01: source별 version, ETag, immutable path, dataAsOf 가용성을 센서스한다.
2. U0-S02: canonical snapshotSetId와 missing source의 `unreplayable` 표현을 검증한다.
3. U0-W01: DART 30사의 revision과 observation을 두 knownAt에서 재생한다.

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

## 산출물 예정

- `sourceSnapshotSetProbe.py`
- `testSourceSnapshotSetProbe.py`
- `changeReplayProbe.py`
- `testChangeReplayProbe.py`
- 작은 synthetic fixture와 reviewed DART fixture

production 코드는 이 경로를 import하지 않는다. 결과는 상위 attempts README와 mainPlan progress ledger에 기록한다.
