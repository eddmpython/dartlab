# Polars 조사 원장

- **우리 현재 사용**: 예. 코어 데이터프레임/쿼리 엔진. pin `polars>=1.0.0,<2` (emscripten/pyodide 는 빌트인 무버전). 실사용 lock 버전 1.41.1.
- **주 사용처**: `src/dartlab/scan/**` (cross-company scan), `frame/**`, gather/providers raw frame, pandera[polars] 계약, quant/analysis 전반. dartlab import 시 Polars Rust 힙 OOM 방어 환경변수 3종을 `src/dartlab/__init__.py`가 import 전에 설정.
- **마지막 조사일**: 2026-07-06
- **현재 결정**: 채택 (코어). 1.x 라인 유지. 신 streaming 엔진(larger-than-RAM)이 우리의 Polars 힙 OOM 병목과 정확히 정렬되므로 긍정 신호. 관찰하며 pin 상향 검토. GPU 엔진은 opt-in only, 강제 의존성은 기각(KILL). Polars Cloud 와 Lakehouse I/O(Delta·Iceberg)는 기각(로컬·HF-SSOT 원칙, 상시 클러스터 금지).

---

## 조사 이력

### 2026-07-06 (조사 시점 최신 1.x 라인, 우리 pin 1.41.1)

조사 경로: MCP WebSearch (공식 블로그·PyPI·GitHub releases·NVIDIA 개발자 블로그). WebFetch 본문 요약은 당시 API 529 과부하로 스니펫 기반 확인.

**카테고리별 관찰**

1. 코어 엔진 / streaming (OOC, larger-than-RAM)
   - Polars 가 streaming 엔진을 재작성(신 streaming engine, 2025-12 공식 announce). Q1 2026 에만 12 릴리스 / 778 PR / 95 기여자.
   - 신 streaming 엔진: 더 많은 join 타입 지원, 모든 주요 포맷에 streaming scan 구현, larger-than-RAM 실행.
   - 판단: 우리에게 가장 중요한 항목. CLAUDE.md 최상단 가드가 "Polars Rust 힙 OOM"이다. 신 streaming 엔진이 성숙하면 `collect(engine="streaming")` 경로의 peak RSS 개선 여지가 곧 직접 이득. 단 우리 코드는 이미 streaming collect 를 쓰므로 "새 기능"이 아니라 "엔진 품질 향상"으로 흡수. 검증은 `tests/_attempts/crossScanOoc/`에서 버전별 RSS 회귀 비교로.

2. GPU 백엔드 (cuDF / RAPIDS)
   - RAPIDS 25.06 이 GPU Polars streaming 엔진 추가(기존 in-memory GPU 엔진에서 streaming 으로 확장). NVIDIA GPU/cuDF 필요.
   - 판단: 기각(강제 의존성) / opt-in 만 허용. `mainPlan/polars-gpu-backend` 결정과 동일 유지. `cudf-polars` 의존성 추가는 KILL. GPU 는 compute-bound opt-in backend 로만, 기본 자동 GPU화 금지. GPU streaming 은 흥미롭지만 NVIDIA 전용이라 사용자 라이브러리 기본 경로가 될 수 없음.

3. Lakehouse I/O (Delta / Iceberg / Parquet)
   - Delta 와 Iceberg 모두 full read/write 지원(2026-04). 신 PartitionBy API. Iceberg/Delta scan 도 streaming.
   - 판단: 기각(현 단계). 우리는 HF parquet + source manifest 가 SSOT 이지 lakehouse 가 아님. `innovation-stack-research/02` Kill List 의 "Lakehouse 과잉 도입"과 일치. 재검토 조건: 정기 100GB+ workload 가 생기고 release proof 에 테이블 포맷 메타가 필요해질 때.

4. Polars Cloud / 분산
   - Polars Cloud 정식 출시(2025-12). query profiler 로 TPC-H 54% 빠르게, 비용 64% 절감(자체 벤치).
   - 판단: 기각. managed/분산 클라우드는 "운영자가 상시 클러스터 관리" 금지 원칙과 충돌(02 Kill List Spark/Ray/분산 항목과 동류). 로컬·HF 무료티어 원칙 위배.

5. 타입 시스템 (Decimals / Int128 / Categoricals)
   - Decimals 안정화, Int128 도입, Categoricals 전면 개편(2025-12).
   - 판단: 보류(watch), 긍정. 금액 정밀도(Decimal)는 재무 라이브러리에 가치. 다만 지금 당장 도입 이유는 없음. 재검토 트리거: 부동소수 반올림이 재무 셀 값에 문제를 일으킨 실측 사례가 나오면 Decimal 컬럼 채택 검토.

6. 버전 / pin 정책 / pyodide 제약
   - 조사 시점 2.0 없음. 1.x 라인이 Q1 2026 에 12 릴리스로 활발. pin `<2` 상한 여전히 안전.
   - pyodide(emscripten) 는 Polars 빌트인이라 무버전 pin 유지 필수(우리 pin 이 이미 sys_platform 분기).
   - 판단: pin `>=1.0.0,<2` 유지. 1.41 에서 최신 1.x 상향은 streaming 엔진 개선 흡수 목적이면 `_attempts` RSS 회귀 통과 후 검토.

**본 자료 (sources)**

- Polars in Aggregate, Apr 2026 (streaming 확장·Lakehouse I/O·Cloud profiling·PartitionBy): https://pola.rs/posts/polars-in-aggregate-apr26/
- Polars in Aggregate, Dec 2025 (Polars Cloud 출시·신 streaming 엔진·Categoricals·Decimals·Int128): https://pola.rs/posts/polars-in-aggregate-dec25/
- Q1 2026 요약 (12 릴리스·778 PR·streaming join 확대): https://x.com/DataPolars/status/2044799199477133344
- PyPI (larger-than-RAM streaming 명시): https://pypi.org/project/polars/
- GitHub Releases: https://github.com/pola-rs/polars/releases
- RAPIDS 25.06 GPU Polars streaming: https://developer.nvidia.com/blog/rapids-adds-gpu-polars-streaming-a-unified-gnn-api-and-zero-code-ml-speedups/

**결정 및 근거 (2026-07-06)**

- 코어 채택 유지. 변경 없음.
- 흡수할 것: 신 streaming 엔진 품질 향상이 pin 상향 시 OOM 완화로 이어질 기대. 단 검증(`_attempts` RSS 회귀) 없이 상향 금지.
- 기각 유지: GPU 강제 의존성, Polars Cloud, Lakehouse I/O. 모두 로컬/HF-SSOT·무클러스터 원칙과 충돌.
- 다음 실측 질문: 최신 1.x streaming 엔진이 우리 cross-scan 실제 parquet 레이아웃에서 1.41 대비 peak RSS 를 낮추는가?

### 2026-06-17 (이전 스냅샷, innovation-stack-research 00~04)

- GPU 는 `mainPlan/polars-gpu-backend` 로 분리. "선택적 GPU backend" 로만, 기본 자동 GPU화·`cudf-polars` 의존성 강제 금지 결정.
- 당시 성능 claim 기준 격상: 4개 패밀리 12개 쿼리, median 2.0x 이상, fallback 5% 이하(전문가 토론 반영).
- Polars GPU 는 OOC/streaming 문제의 기본 해법이 아니라 compute-bound opt-in 으로 명확히 분리(DuckDB OOC arm 과 문제 영역 구분).
