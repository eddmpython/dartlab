# 093: sections 파이프라인 메모리 최적화

## 상태: 완료 (부분 채택)

## 목표
sections 파이프라인의 메모리 사용량(회사당 피크 200-500MB)을 줄인다.

## 조사 결과 (세계적 기술 벤치마크)
- Polars streaming engine, DuckDB, LanceDB, Arrow IPC mmap, ColBERTv2 등 20개+ 기술 조사
- **결론**: 별도 포맷 변환 저장 없이 parquet 실시간 소비 유지하는 전제 하에, Python 측 최적화가 주력

## 적용한 최적화
1. **scan_parquet projection pushdown**: `_SECTIONS_REQUIRED_COLS` 7개만 select
2. **_expandStructuredRows generator 전환**: list 축적 → yield 방식, occurrence 인라인 카운트
3. **Categorical 인코딩**: chapter, blockType, textNodeType, cadenceScope
4. **DataFrame 빌딩 중 pop 소비**: topicMap/rowMeta/rowOrder 등 처리 완료 항목 즉시 해제

## 실측 결과 (삼성전자 005930)

| 지표 | Baseline | 최적화 후 | 변화 |
|------|----------|-----------|------|
| 소요 시간 | 5.82s | 5.30s | **-9%** |
| RSS | 491.3MB | 490.1MB | -1.2MB |

## 핵심 발견
- **RSS 490MB 중 ~350MB(72%)가 Polars Rust 힙** → Python gc 불가
- Python 측 최적화 여지는 ~90MB(18%)뿐
- DataFrame 97MB 중 96.35MB(99.3%)가 본문 텍스트(Utf8)
- Categorical 인코딩은 메타 컬럼(0.7%)에만 적용되므로 효과 미미
- **근본적 메모리 절감은 Polars Rust 힙을 줄이는 방향이어야 함**

## 채택 사항
- **generator 전환**: 속도 9% 향상 + 코드 구조 개선 → 채택
- **projection pushdown**: 미래 확장성(컬럼 추가 시 보호) → 채택
- **Categorical**: 미미하지만 올바른 방향 → 채택
- **pop 소비 패턴**: 코드 의도 명확화 → 채택

## 003: 2-pass PoC — 가설 기각

periodColumns 방식(topicMap 대신 period별 dict에 text 저장 + pop 해제)을 테스트.

| 지표 | 기존 방식 | 2-pass PoC | 변화 |
|------|----------|-----------|------|
| 피크 RSS | ~491MB | 494.4MB | +3MB (악화) |
| 소요 시간 | 3.33s | 9.22s | +177% (악화) |

**기각 사유**: dict 구조를 바꿔도 "모든 period의 text가 Python heap에 동시 존재"하는 문제는 해결 불가. load 단계(iterPeriodSubsets)에서 이미 404.9MB. text를 Python str로 추출하는 시점에서 복제가 발생하므로 dict 레이아웃 변경은 무의미.

## 근본 한계 정리

27MB parquet → 490MB RSS (18배 팽창)의 구조:
```
parquet (27MB) → Polars decompress (Rust heap ~150MB)
  → iter_rows → Python str 복제 (~150MB)
  → topicMap dict 축적 (~100MB)
  → DataFrame 재구성 (Rust heap ~97MB)
```

Python 측에서 할 수 있는 것은 ~90MB(18%)뿐. Rust heap 350MB(72%)는 gc 불가.
dict 구조 변경, Categorical, projection pushdown 모두 이 한계 안에서만 동작.

## 향후 방향 (실험 범위 밖)
- parquet 자체 크기 줄이기 (불필요 컬럼 제거, zstd 압축 레벨 조정)
- Polars Rust 측 streaming (Polars 신규 streaming engine 활용)
- text structure 분석을 Polars expression/Rust plugin으로 옮겨 Python str 복제 제거
- 진짜 2-pass: Pass1에서 text 아예 안 읽기 (메타만 축적) + Pass2에서 rowIdx 기반 text 회수 — 단, _expandStructuredRows가 text 내용에 의존하므로 구조 재설계 필요
