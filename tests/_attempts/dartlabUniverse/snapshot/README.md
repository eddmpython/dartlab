# Snapshot attempts

> 상태: U0-S01 및 canonical replay guard 완료, U0-W01 대기
> 책임: map, search, panel, finance, capability, recipe의 source version을 한 재현 단위로 묶는다.

## 가설

`SourceSnapshotSet`이 있으면 단일 map buildId보다 변화 재생과 share replay를 정직하게 판정할 수 있다.

## 실행 순서

1. U0-S01: source별 version, ETag, immutable path, dataAsOf 가용성을 센서스한다. 완료.
2. U0-S02: canonical snapshotSetId와 missing source의 `unreplayable` 표현을 검증한다. U0-S01 회귀 계약에 통합 완료.
3. U0-W01: DART 30사의 revision과 observation을 두 knownAt에서 재생한다.

## U0-S01 실행

```powershell
uv run python -X utf8 tests/_attempts/dartlabUniverse/snapshot/sourceSnapshotSetProbe.py
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
- `changeReplayProbe.py`
- `testChangeReplayProbe.py`
- 작은 synthetic fixture와 reviewed DART fixture

production 코드는 이 경로를 import하지 않는다. 결과는 상위 attempts README와 mainPlan progress ledger에 기록한다.
