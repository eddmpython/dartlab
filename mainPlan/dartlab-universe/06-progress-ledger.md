# 06. Progress Ledger

## 현재 상태

- [x] 저장소 운영 규칙과 Skill OS의 architecture, API, UI, data lineage, testing 계약 재확인
- [x] HF repository 68,199파일 전수 byte 계수
- [x] staging, compatibility, active 수명주기 분리
- [x] capability, Skill OS, Analysis Graph, core engine axis 계수
- [x] live map meta, ecosystem, company egograph 실측
- [x] DART 및 EDGAR panel schema 동형 확인
- [x] current relation source, type, evidence, degree, self-loop 전수 감사
- [x] `OCI` hub 오탐 원인 확인
- [x] existing search sidecar, DataCore, range runtime, entity graph sidecar 재사용 경계 확인
- [x] product, ontology, runtime, UX, execution, 3-year maintenance 설계
- [ ] 운영자 구현 go
- [ ] U0 attempts
- [ ] U1~U2 implementation
- [ ] U3 artifact 변경 승인 여부
- [ ] UI 눈검수 및 push 승인

## 결정 원장

| 날짜 | 결정 | 근거 |
|---|---|---|
| 2026-07-15 | 제품명은 DartLab Universe | ontology는 내부 physics, universe는 사용자 surface |
| 2026-07-15 | 276GB 전량 graph copy 기각 | staging 153.91GB, compatibility 63.66GB, active 58.19GB |
| 2026-07-15 | 새 public engine 기각 | 기존 226 capability와 147 core axes 재사용 |
| 2026-07-15 | relation과 assertion 분리 | current `(from,to,type)` dedup이 시간 및 revision 손실 |
| 2026-07-15 | existing edge는 candidate hint | sourceRef 및 time 0, OCI 4,474 edge 오탐 |
| 2026-07-15 | Evidence on Demand 우선 | exact BM25 range와 panel source가 이미 존재 |
| 2026-07-15 | U3는 승인 게이트 | runtime SSOT 우선, 새 bake 무승인 금지 |
| 2026-07-15 | 2D 기본, 3D optional | 분석, 모바일, 접근성, vendor 독립성 |
| 2026-07-15 | `/map` 진화 | 병렬 product surface와 유지보수 중복 방지 |
| 2026-07-15 | 3년 운영 모델 포함 | schema, owner, deprecation, quality, incident, cost를 제품 계약으로 승격 |

## 핵심 실측 스냅샷

```text
HF total                 68,199 files / 275,755,437,729 bytes
search staging           2,173 files / 153,910,337,279 bytes
compatibility surfaces  11,344 files / 63,656,962,973 bytes
active and other        54,682 files / 58,188,137,477 bytes
current map              2,664 nodes / 20,560 edges / 34 industries
map ecosystem            6,015,606 bytes
map atlas                27,517 bytes
company payload total   79,517,001 bytes
capabilities             226
skills                   286
core dispatch axes       147
panel_text edges          17,400
panel_table edges            208
self loops                    13
OCI incident edges         4,474
exact edge sourceRef            0
```

## 외부 기술 사실

- [HF dataset card](https://huggingface.co/datasets/eddmpython/dartlab-data): 276GB, CC BY 4.0, KR 약 2,700사와 US 약 1,000사, Parquet 직접 접근
- [hyparquet](https://github.com/hyparam/hyparquet): browser HTTP range, row 및 column projection
- [Cosmograph library docs](https://cosmograph.app/docs-lib/): Parquet와 browser graph rendering 가능. 본 계획은 current cosmos renderer를 adapter 뒤에 두며 full product 종속을 전제하지 않음

## 구현 전 blocker

1. 운영자 go가 필요하다.
2. U0 gold positive 및 hard negative set이 없다.
3. exact evidence resolver의 cold P95와 transfer가 아직 측정되지 않았다.
4. `scan-screener-os`의 public valuation licensing P0가 승인 대기다. Universe는 해당 필드를 사용하지 않아야 한다.
5. workspace의 landing 및 ui 대량 삭제는 본 작업과 무관한 기존 변경이다. 구현 시 HEAD 복구 여부와 다른 세션 소유권을 먼저 확인해야 한다.

## 다음 단일 행동

운영자 go 이후 `tests/_attempts/dartlabUniverse/` U0만 착수한다. U0 품질 게이트를 통과하기 전 UI나 map artifact를 변경하지 않는다.
