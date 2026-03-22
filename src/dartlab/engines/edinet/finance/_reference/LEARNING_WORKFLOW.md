# EDINET 계정 매핑 학습 워크플로우

DART/EDGAR와 동일한 7단계 사이클.

## 매핑 파이프라인

```
원본 XBRL element_id + 일본어 account_name
  ↓ 1. prefix 제거 (jpcrp_, jppfs_, jpigp_, jpdei_, ifrs-full_)
  ↓ 2. ID_SYNONYMS (영문 XBRL element 동의어 통합)
  ↓ 3. ACCOUNT_NAME_SYNONYMS (일본어 계정명 동의어 통합)
  ↓ 4. CORE_MAP (핵심 계정 ~50개 → snakeId 오버라이드)
  ↓ 5. accountMappings.json 조회 (학습 결과 누적)
  ↓ 6. 전각/공백 정규화 후 재조회
  ↓ 7. 미매핑 → None
```

## 학습 사이클

### 1. measure — 현재 매핑률 측정
```python
from dartlab.engines.edinet.finance.mapper import EdinetMapper
rate = EdinetMapper.mappingRate(elements)
# {"total": N, "mapped": M, "rate": M/N}
```

### 2. collect — 미매핑 계정 수집
- 전체 parquet에서 매핑 실패 계정 추출
- 빈도순 정렬 → 상위 N개 우선 처리

### 3. analyze — 패턴 분석
- 공통 prefix (jpcrp_cor: 등)
- 유사 일본어명 (전각/반각 차이, 괄호 유무)
- DART 한국어 ↔ 일본어 대응 관계

### 4. learn — 규칙 기반 자동 분류
- J-GAAP taxonomy 기반 자동 매핑
- DART/EDGAR 기존 매핑에서 영문 element 공유분 자동 흡수
- rapidfuzz 유사도 매칭 (수동 검증 필요)

### 5. merge — accountMappings.json 병합
```python
# 학습 결과를 mapperData/accountMappings.json에 누적
import json
mappings = json.load(open("mapperData/accountMappings.json"))
mappings.update(new_learned)
json.dump(mappings, open("mapperData/accountMappings.json", "w"), ensure_ascii=False, indent=2)
```

### 6. verify — 매핑률 재측정 + 오매핑 검증
- 매핑률 증가 확인
- 오매핑 없는지 샘플 검증
- BS/IS/CF 각각 별도 측정

### 7. iterate — 다음 사이클
- 목표 매핑률 도달까지 반복
- DART: 34,171개 매핑 달성
- EDGAR: 10,680개 매핑 달성
- EDINET 목표: 실험 기반 점진 확장

## EDINET 특수 사항

### 3중 회계기준
- J-GAAP: jppfs_ prefix, 일본 고유 계정 (経常利益, 特別利益)
- IFRS: ifrs-full_ prefix, 국제 표준
- US-GAAP: us-gaap_ prefix (일부 기업만)

### 전각/반각 정규화
- `１２３` → `123`
- `（注）` → `(注)`
- `　` (전각 스페이스) → ` ` (반각)

### 회계연도
- 일본은 4월 시작~3월 결산이 다수 (국제 표준 1월~12월과 다름)
- context_id에서 기간 추출 시 주의

## 파일 구조
```
finance/
├── mapper.py           # 7단계 매핑 파이프라인
├── mapperData/
│   └── accountMappings.json  # 학습 결과 누적 (초기: 빈 dict)
└── _reference/
    ├── LEARNING_WORKFLOW.md   # 이 문서
    └── taxonomy/              # J-GAAP/IFRS taxonomy 원본 (실험 후 추가)
```

## 참조
- DART 학습 워크플로우: `engines/dart/finance/_reference/LEARNING_WORKFLOW.md`
- EDGAR 학습 워크플로우: `engines/edgar/finance/_reference/LEARNING_WORKFLOW.md`
