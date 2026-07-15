# Projection attempts

> 상태: U0-P01 bounded projection 계약과 live 3-scene 검증 완료
> 책임: 질문당 작은 scene을 hard bound, deterministic hash, lane isolation, omission receipt로 만든다.

## 가설

Current atlas, industry detail, company egograph를 새 artifact로 복제하지 않고 runtime에서 stable priority로 자르면, 276GB truth 위에 질문당 50~500 node의 재현 가능한 Universe scene을 만들 수 있다.

## 실행

```powershell
uv run python -X utf8 tests/_attempts/dartlabUniverse/projection/boundedProjection.py
uv run python -X utf8 tests/audit/docstring4Section.py tests/_attempts/dartlabUniverse/projection --strict
uv run python -X utf8 tests/audit/docstring9Section.py tests/_attempts/dartlabUniverse/projection --strict
```

Unit test는 repository test lock을 획득한 뒤 `testBoundedProjection.py` 단일 파일만 실행한다.

## 계약

- `ProjectionSpec`은 query, seedIds, SourceSnapshotSet, maxDepth, maxNodes, maxEdges를 고정한다.
- `maxNodes`는 500, `maxEdges`는 2,000을 넘지 못한다.
- Seed 수가 node budget을 넘거나 seed identity가 없으면 실행하지 않는다.
- Fact edge는 assertion ID와 exact evidence refs를 모두 요구한다.
- Candidate edge는 fact admission field를 가질 수 없고 자동 승격되지 않는다.
- Derived edge는 derivation refs, scenario edge는 scenario receipt를 요구한다.
- Stable queue는 depth, lane, priority, edge ID 순으로 선택한다.
- 생략된 node와 edge는 reason 및 lane별 count를 `OmissionReceipt`에 남긴다.
- Selected edge는 두 endpoint가 selected node에 있을 때만 scene에 들어간다.
- Scene hash는 logical node, edge, receipt, spec, SourceSnapshotSet을 결속하며 input order와 무관하다.

## U0-P01 결과

| Scene | Input | Hard bound | Output |
|---|---:|---:|---:|
| Atlas, semiconductor seed | 34 node / 50 edge | 34 / 50 | 18 node / 35 edge |
| Semiconductor industry, 005930 seed | 125 node / 85 edge | 50 / 80 | 26 node / 34 edge |
| Samsung egograph, 005930 seed | 178 node / 218 edge | 50 / 80 | 50 node / 60 edge |

| 항목 | 실측 |
|---|---:|
| SourceSnapshotSet | `sha256:054a4e376b92140278d2defe732c5375e62df21e9dacbd78955c58a3dafd68db` |
| Candidate input edge | 303 |
| Derived input edge | 50 |
| Fact input edge | 0 |
| Repeated scene hash | 3/3 |
| Hard bound violation | 0 |
| Seed loss | 0 |
| Lane violation | 0 |
| Synthetic regression | 8/8 PASS |
| Bounded projection live ready | true |

Atlas flow는 artifact 집계이므로 derived lane, industry와 company relation 303개는 U0-O01 assertion admission이 없으므로 candidate lane으로 유지했다. `confidence`와 source label은 fact 승격에 사용하지 않았다.

판정은 `promote`다. Bounded projection contract 자체는 production 이관 후보다. Current artifact만으로 세 seed archetype을 deterministic하게 자를 수 있어 276GB 전체 graph copy와 새 bake는 필요하지 않다. 다만 fact lane은 0이며 U0 evidence와 assertion live gate가 열리기 전 candidate scene만 공개할 수 있다.

## 다음

U0-V01에서 fact, candidate, derived, scenario, disputed, unknown 상태 문법을 사람이 정확히 읽는지 검증한다. Renderer dependency를 추가하지 않고 contract token, DOM reference card, task sheet부터 만든다.

Production 코드는 이 경로를 import하지 않는다.
