---
id: runtime.cacheStrategy
title: Cache Strategy — prompt cache + dartlab cache key
kind: curated
scope: builtin
status: drafted
category: runtime
purpose: Claude prompt cache + dartlab 자체 cache (BoundedCache / lru_cache / disk parquet) 전략 SSOT. cache hit 율 측정 + cache key 설계 표준.
whenToUse:
  - cache strategy
  - prompt cache
  - cache hit rate
  - BoundedCache
  - cache key
inputs:
  - tool call payload
  - cache key 설계
outputs:
  - cache hit / miss metric
  - cache invalidation 트리거
toolRefs: []
knowledgeRefs:
  - runtime.toolComposition
sourceRefs:
  - dartlab://skills/runtime.cacheStrategy
requiredEvidence:
  - skillRef
  - executionRef
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: supported
  pyodide:
    status: limited
linkedSkills:
  - runtime.toolComposition
---

## 3 cache layer

### 1. Claude prompt cache

- 5 분 TTL (Anthropic 기본).
- system prompt + tool definitions 고정 → cache breakpoint.
- 효과: ~90% cost 감축 (cached input).

### 2. dartlab BoundedCache (in-memory)

- Polars heap 가드 (`operation.performanceProfile`).
- per-Company 200~500MB → max 2 Company 동시 (사용자 메모리).
- fixture scope `module` (test).

### 3. Disk parquet cache

- 영구 저장 (`data/cache/*.parquet` 또는 HF dataset).
- key: `<axis>_<target>_<period>.parquet`.
- invalidation: schema 변경 시 manual delete.

## cache key 설계

```python
def cache_key(axis, target, period, **kwargs):
    """axis-target-period + sorted kwargs hash"""
    base = f"{axis}_{target}_{period}"
    extra = "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
    return f"{base}_{hash(extra)}"
```

## 측정

```python
from dartlab.cache.metrics import getCacheStats
print(getCacheStats())
# {"hits": 1234, "misses": 56, "hit_rate": 0.957, "size_mb": 234}
```

## 강행 룰

1. 모든 새 cache → `BoundedCache` 사용 (heap 가드).
2. Claude prompt cache breakpoint → system prompt 변경 최소화.
3. disk cache → schema 변경 시 invalidation 절차 박힘.

## 기본 검증

- cache hit 율 ≥ 80% (production).
- size 한계 명시 (BoundedCache max_entries).
- Claude API 측 `cache_creation_input_tokens` 측정 (실 cache 작동 확인).
