# 테이블 수평화 개선

## 현재 상태 (2026-03-18)

- 실제 show() 기준: **수평화 62.9%**, 원본 fallback 37.0%, 데이터 반환률 99.9%
- sections pipeline은 건드리지 않음 — Company의 show() 레이어에서만 처리
- 코드 위치: `company.py:_horizontalizeTableBlock()`

## 적용된 개선

1. **헤더 시그니처 그룹핑** — `_groupHeader()`로 기간별 다른 구조 분리
2. **matrix multi-column 분리** — vals ≤ headerNames일 때 `항목_헤더명` 분리
3. **sparse 감지** — 항목 >15, fillRate <0.5 → 원본 fallback
4. **수평화 실패 시 원본 텍스트 fallback**
5. **주석번호 정규화** — `(*)`, `(*1)`, `(*1,2)` → 제거 (75건 통합, 오탐 0)
6. **1 block topic 자동 반환** — `show("IS")` → 바로 DataFrame
7. **pure_kisu 차단 제거**

## 실험/기각 목록

| 접근 | 결과 | 판정 |
|------|------|------|
| fuzzy matching (RapidFuzz) | 오탐 심각 (사내이사≈사외이사=89%) | 기각 |
| suffix 분리 fuzzy | 전전기≈전기=80% 오탐 | 기각 |
| 괄호 기반 통합 | 813건 중 오탐 208건 (25.6%) | 기각 |
| 임계값 완화 (Jaccard 0.15, 목록 100) | +7.6%p이지만 엉망 수평화 증가 | 기각 |
| 임베딩 (ko-sroberta) | threshold 분리 불가, 속도 38분 | 기각 |
| 값 교차 검증 | DART에서 항목명 불일치 0건, 전제 틀림 | 기각 |
| 정규형(Normal Form) 단독 | 기존보다 -6.6%p | 기각 |
| Valentine (스키마 매칭) | 행 매칭 불가, 기수 오매칭 | 기각 |
| datamatch | 런타임 에러, 유지보수 중단 | 기각 |
| py_stringmatching | 설치 실패 (Visual Studio 필요) | 기각 |
| ML 분류기 (RandomForest) | +17%p이나 실패 recall 낮음 | 규칙 3개만 추출 |

**핵심 교훈**: 외부 도구/통계적 유사도보다 **dartlab 정규화(94%)가 JaroWinkler(75%)보다 정확**. DART 항목 매칭은 한국어 정규화 + 도메인 지식이 핵심.

## 다음 단계: 캐노니컬 스키마

### 검증 결과

삼성전자 1종목: **51.7% → 73.0% (+21.3%p)**

### 핵심 아이디어

기간별 독립 파싱 → **전 기간 동시 스캔**.

```
사전계산 (Company 초기화 시 1회):
  전 기간 테이블 동시 스캔 →
  1. canonical header (가장 많은 기간에 등장하는 헤더)
  2. canonical items (전 기간 항목 합집합)
  3. synonym map (같은 위치의 표기 변형 자동 통합)
  4. tableCategory (이력형/목록형 전 기간 통계로 확정)
  → CanonicalSchema 캐시

show() 호출:
  스키마 로드 → 확정된 구조로 파싱 → synonym map으로 정규화
```

### 실험 결과

- `experiments/066_universalNorm/002_canonicalSchema.py` — 삼성전자 1종목 PoC (+21.3%p)
- `experiments/066_universalNorm/004_fullVerify.py` — **283종목 전수 검증: 34.1% (기존 58.4%보다 못함)**

### 전수 검증 결과 — 흡수 불가

```
스키마 성공: 43,723 (34.1%)
기존 성공:   74,832 (58.4%)
기존만 성공: 39,972건
스키마만 성공: 8,863건 (대부분 null 채움, 품질 나쁨)
```

- 삼성전자 1종목 +21.3%p는 **과대평가** — 283종목 전수에서는 -24.3%p
- 스키마만 성공한 블록의 실제 데이터: 대부분 null, 기수가 항목명에 붙어서 품질 나쁨
- **원인**: 에이전트 실험이 삼성전자의 특정 topic 구조에 과적합. 다른 종목의 다양한 구조에 대응 못 함

### 보조 개선

- **구조 분해 매칭** (F1 95%, 오탐 0) — core+qualifier+annotation 분리
- **셀 핑거프린트** (99.1% 구조 판별) — `_groupHeader` 보조 지표
- **ML에서 발견된 규칙 3개** — `avgDateRatio > 0.28` 등 이력형 조기 감지

### 중기 연구 후보

- **Magneto식 SLM+LLM 2단계** — 기존 매퍼 34,000개를 학습 데이터로 활용
- **STARMIE/Watchog 컬럼 임베딩** — 테이블 간 unionable 컬럼 자동 탐색
- **DART 테이블 수평화 연구는 세계적으로 없음** — dartlab이 최초

## 실험 폴더

- `experiments/064_tableHorizontal/` — 기본 수평화 개선 (020~026)
- `experiments/065_cellFingerprint/` — 셀 타입 핑거프린트
- `experiments/066_universalNorm/` — 정규형, 캐노니컬 스키마, ML 분류기
- `experiments/066_normalForm/` — 정규형 심화 실험 (001~010)
- `experiments/067_embeddingMatch/` — 임베딩 기반 매칭
