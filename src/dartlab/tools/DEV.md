# tools/ 개발 문서

AI 에이전트, 보고서 생성, 대화형 분석에서 재사용하는 빌딩블록.
LLM 의존성 없이 독립 동작. Company 인스턴스 또는 Polars DataFrame을 직접 받는다.

## 모듈 구조

```
tools/
├── __init__.py   # chart, table, text 재export
├── chart.py      # Plotly 재무 차트 + ChartSpec JSON 프로토콜 (optional: plotly)
├── table.py      # DataFrame 가공 (YoY, 성장률, 피벗, 한국어 포맷)
├── text.py       # 텍스트 분석 (키워드 추출, 감성 분석, 숫자 추출)
└── network.py    # vis.js 네트워크 시각화 (optional: networkx)
```

## chart.py — 재무 차트

### 두 가지 경로

1. **Plotly 직행**: `chart.revenue_trend(c).show()` → Plotly Figure
2. **ChartSpec 경로**: `chart.spec_revenue_trend(c)` → JSON dict → `chart.chart_from_spec(spec).show()`

ChartSpec은 JSON 프로토콜이라 Plotly 없이도 생성 가능. 프론트엔드(Svelte)에서도 같은 스펙을 소비한다.

### 범용 차트 (DataFrame → Plotly)

| 함수 | 용도 |
|------|------|
| `line(df, x, y)` | 시계열 라인 차트 |
| `bar(df, x, y, stacked)` | 바 / 누적 바 차트 |
| `pie(df, names, values)` | 파이 차트 |
| `waterfall(labels, values)` | 폭포(브릿지) 차트 |

### 재무 템플릿 차트 (Company → Plotly)

| 함수 | 용도 |
|------|------|
| `revenue_trend(c)` | 매출·영업이익·순이익 + 영업이익률 콤보 |
| `cashflow_pattern(c)` | 영업/투자/재무 CF 패턴 |
| `dividend_analysis(c)` | DPS + 배당수익률 + 배당성향 |
| `balance_sheet_composition(c)` | 유동/비유동 자산 스택 바 |
| `profitability_ratios(c)` | 영업이익률·순이익률·ROE 라인 |

### ChartSpec 생성기 (Company → JSON dict, plotly 불필요)

| 함수 | chartType | 데이터 소스 |
|------|-----------|------------|
| `spec_revenue_trend(c)` | combo | finance annual IS |
| `spec_cashflow_waterfall(c)` | waterfall | finance annual CF |
| `spec_balance_sheet(c)` | bar (stacked) | finance annual BS |
| `spec_profitability(c)` | line | ratioSeries |
| `spec_dividend(c)` | combo | report.dividend |
| `spec_insight_radar(c)` | radar | insights (10영역) |
| `spec_ratio_sparklines(c)` | sparkline | ratioSeries |
| `spec_diff_heatmap(c)` | heatmap | diff() |

### auto_chart

`chart.auto_chart(c)` → 사용 가능한 모든 ChartSpec을 자동 생성 (데이터 없는 차트는 skip).
삼성전자 기준 7개 스펙 생성 (combo, bar, line, waterfall, radar, sparkline, heatmap).

### chart_from_spec

`chart.chart_from_spec(spec)` → ChartSpec JSON을 Plotly Figure로 변환.
6개 chartType 지원: combo/bar/line, radar, waterfall, heatmap, sparkline, pie.

### 테마

DartLab 8색 팔레트 (`COLORS`). `_apply_theme(fig)` 으로 통일된 레이아웃 적용.

## table.py — DataFrame 가공

| 함수 | 용도 |
|------|------|
| `yoy_change(df, value_cols, pct)` | YoY 변동 컬럼 추가 (% 또는 절대) |
| `ratio_table(bs, is_, cf)` | BS·IS에서 부채비율·유동비율·ROE 등 계산 |
| `summary_stats(df, value_cols)` | mean/min/max/std/CAGR/trend 요약 |
| `growth_matrix(df, value_cols)` | 1Y/2Y/3Y/5Y CAGR 매트릭스 |
| `pivot_accounts(df)` | 재무제표 행=계정→열=계정 피벗 |
| `format_korean(df, unit, cols)` | 숫자 → 한국어 단위 (억원, 조원 등) |

## text.py — 텍스트 분석

| 함수 | 용도 |
|------|------|
| `extract_keywords(text, top_n)` | 빈도 기반 키워드 추출 (불용어 내장) |
| `sentiment_indicators(text)` | 긍정/부정/리스크 키워드 카운트 + 점수 |
| `extract_numbers(text, context_chars)` | 숫자 + 단위 + 맥락 추출 |
| `section_diff(a, b)` | 두 섹션 리스트의 추가/삭제/변경/유지 비교 |

한국어 재무 키워드 사전 내장: 긍정 22개, 부정 21개, 리스크 20개.

## 사용 예시

```python
from dartlab.tools import chart, table, text

c = dartlab.Company("005930")

# 차트
chart.revenue_trend(c).show()               # Plotly 직행
specs = chart.auto_chart(c)                 # 7개 ChartSpec
chart.chart_from_spec(specs[0]).show()      # spec → Plotly

# 테이블
table.yoy_change(c.dividend, value_cols=["dps"])
table.format_korean(c.BS, unit="백만원")

# 텍스트
text.sentiment_indicators(c.show("businessOverview")[0]["2024Q4"])
text.extract_numbers(c.show("companyOverview")[0]["2024Q4"])
```

## 테스트

`tests/test_tools_chart_table_text.py` — 17개 테스트 (chart spec/table/text 전체 커버)

## network.py — 관계 네트워크 시각화

### 설계 원칙

- **vis-network CDN** — 별도 설치 없이 HTML에서 로드
- **networkx** — 레이아웃 계산용 optional dependency (`charts` extra)
- **forceAtlas2Based** — 대형 그래프(1,600+ 노드)도 안정적인 물리 엔진
- **HTML 파일 생성 → 브라우저 오픈** — Jupyter/노트북/스크립트 어디서든 동일

### 사용 경로

```python
# ego 뷰 (Company에서)
c = dartlab.Company("005930")
c.network()         # → NetworkView (.show()로 브라우저)
c.network().show()  # 브라우저 오픈
c.network().save("삼성전자.html")  # 파일 저장

# 전체 시장 (모듈 레벨)
dartlab.network().show()

# DataFrame 뷰는 view 인자
c.network("members")   # 같은 그룹 계열사 DataFrame
c.network("edges")     # 출자/지분 연결 DataFrame
c.network("cycles")    # 순환출자 경로 DataFrame
c.network("peers")     # ego 서브그래프 DataFrame
```

### 클래스

| 클래스 | 위치 | 역할 |
|--------|------|------|
| `NetworkView` | `tools/network.py` | HTML 시각화 결과. `.show()` `.save()` |

### 주요 함수

| 함수 | 역할 |
|------|------|
| `render_network(nodes, edges, title, center_id)` | export_full/export_ego → NetworkView |
| `_prepare_vis_data(...)` | 노드/엣지 → vis.js 형식 변환 |
| `_build_html(...)` | vis.js HTML 문자열 생성 |

### 데이터 흐름

```
Company.network()
  → _ensureNetwork() → build_graph() + export_full() 캐싱
  → view=None → export_ego() → render_network() → NetworkView
  → view="edges" 등 → DataFrame 반환

dartlab.network()
  → build_graph() + export_full() → render_network() → NetworkView
```

### UI 기능

- **다크/라이트 테마** 전환 (DartLab 브랜딩 색상)
- **검색** — 회사명/종목코드 (`/` 키로 포커스)
- **그룹 패널** — 좌측, 그룹 클릭 시 해당 그룹 하이라이트
- **노드 클릭** — 연결된 회사만 하이라이트, 나머지 dim
- **툴팁** — 노드 hover: 회사 정보, 엣지 hover: 지분율/목적
- **줌 컨트롤** — 확대/축소/전체보기/초기화
- **엣지 방향** — 화살표로 출자/피출자 구분
- **노드 크기** — degree(연결수) 비례
- **ESC** — 하이라이트 초기화 + 전체보기

### 금지

- Plotly로 네트워크 그래프 그리지 않는다 (대형 그래프에서 뭉침, 방향 표시 불가)
- 전체 시장 그래프를 정적 이미지로 렌더링하지 않는다
