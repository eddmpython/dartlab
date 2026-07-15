# DartLab Universe attempts

> 상태: U0 진행 중. production 배선 금지
> 목적: Universe의 신규 의미 계약을 실데이터로 반증하고, 통과한 계약만 본진에 이관한다.

## 카테고리 한 줄

현재 HF truth와 기존 엔진을 이용해 entity, assertion, evidence, time, bounded projection의 제품 적격성을 순서대로 검증한다.

## 졸업 순서

1. 카테고리와 가설 원장 확정
2. 현재 공개 graph truth census
3. canonical entity resolution
4. exact evidence resolution
5. assertion, revision, bitemporal contract
6. bounded projection과 deterministic scene
7. public runtime latency 및 transfer budget
8. cross-market conformance
9. 덕지덕지 제거와 9섹션 docstring 확정
10. reviewed gold와 hard negative 통과 후에만 production 후보 이관

상세 실험 순서와 판정값은 [mainPlan의 attempts matrix](../../../mainPlan/dartlab-universe/08-attempts-evidence-matrix.md)가 정본이다.

## 실행 가능한 첫 근거

```powershell
uv run python -X utf8 tests/_attempts/dartlabUniverse/truth/graphTruthProbe.py
uv run python -X utf8 -m pytest tests/_attempts/dartlabUniverse/truth/testGraphTruthProbe.py -q
```

## 현재 결론 원장

| attempt | 입력 | 실측 | 판정 |
|---|---|---|---|
| U0-T01 graph truth census | HF `landing/map/ecosystem.json`, version `2026-04-14` | node 2,664, edge 20,560, self-loop 13, exact sourceRef 0, exact availableAt 0, observed 적격 0, OCI incident 4,474 | 기존 edge는 fact가 아니라 candidate hint. assertion/evidence 계약 선행 |

## 금지

- attempt 결과를 자동으로 HF truth 또는 map artifact에 쓰지 않는다.
- 현재 edge의 confidence 숫자만으로 observed 승격하지 않는다.
- sourceRef와 availableAt이 없는 edge를 public fact layer에 넣지 않는다.
- U0 졸업 전 `src/dartlab/**`에 Universe 전용 신규 능력을 배치하지 않는다.
