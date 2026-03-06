# DartLab

**DART 공시 문서를 완벽하게 분석하는 Python 라이브러리**

DartLab은 DART 공시의 숫자와 텍스트를 모두 파싱하고,
분기·반기·사업보고서를 시계열로 정렬하여 기업 분석의 새로운 차원을 연다.

## 주요 기능

| 레이어 | 설명 | 상태 |
|--------|------|------|
| **정량 분석** | Bridge Matching으로 분기별 실적 역산 | 출시됨 |
| **정성 분석** | 텍스트 시계열 비교 및 변경점 추적 | 개발 중 |
| **교차 검증** | 숫자와 텍스트의 연결 분석 | 개발 중 |

## 빠른 시작

```bash
pip install dartlab
```

```python
from dartlab.finance.summary import analyze

result = analyze("data/docsData/005930.parquet")
print(result.dataframe)
```

자세한 내용은 [시작하기](getting-started/installation.md)를 참고하세요.
