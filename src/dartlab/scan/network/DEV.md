# network/ — 관계 네트워크 엔진

상장사 간 출자/지분 관계를 분석하여 그룹 분류, 순환출자 탐지, 네트워크 시각화를 제공한다.

## 파일 구조

```
providers/dart/network/
├── __init__.py      # build_graph() 파이프라인 오케스트레이터
├── scanner.py       # DART report parquet 스캔 (투자/주주/공시GT)
├── edges.py         # 엣지 구축 + 중복 제거 + 지분율 정규화
├── classifier.py    # 5단계 균형 분류 (docs → well-known → 출자 → 주주 → 인명)
├── cycles.py        # DFS 순환출자 탐지
└── export.py        # JSON export (full/overview/ego)
```

시각화 렌더러는 `tools/network.py`에 분리.

## 데이터 흐름

```
DART report parquet (investedCompany, majorHolder)
  ↓ scanner.py: scan_invested() / scan_major_holders() / scan_affiliate_docs()
원본 DataFrame + docs ground truth
  ↓ edges.py: build_invest_edges() / build_holder_edges() / deduplicate_edges()
정제된 엣지 (invest_edges, corp_edges, person_edges)
  ↓ classifier.py: classify_balanced()  [5단계]
code_to_group 매핑
  ↓ cycles.py: detect_cycles()
순환출자 경로
  ↓ export.py: export_full() / export_ego()
JSON (nodes, edges, groups, industries, cycles)
  ↓ tools/network.py: render_network()
NetworkView → .show()로 브라우저 오픈
```

## 분류 파이프라인 (5단계)

| 단계 | 이름 | 설명 |
|------|------|------|
| 0 | docs lock | 공시 원문 ground truth (관계회사 현황)로 확정 |
| 1 | well-known | 하드코딩된 주요 100+ 대기업 시드 |
| 2 | investment | 출자 방향 전파 (경영참여 목적 우선) |
| 3 | corporate shareholder | 법인 대주주 흡수 |
| 4 | personal shareholder | 공유 인명 주주 → 최대 연결 그룹 |
| 5 | keyword fallback | 사명 키워드 매칭 + 나머지 독립 처리 |

## Company 인터페이스

`providers/dart/company.py`에서 `network()` 메서드 제공:

```python
c = dartlab.Company("005930")

# 시각화 (view=None → NetworkView)
c.network()              # ego 1홉 → NetworkView
c.network(hops=2)        # ego 2홉
c.network().show()       # 브라우저 오픈
c.network().save("out.html")

# DataFrame 뷰
c.network("members")     # 같은 그룹 계열사
c.network("edges")       # 출자/지분 연결
c.network("cycles")      # 순환출자 경로
c.network("peers")       # ego 서브그래프

# 모듈 레벨 (전체 시장)
dartlab.network().show()
```

`_ensureNetwork()`가 `build_graph()` + `export_full()`을 1회 실행하고 `_cache`에 저장.

## DataFrame 뷰 컬럼

### members
`종목코드, 회사명, 시장, 업종, 자기`

### edges
`종목코드, 회사명, 유형, 방향, 목적, 지분율, 그룹`

### cycles
`경로, 길이, 회사목록`

### peers
`종목코드, 회사명, 그룹, 업종, 연결수, 자기`

## 시각화 (tools/network.py)

- **vis-network CDN** — 설치 불필요, HTML에서 로드
- **forceAtlas2Based** — 대형 그래프(1,600+ 노드) 물리 엔진
- **DartLab 브랜딩** — 다크/라이트 테마, `#ea4647` primary
- **인터랙션**: 노드 클릭 → 연결만 하이라이트, 그룹 클릭 → 그룹 하이라이트
- **검색**: 회사명/종목코드 (`/` 키)
- **툴팁**: 노드(회사 정보), 엣지(지분율/목적)
- **엣지 방향**: 화살표 (출자=파랑, 지분보유=초록)

### 클래스

| 클래스 | 위치 | 역할 |
|--------|------|------|
| `NetworkView` | `tools/network.py` | HTML 래퍼. `.show()` `.save()` |

### 함수

| 함수 | 역할 |
|------|------|
| `render_network(nodes, edges, title, center_id)` | export → NetworkView |

## 검증 데이터

- 43개 시나리오 테스트 (`tests/test_affiliate.py`)
- 삼성/현대차/SK/LG/롯데 필수 소속 검증
- 독립성 비율, 순환출자, 노드 수 범위 검증
- 실험 070 (018개 실험 완료)

## 금지

- Plotly로 네트워크 그래프 그리지 않는다
- `sectionMappings.json`처럼 무분별한 수작업 하드코딩 금지 — well-known 시드 추가는 실험 검증 후
- Company에서 `build_graph` 직접 import 금지 — 반드시 `_ensureNetwork()` 경유
