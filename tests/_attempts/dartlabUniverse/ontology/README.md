# Ontology attempts

> 상태: U0-O01 assertion 및 bitemporal 계약 완료, live assertion admission 차단
> 책임: relation identity, assertion revision, exact evidence, valid time, knowledge time을 분리한다.

## 가설

Relation과 assertion ID를 분리하고 exact evidence binding과 append-only supersedes lineage를 assertion identity에 결속하면, 같은 관계의 여러 공시와 정정을 잃지 않으면서 point-in-time view를 재현할 수 있다.

## 실행

```powershell
uv run python -X utf8 tests/_attempts/dartlabUniverse/ontology/assertionContract.py
uv run python -X utf8 tests/audit/docstring4Section.py tests/_attempts/dartlabUniverse/ontology --strict
uv run python -X utf8 tests/audit/docstring9Section.py tests/_attempts/dartlabUniverse/ontology --strict
```

Unit test는 repository test lock을 획득한 뒤 `testAssertionContract.py` 단일 파일만 실행한다.

## 계약

- `relationId`는 subject, predicate, object, direction만 canonical hash한다.
- `assertionId`는 relation, status, SourceSnapshotSet, publication 및 availability, validity, event, supersedes, evidence binding을 canonical hash한다.
- Query `knownAt`은 assertion ID에 들어가지 않는다.
- 같은 relation의 다른 filing, period, correction은 별도 assertion ID를 가진다.
- Correction은 predecessor를 삭제하지 않고 `supersedesAssertionId`로 연결한다.
- Supersedes는 같은 relation에서 availability가 증가해야 하고 branch를 허용하지 않는다.
- `sourcePublishedAt <= availableAt`을 강제한다. `eventAt`과 `validFrom`은 availability보다 미래여도 허용한다.
- Evidence는 production `Ref`를 사용하되 external source, canonical filing ID, section, exact text 또는 table locator, immutable hash, exact time을 요구한다.
- Query는 validAt과 knownAt을 독립 필터하고 lineage별 latest known revision을 반환한다.
- Query 결과는 production `VintageRef`의 `asKnown`, `asOfExact`를 통과해야 한다.

## U0-O01 결과

| 항목 | 실측 |
|---|---:|
| Public ecosystem edge | 20,560 |
| Unique relation candidate | 20,560 |
| Self-loop | 13 |
| Assertion ID | 0 |
| Supersedes link | 0 |
| Exact evidence pointer | 0 |
| SourcePublishedAt | 0 |
| AvailableAt | 0 |
| ValidFrom | 0 |
| ValidTo | 0 |
| Admitted status | 0 |
| Assertion ready | 0 |
| Synthetic regression | 9/9 PASS |
| Future knowledge leak | 0 |
| History loss | 0 |
| Live ready | false |

Public ecosystem의 20,560 edge는 서로 다른 relation candidate로 안정적으로 식별할 수 있다. 그러나 이는 presentation topology의 uniqueness일 뿐 assertion history가 있다는 뜻은 아니다. Assertion ID, exact evidence, source time, validity, admitted status가 모두 0이고 self-loop 13개가 남아 있다.

판정은 `revise`다. Synthetic contract는 relation과 assertion 분리, order-independent hash, append-only correction, cutoff 독립 identity, future effective event, future knowledge exclusion, exact VintageRef를 통과했다. Live edge는 assertion source가 0이므로 candidate를 observed로 compile하지 않는다.

## 다음

U0-P01에서 candidate, fact, derived, scenario lane을 분리한 bounded projection을 만든다. Current edge는 candidate lane에서만 seed로 사용할 수 있고 assertionReady 0은 fact lane 0으로 이어져야 한다.

Production 코드는 이 경로를 import하지 않는다.
