# 104_rustNative -- sections 파이프라인 Rust(pyo3) 마이그레이션 PoC

## 목적
sections 수평화 파이프라인의 핵심 병목(parseTextStructureWithState)을
pyo3 Rust로 교체하여 성능 향상을 실측한다.

## 실험 목록

| # | 파일 | 목표 | 결과 | 상태 |
|---|------|------|------|------|
| 001 | 001_benchmark.py | Python vs Rust 성능 비교 | 콜드 1.3x, 캐시 0.8x | 기각 |

## 001 결과 상세

**데이터**: 삼성전자(005930) 179블록, 17.6M 문자

| 모드 | Python | Rust | 배율 |
|------|--------|------|------|
| 캐시 워밍 50회 | 6.93s | 8.97s | 0.8x (Python 우세) |
| 콜드 스타트 1회 | 0.230s | 0.171s | 1.3x |
| 콜드 columnar+DF | 0.230s | 0.182s | 1.3x |

- 정합성: 100% (50블록 전수 비교)
- Python lru_cache(16384)가 반복 호출에서 Rust를 압도

## 핵심 발견

1. **parseTextStructureWithState 단독 포팅은 ROI 부족**
   - Python lru_cache + CPython 내장 str 연산이 이미 효율적
   - Rust 계산 이득을 Python↔Rust 경계 변환(str 복사, dict 생성)이 상쇄

2. **의미 있는 개선을 위한 조건**
   - 전체 파이프라인(mapper+chunker+textStructure+DataFrame 조립) 통째로 Rust
   - parquet I/O부터 최종 Polars DataFrame까지 Python 경유 없이 Rust에서 완결
   - 포팅 범위: ~3000줄 → 비용 대비 효과 재검토 필요

3. **현재 파이프라인에서 진짜 병목**
   - dict → DataFrame 조립: 57% (Python dict 수천개 생성 비용)
   - textStructure 파싱: 24% (이번 실험 대상)
   - 즉, textStructure만 Rust로 옮겨도 전체의 24% 중 30%만 절감 = 전체 7%

## 다음 방향

- **C안 재검토**: Polars lazy + expression 체인으로 dict 중간단계 자체를 제거
- **전체 파이프라인 Rust**: 비용 높지만 5-10x 가능 (parquet→DataFrame 직행)
- **현실적 최적화**: Python 레벨에서 dict 생성 최소화 (tuple/namedtuple 전환)
