# 테스트 체계

> 커버리지 90% 목표. 엔진별 최소 80%. 새 기능은 테스트 없이 머지하지 않는다.

## 마커 체계

| 마커 | 의미 | 병렬 | CI 실행 |
|------|------|------|--------|
| `unit` | 순수 로직, mock만, 데이터 로드 없음 | 안전 | 항상 |
| `integration` | Company 1개 로딩 필요 | 주의 | CI |
| `heavy` | 대량 데이터, 단독 실행 | 금지 | 수동 |
| `requires_data` | 로컬 parquet 필요 | 주의 | skip |

## 메모리 규칙

- **Polars는 네이티브 Rust 힙. gc.collect()로 회수 불가.**
- Company 1개 ≈ 200~500MB. 동시 3개 = OOM.
- conftest.py에 1200MB 초과 시 pytest.exit() 안전장치.
- fixture scope → `module` (session scope 금지).
- `pytest` 직접 호출 금지 → `bash scripts/test-lock.sh` 사용.

## 실행 방법

```bash
# unit만 (빠름, 항상)
bash scripts/test-lock.sh tests/ -m "unit" -v --tb=short

# integration (데이터 필요)
bash scripts/test-lock.sh tests/ -m "not unit and not heavy and not requires_data" -v --tb=short

# heavy (단독)
bash scripts/test-lock.sh tests/ -m "heavy" -v --tb=short
```

## 엔진별 테스트 파일

각 엔진은 최소 1개 전용 테스트 파일을 가진다.

| 엔진 | 테스트 파일 | 상태 |
|------|-----------|------|
| Company | `test_company.py`, `test_company_*.py` | 있음 |
| scan | `test_scan_axes.py`, `test_scanAccount.py` | 있음 (일관성 테스트 추가 필요) |
| analysis | `test_new_axes.py`, `test_analyst.py` | 있음 |
| credit | `test_credit.py` | 보강 필요 |
| quant | — | **없음** → test_quant_engine.py 필요 |
| gather | `test_gather.py`, `test_gather_global.py` | 있음 |
| search | `test_search.py` | 있음 |
| review | `test_report_engine.py` | 보강 필요 |
| ai | `test_coding_local.py`, `test_coding_runtime.py` | 있음 |
| viz | `test_tools_chart.py` | 보강 필요 |

## 테스트 작성 규칙

1. **파일명**: `test_{모듈명}.py` (conftest가 아닌 개별 파일)
2. **마커**: 모든 테스트에 `pytestmark = pytest.mark.unit` 등 명시
3. **mock**: Company 데이터가 필요한 unit 테스트는 fixture로 mock
4. **assert**: 단순 `assert True` 금지 — 구체적 값 검증
5. **독립성**: 테스트 간 상태 공유 금지 (global 변수 사용 금지)

## CI 규칙

```yaml
# ci.yml test 작업
pytest tests/ -v --tb=short 
  -m "not requires_data and not heavy" 
  --benchmark-disable 
  --cov=dartlab --cov-report=xml
  --cov-fail-under=90
```

| 항목 | 기준 |
|------|------|
| 커버리지 | 90% 이상 (fail_under) |
| lint | ruff==0.11.6 고정 |
| format | ruff format |
| 벤치마크 | 별도 워크플로우 (CI에서 disable) |

## 커버리지 현황

| 시점 | 커버리지 | 비고 |
|------|---------|------|
| v0.8.0 | ~30% | 초기 |
| v0.8.3 | 29% | 신규 엔진 추가로 희석 |
| 목표 | 90%+ | 0.8 안정화 완료 기준 |
