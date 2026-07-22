# dataUniversePerformance

Status: 개념확립 완료, 본진 승격 후보

카테고리: 데이터 작업대 전종목 조회 성능

## 문제

현 EDGAR `scanAccount("sales", freq="Q")` 는 17,367개 파일을 작업 큐에 넣고,
CIK 매핑이 있는 파일만 개별 Polars 스캔한 뒤 회사별, 연도별 Python 반복문으로
분기를 만든다. 2026-07-22 로컬 실데이터 기준 실제로 읽을 후보는 6,758개지만
기준 실행은 약 45~56초가 걸렸다.

## 후보

1. `duckdbNative`: 런타임 Parquet를 DuckDB가 직접 읽고, predicate와 projection,
   회사-연도 축약을 한 SQL에서 수행한다. Python에는 약 5.3만 회사-연도 행만
   반환한다.
2. `polarsNative`: 같은 파일 집합을 하나의 Polars LazyFrame으로 스캔하고, 약
   99만 매칭행을 한 번에 수집한 뒤 벡터화된 분기 선택을 수행한다.
3. `duckdbAll`: 파일 pruning을 끈 비교군이다. 미상장 또는 ticker 미매핑 파일까지
   읽은 뒤 결과에서 제거하는 낭비를 수치화한다.

두 후보 모두 영속 색인이나 재가공 사본을 만들지 않는다. 파일 경로는 기존 런타임
EDGAR SSOT를 그대로 가리킨다.

## 의미 보존

- 식별자는 Parquet 내부 `cik`가 아니라 파일명 CIK다. 실데이터
  `0001790169.parquet`는 내부 `cik=0000000000` 행을 포함하므로 이 차이가 실제
  결과 누락을 만든다.
- FY는 소스에서 첫 값이다.
- Q1~Q3은 절댓값이 가장 작은 값을 쓰고, 동률은 값과 소스 행 순서로 결정한다.
- Q1~Q3이 모두 있을 때만 Q4를 `FY - Q1 - Q2 - Q3`로 계산한다. 하나라도 없으면
  FY를 Q4로 둔다.
- 최종 스키마는 `stockCode`, `corpName`, 최신순 기간 열이다.

## 실행

```text
uv run python -X utf8 tests/_attempts/dataUniversePerformance/bench.py
bash tests/test-lock.sh tests/_attempts/dataUniversePerformance/test_prototype.py -v
```

## 판정 기준

- 기준 결과와 종목, 기간, 값이 동일해야 한다.
- 기준 대비 elapsed가 유의미하게 감소해야 한다.
- peak RSS가 작업대 예산 안에 있어야 하며, DuckDB에는 512 MiB spill 한도를 둔다.
- DART와 EDGAR 동시 실행은 순차 실행보다 실측상 이득이 있을 때만 기본값으로 쓴다.

## 실데이터 규모

2026-07-22 로컬 런타임 SSOT 기준이다.

| 항목 | 수치 |
| --- | ---: |
| EDGAR finance 전체 | 17,367 files, 722,576,045 bytes |
| ticker map 고유 CIK | 8,023 |
| 실제 존재하는 listed CIK 파일 | 6,758 files, 391,490,940 bytes |
| sales 필터 통과 원천행 | 986,695 |
| source-native 축약 후 company-year 행 | 53,005 |
| 최종 결과 | 5,153 stocks x 76 periods, shape 5,153 x 78 |

현 로그의 `17,367 파일 스캔`은 작업 큐 크기다. production processor는 파일명
CIK가 ticker map에 없으면 parquet를 열기 전에 반환하므로 실제 source 후보는
6,758개다. 새 경로는 처음부터 이 6,758개 경로만 manifest에 넣는다.

## 단일 계정 격리 벤치

각 arm은 별도 프로세스에서 실행했고 RSS를 worker 내부에서 10 ms 간격으로
측정했다. OS page cache 상태에 따라 현재 경로는 34.9~59.5초 범위였으므로 절대
시간보다 같은 run의 arm 차이와 반복 범위를 함께 본다.

| arm | elapsed sec | peak RSS MiB | 결과 shape | 판정 |
| --- | ---: | ---: | ---: | --- |
| current file jobs | 34.91 | 256.3 | 5,153 x 78 | 기준 |
| DuckDB, 4 threads, 512 MiB limit | 6.16 | 663.7 | 5,153 x 78 | 빠르나 메모리 큼 |
| DuckDB, 8 threads, 512 MiB limit | 4.92 | 666.9 | 5,153 x 78 | 속도 최상급, 메모리 큼 |
| DuckDB, 4 threads, 64 MiB limit | 5.96 | 343.8 | 5,153 x 78 | 권장 균형점 |
| DuckDB, 2 threads, 64 MiB limit | 9.00 | 334.8 | 5,153 x 78 | 메모리 소폭 절약 |
| DuckDB, 512-file batches | 6.66 | 341.8 | 5,153 x 78 | peak 이점 거의 없음 |
| DuckDB, all 17,367 files | 12.95 | 950.9 | 5,153 x 78 | file pruning 필수 |
| Polars one LazyFrame | 4.84 | 922.7 | 5,153 x 78 | 메모리 때문에 기각 |
| Arrow bounded, 256 files | 26.41 | 378.4 | 5,153 x 78 | 안전하지만 느려 기각 |

권장 arm은 DuckDB 4 threads와 64 MiB engine limit다. 현재 대비 약 5.9배
빠르고, 느린 기준 반복과 비교하면 약 10배까지 빨랐다. 다만 process peak RSS는
현재보다 약 88 MiB 높다. DuckDB limit는 버퍼와 hash aggregate의 spill 한도이지
Python, 파일 manifest, 라이브러리 자체 메모리를 포함한 process hard cap이 아니다.
따라서 이 결과를 64 MiB process 메모리라고 표현하면 안 된다.

file pruning은 선택 사항이 아니다. 같은 512 MiB DuckDB 설정에서 17,367개 전체
경로는 12.95초와 950.9 MiB, listed 6,758개 경로는 6.16초와 663.7 MiB였다.

## 실데이터 정확도

`verify.py`가 현 production 결과와 후보 결과를 `check_exact=True`로 비교했다.

| candidate | shape | exact all-cell parity |
| --- | ---: | --- |
| DuckDB native | 5,153 x 78 | PASS |
| Polars native | 5,153 x 78 | PASS |

초기 비교에서 `2020Q4`에 1 ULP 차이가 있었다. production은
`FY - sum(Q1, Q2, Q3)`이고 첫 prototype은 `FY - Q1 - Q2 - Q3` 순서였다.
괄호 순서를 production과 동일하게 만든 뒤 전 셀 exact parity를 통과했다.

또한 파일명 식별자 사용은 실제 결손을 막는다. `0001790169.parquet`의 일부 내부
행은 `cik=0000000000`이지만 파일명은 ZSTK의 올바른 CIK다. 내부 `cik`로 join한
초기 SQL은 ZSTK 한 종목을 누락했고, 파일명 CIK로 바꾼 뒤 5,153종목이 일치했다.

## KR과 US 스케줄

DART와 EDGAR provider를 먼저 import한 뒤 같은 프로세스에서 순차와 병렬을
각각 격리 측정했다. 두 작업은 같은 로컬 디스크와 메모리 대역폭을 공유한다.

| EDGAR 경로 | schedule | elapsed sec | peak RSS MiB |
| --- | --- | ---: | ---: |
| current | sequential | 45.72 | 438.8 |
| current | parallel | 48.82 | 451.6 |
| DuckDB 64 MiB | sequential | 6.35 | 612.2 |
| DuckDB 64 MiB | parallel | 7.41 | 619.8 |

현재 경로의 병렬은 6.8%, 최적화 경로의 병렬은 16.8% 느렸다. 이 머신에서는
KR과 US 로컬 finance scan을 같은 concurrency group으로 묶어 순차 실행하는 것이
맞다. 서로 다른 원격 I/O 또는 다른 물리 디스크라는 증거가 있을 때만 병렬화해야
한다. cold import 자체를 두 thread에서 동시에 시작한 첫 실험에서는 Python module
lock deadlock도 발생했으므로 owner import와 registry 준비는 worker 시작 전에 끝내야
한다.

## 여러 metric 한 번에 읽기

`scanAccountsDuckDbNative` prototype은 `sales`와 `operating_profit`의 tag set을
`requested_tags(tagLower, measureId)` 관계로 만들고 EDGAR parquet와 한 번 join한다.
group key에 `measureId`, 파일명 CIK, fiscal year를 함께 넣으므로 각 계정을 별도
호출한 의미를 유지한다.

실데이터 한 번 scan 결과:

| 요청 | elapsed sec | peak RSS MiB | 결과 |
| --- | ---: | ---: | --- |
| sales + operating_profit fused | 6.88 | 451.1 | 5,153 x 78 + 5,074 x 78 |

synthetic contract test는 두 measure가 한 SQL source scan에서 각각 올바른 Q4를
만드는 것을 검증한다. 별도 production 두 호출과의 실데이터 전 셀 parity는 이번
시간 안에 추가 측정하지 않았으므로, 승격 gate에서 반드시 보강한다.

본진의 최소 내부 owner-bulk 계약은 다음 형태가 적합하다.

```text
scanAccounts(
    measureIds: tuple[str, ...],
    *,
    freq: "Q" | "Y",
    universe: listed CIK snapshot,
) -> record batches of
    (market, stockCode, corpName, measureId, period, value)
```

이는 새 공개 axis가 아니다. 외부 사용자는 계속 `dartlab.data("query", ...)` 한 번으로
여러 measure를 요청하고, data planner가 EDGAR owner의 batch callable을 한 번 호출한
뒤 request partition 또는 factor projection으로 나눈다. wide frame dict는 기존
`scanAccount` 호환 adapter에서만 만든다. factor projection은 long record batch를
직접 받아 pivot 비용도 피한다.

## 최종 판정

1. 승격 1순위는 listed filename-CIK path pruning과 DuckDB source-native aggregation,
   4 threads, 64 MiB engine limit다.
2. 여러 EDGAR account 요청은 반드시 tag-to-measure 관계로 fuse해 파일을 한 번만
   읽는다. 계정별 `scanAccount` 반복은 factor-store 작업대에 부적합하다.
3. KR과 US local finance owner는 이 머신에서 병렬이 더 느리므로 같은 local-I/O
   concurrency group에서 순차 실행한다.
4. Polars one-shot은 가장 빠르지만 922.7 MiB peak 때문에 승격하지 않는다.
5. Arrow bounded arm은 메모리 hardening fallback 참고값으로 남기되 기본 경로로
   승격하지 않는다.

남은 승격 gate는 fused multi-measure의 production exact parity, cancellation과
continuation 경계, 다른 계정 유형과 annual 모드 실데이터 parity, 여러 머신에서의
memory ceiling 재측정이다.
