# Export — Excel 내보내기

## 구조

```
export/
├── excel.py       # Company → .xlsx 변환 (동적 스캔, 재무 피벗, 스타일링)
├── template.py    # 템플릿 기반 내보내기 (PRESETS)
├── sources.py     # 데이터 소스 트리 (registry 기반)
└── store.py       # 임시 저장소
```

## 핵심 동작

1. Company의 모든 property를 순회하여 DataFrame이면 시트 생성
2. 재무 시계열(IS/BS/CF): 연도별 피벗 → 헤더 파란색, 계정명 굵은체, 음수 빨강
3. registry `DataEntry`를 기준으로 시트 이름/순서 결정

## 알려진 품질 이슈 (CLAUDE.md § [트러블])

1. **계정명 영어/한글 혼재**: `_ACCOUNT_LABELS`에 28개만 한글, 나머지 snakeId 그대로
2. **연도 정렬 비일관**: report별 year 타입(str vs i64)과 정렬 방향 제각각
3. **segments None**: K-IFRS 주석 "부문정보" 파싱 실패
4. **salesOrder 컬럼명 v1/v2/v3**: 연도 헤더 추출 실패
5. **내보내기 속도**: `listAvailableModules()`가 모든 property 순차 로드

## 설계 원칙

- registry 기반: 시트 구성은 `_entries.py`의 DataEntry에 의존
- Tier 2 (Beta): 안정성은 아직 beta 수준
