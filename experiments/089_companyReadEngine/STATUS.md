# 089 Company Read Engine

## 목표

`Company` 읽기 경로에서 **결과 완전 동일성**을 유지하면서 속도와 메모리를 함께 줄일 수 있는지 검증한다.

## 결과 요약

| 실험 | 대상 | exact | 핵심 결과 | 판정 |
|---|---|---:|---|---|
| 001 | baseline harness | 기준선 | `show/trace/topics/docs`가 대체로 700MB~1.3GB | 기준선 |
| 002 | Polars-only route split | 21/60 | `availableApiTypes`, `trace("BS")`, 일부 `show("BS")`는 exact + 26x~79x + 큰 메모리 절감 | **부분 채택** |
| 003 | topic-scoped docs only | 0/12 | docs `show()`는 40x~98x 빨라졌지만 payload 불일치 | 기각 |
| 004 | PyArrow scanner | 6/30 | exact는 `availableApiTypes`만, 002보다 느리고 무거움 | 기각 |
| 005 | DuckDB parquet_scan | 6/30 | exact는 `availableApiTypes`만, 005930 docs/meta는 baseline보다 peak 더 큼 | 기각 |

## 핵심 수치

- baseline
  - `show("BS")`: `5.468~7.748s`, peak `688.3~908.3MB`
  - `trace("BS")`: `6.810~9.686s`, peak `973.7~1362.0MB`
  - `show("companyOverview")`: `5.875~7.553s`, peak `691.6~964.0MB`
  - `topics`: `6.104~8.093s`, peak `714.4~902.9MB`

- 002 Polars-only route split
  - `availableApiTypes`: exact `6/6`, `26.44~37.08x`, peak `54.0~76.7%` 절감
  - `trace("BS")`: exact `6/6`, `45.34~78.99x`, peak `81.7~87.1%` 절감
  - `show("BS")`: exact `3/6`, `36.03~56.54x`, peak `75.9~80.6%` 절감
  - `topics`: exact `0/6`, 그래도 `6.60~10.41x`, peak `58.2~66.3%` 절감
  - `_sections` cache: `60/60`에서 생성 안 됨

- 003 Topic-scoped docs
  - docs `show()` exact `0/12`
  - 속도는 `40.81~97.58x` 빨라졌지만 block identity가 baseline과 다름

- 004 PyArrow
  - exact `6/30`, 전부 `availableApiTypes`
  - 002보다 실용성이 낮음

- 005 DuckDB
  - exact `6/30`, 전부 `availableApiTypes`
  - 005930 docs/meta에서는 peak `882~887MB`로 오히려 악화

## 결론

1. **지금 당장 승자는 002 방향이다.**
   `full sections`를 안 만드는 route split 자체는 맞았다.

2. **정확히 같은 결과가 이미 입증된 구간**
   - `availableApiTypes`
   - `trace("BS")`
   - 일부 `show("BS")`

3. **아직 exact가 아닌 구간**
   - `topics`
   - `index`
   - docs `show()`
   - report `trace()`

4. **의미 있는 기술 결론**
   - 이 repo 병목은 parquet scan보다 **그 뒤의 Python 재구성**이다.
   - 그래서 Arrow/DuckDB를 넣어도 002보다 좋아지지 않았다.
   - 다음 단계는 새 엔진보다 `002`를 production 코드에 녹이면서 docs/report exact reconstruction 규칙을 맞추는 쪽이다.
