# Bridge Matching

## 개념

DART 공시의 요약재무정보는 매년 계정명이 미세하게 바뀔 수 있다.

- K-IFRS 개정으로 계정명 변경
- 회사의 자체적인 표기 변경
- 연결/별도 전환 시 계정 구조 변동

Bridge Matching은 이런 변경에도 불구하고 같은 성격의 계정을 자동으로 연결한다.

## 작동 원리

1. **세그먼테이션**: 공시 문서에서 요약재무정보 테이블을 추출
2. **파싱**: 계정명과 금액을 구조화
3. **브릿지 매칭**: 인접 연도 간 계정명을 매칭
4. **변경점 탐지**: 매칭률이 급격히 떨어지는 지점을 breakpoint로 판단

## 사용법

```python
from dartlab.finance.summary import analyze

result = analyze("data/docsData/005930.parquet")

# 브릿지 결과 확인
for bridge in result.bridges:
    print(f"기간: {bridge.fromPeriod} → {bridge.toPeriod}")
    print(f"매칭: {bridge.matchCount}개")
```

## 핵심 계정

DartLab은 다음 핵심 계정의 시계열 연속성을 우선 보장한다:

| 계정 | 설명 |
|------|------|
| 매출액 | 수익 기반 |
| 영업이익 | 본업 수익성 |
| 당기순이익 | 최종 수익 |
| 자산총계 | 규모 지표 |
| 부채총계 | 재무건전성 |
| 자본총계 | 순자산 |
