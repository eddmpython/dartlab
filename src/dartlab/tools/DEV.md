# tools/ 개발 문서

AI 에이전트, 보고서 생성, 대화형 분석에서 재사용하는 빌딩블록.

## 모듈 구조

```
tools/
├── chart.py      # Plotly 재무 차트 (optional: plotly)
├── table.py      # DataFrame 가공 (YoY, 포맷)
├── text.py       # 텍스트 분석 (키워드 추출)
└── network.py    # vis.js 네트워크 시각화 (optional: networkx)
```

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
