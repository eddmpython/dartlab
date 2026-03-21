# Notebooks 현황

## 개요
Jupyter 노트북. Google Colab에서 바로 실행 가능. `docs/`의 문서와 대응.

## 폴더 구조

```
notebooks/
├── getting-started/
│   └── quickstart.ipynb              # sections → show → trace → diff 빠른 시작
├── tutorials/                        # 한국어 학습용 (DART 중심)
│   ├── 01_quickstart.ipynb           # 핵심 흐름 (sections/show/trace/diff)
│   ├── 02_financial_statements.ipynb # BS/IS/CF 재무제표
│   ├── 03_timeseries.ipynb           # 시계열 분석
│   ├── 04_ratios.ipynb               # 47개 재무비율
│   ├── 05_report_data.ipynb          # 정기보고서 데이터
│   ├── 06_disclosure.ipynb           # 공시 텍스트
│   ├── 07_advanced.ipynb             # 고급 활용
│   ├── 08_cross_company.ipynb        # 기업 간 비교
│   └── 09_edgar.ipynb                # EDGAR (미국)
└── showcase/                         # 영문 글로벌 쇼케이스 (DART+EDGAR)
    ├── 01_quickstart.ipynb           # 3 lines to analyze any company
    ├── 02_financial_analysis.ipynb   # Statements, time series, ratios
    ├── 03_kr_us_compare.ipynb        # Samsung vs Apple side-by-side
    ├── 04_risk_diff.ipynb            # Risk disclosure change tracking
    ├── 05_sector_screening.ipynb     # Screen by financial criteria
    ├── 06_insight_anomaly.ipynb      # 7-area grading + anomaly detection
    ├── 07_network_governance.ipynb   # Corporate network & governance
    ├── 08_signal_trend.ipynb         # 48-keyword disclosure trends
    ├── 09_ai_analysis.ipynb          # AI-powered analysis (dartlab.ask)
    └── 10_disclosure_deep_dive.ipynb # Sections architecture deep dive
```

## Colab 링크 패턴
```
# tutorials (한국어)
https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/{filename}.ipynb

# showcase (영문)
https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/showcase/{filename}.ipynb
```

## 규칙
- 파일명: `XX_snake_case.ipynb`
- 첫 셀: 제목 + Colab 배지
- 두 번째 셀: `!pip install -q dartlab`
- 핵심 흐름: `c.sections → c.show(topic) → c.trace(topic) → c.diff()`
- 각 셀은 독립적으로 이해 가능하게 작성
- tutorials/: 한국어, DART 기능 중심
- showcase/: 영문, DART+EDGAR 글로벌 대상
