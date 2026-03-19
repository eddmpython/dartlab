# Notebooks 현황

## 개요
Jupyter 노트북. Google Colab에서 바로 실행 가능. `docs/`의 문서와 대응.

## 폴더 구조

```
notebooks/
├── getting-started/
│   └── quickstart.ipynb        # sections → show → trace → diff 빠른 시작
└── tutorials/
    ├── 01_quickstart.ipynb      # 핵심 흐름 (sections/show/trace/diff)
    ├── 02_financial_statements.ipynb  # BS/IS/CF 재무제표
    ├── 03_timeseries.ipynb      # 시계열 분석
    ├── 04_ratios.ipynb          # 47개 재무비율
    ├── 05_report_data.ipynb     # 정기보고서 데이터
    ├── 06_disclosure.ipynb      # 공시 텍스트
    ├── 07_advanced.ipynb        # 고급 활용
    ├── 08_cross_company.ipynb   # 기업 간 비교
    └── 09_edgar.ipynb           # EDGAR (미국)
```

## Colab 링크 패턴
```
https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/{filename}.ipynb
```

## 규칙
- 파일명: `XX_snake_case.ipynb`
- 첫 셀: 제목 + Colab 배지
- 두 번째 셀: `!pip install -q dartlab`
- 핵심 흐름: `c.sections → c.show(topic) → c.trace(topic) → c.diff()`
- 각 셀은 독립적으로 이해 가능하게 작성
