---
title: DartLab
---

# DartLab

DART 공시 문서의 재무제표, 주석, 텍스트를 파싱하고 시계열로 정렬하는 Python 라이브러리.

## 무엇을 할 수 있나

종목코드 하나면 된다. 14개 분석 모듈이 공시 문서에서 데이터를 추출하고 시계열로 정렬한다.

| 분류 | 모듈 | 설명 |
|------|------|------|
| 재무제표 | summary, statements, segment, costByNature | 요약재무정보, BS/IS/CF, 부문별 매출, 비용구조 |
| 주주/자본 | majorHolder, shareCapital | 최대주주, 의결권, 발행/유통주식 |
| 사업 현황 | dividend, employee, subsidiary, affiliate, bond, rawMaterial | 배당, 직원, 출자, 관계기업, 채무증권, 설비 |
| 텍스트 | mdna | 이사의 경영진단 및 분석의견 |

데이터가 로컬에 없으면 GitHub Releases에서 자동으로 다운로드한다.

## 빠른 시작

```python
from dartlab import Company

samsung = Company("005930")

result = samsung.analyze()
result.FS    # 전체 재무제표 시계열 (Polars DataFrame)
result.BS    # 재무상태표
result.IS    # 손익계산서
```

## 다음 단계

- [설치](getting-started/installation.md)
- [빠른 시작](getting-started/quickstart.md)
- [Bridge Matching](user-guide/bridge-matching.md)
- [API Reference](api/overview.md)
