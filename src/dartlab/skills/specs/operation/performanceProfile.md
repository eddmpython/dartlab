---
id: operation.performanceProfile
title: Performance Profile — Polars heap + py-spy + mprof 절차서
kind: curated
scope: builtin
status: drafted
category: operation
purpose: dartlab 성능 측정과 메모리 가드 공개 SSOT — Polars Rust heap OOM 가드 정황 진단 + py-spy CPU profile + mprof memory tracking + arrow flight 분석.
whenToUse:
  - performance profile
  - 성능 측정
  - Polars heap
  - py-spy
  - mprof
  - OOM 진단
inputs:
  - Company 인스턴스 또는 sweep 명령
outputs:
  - profile (CPU flamegraph / memory trace)
  - 회귀 회피 권고
toolRefs: []
knowledgeRefs:
  - operation.testing
sourceRefs:
  - dartlab://skills/operation.performanceProfile
requiredEvidence:
  - skillRef
  - executionRef
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: limited
  webAi:
    status: limited
  pyodide:
    status: limited
linkedSkills:
  - operation.testing
  - operation.code
---

## 3 측정 도구

### 1. py-spy (CPU flamegraph)

```bash
uv run py-spy record -o profile.svg --pid <pid>
# 또는
uv run py-spy top --pid <pid>
```

- hot function 식별 + Polars expression 비효율 검출.

### 2. mprof (memory tracking)

```bash
uv run mprof run --include-children python -X utf8 tests/_attempts/profile_sweep.py
uv run mprof plot
```

- per-Company heap growth 측정 (Polars Rust ~200-500MB / Company).
- gc.collect() 호출 후 회수율 0 검증.

### 3. arrow flight (column read 분석)

```python
import pyarrow.parquet as pq
table = pq.read_table("data/dart/finance/005930.parquet", columns=["account_id"])
print(table.nbytes)
```

- 컬럼 필터 효과 측정 (`_SECTIONS_REQUIRED_COLS` 최적화).

## 가드 룰

1. Company 1 개 ≈ 200-500MB Polars Rust heap (본 spec 강행).
2. 병렬 Company ≤ 2 (dartlab import 시 순차).
3. test sweep maxTargets=5 강행 (recipe sweep).
4. fixture scope `module` (test).
5. 새 cache → BoundedCache (heap 가드).

## 절차

```
1. baseline 측정 (변경 전 mprof / py-spy)
2. 변경 (코드 또는 cache 추가)
3. 재측정 (같은 명령)
4. 비교 → 회귀 (heap > +20%) 또는 개선 commit
```

## 기본 검증

- 모든 새 cache → BoundedCache.
- recipe sweep maxTargets=5 강행.
- profile 결과 incidents.md 기록.
