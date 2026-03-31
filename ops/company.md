# Company

Company는 dartlab의 facade. 종목코드 하나로 모든 데이터에 접근한다.
dartlab의 모든 방향성은 Company에서 시작하고, Company로 돌아온다.

## 근본 전제

**모든 기간은 비교 가능해야 하고, 모든 회사는 비교 가능해야 한다.**

이것이 dartlab의 근본 전제다. sections 사상(topic × period 수평화)과 계정 표준화(XBRL 정규화)는 이 전제를 현실로 만드는 두 엔진이다. scan이 가능한 것도, analysis가 의미 있는 것도, 이 비교 가능성이 확보되어 있기 때문이다.

- 기간 비교 가능 → 같은 회사의 과거와 현재를 나란히 놓는다 (sections, diff)
- 기업 비교 가능 → 다른 회사의 같은 지표를 나란히 놓는다 (scan, analysis)

## 핵심 철학

- 비교 가능성이 모든 분석의 기반
- 완벽한 축을 세우는 게 모든 방향성
- Company → Analysis → Review → Scan 순서로 계층이 쌓인다
- 모든 개선은 **DART 먼저**, EDGAR는 DART 안정화 후 따라감

## sections 사상 — Company의 근간

sections(topic × period 수평화)가 회사의 전체 지도다. dartlab의 양대 축 중 하나.

```
sections = { topic: { period: content } }
```

- **finance**: sections보다 숫자가 강하다 → 해당 topic을 **대체**한다
- **report**: DART에만 있다 → 해당 topic에 **채운다**
- **EDGAR**: report 없이 sections + finance 대체만으로 완성

sections 위에 올라가는 소비 레이어는 두 가지뿐이다:
- **diff**: 기간간 텍스트 변화 감지 → `core/docs/diff.py`
- **viewer**: sections + index 메타데이터. 렌더러(HTML/Svelte/PDF)가 소비

source 우선순위: **finance > report > docs** (숫자 → 정형 → 서술)

개별 property(dividend, employee 등)는 sections 사상 이전의 우회로다.
Company 클래스에 직접 연결하지 않고, **show() 경로로만 접근**한다.

## 4 Namespace

```python
c.docs      # 원문 (sections 기반)
c.finance   # 숫자 (IS/BS/CF/CIS, ratios, timeseries)
c.report    # 정형 공시 (DART 전용)
c.profile   # 통합 (sections + finance + report merge)
```

기본 소비 경로는 **profile first** — `c.sections`는 `c.profile.sections`.

## 공통 인터페이스

### 핵심 — show/select (경량, 추천 경로)
```python
c.show(topic)                          # 특정 topic 데이터 (부분 빌드, 빠름)
c.show("IS", period="2023")           # 기간 필터
c.show("IS", period=["2022", "2023"]) # 세로 비교
c.select("IS", ["매출액", "영업이익"]) # 행/열 필터
c.select("IS", ["매출액"]).chart()     # 필터 + 시각화
c.topicSummaries()                     # 토픽 목록 + 200자 요약 (경량)
```

show/select는 **해당 topic만 부분 빌드** — 전체 sections를 로드하지 않는다.
AI가 데이터를 조회할 때는 show/select를 기본 경로로 사용한다.

### 탐색/추적
```python
c.index           # 전체 주제 목록
c.trace(topic)    # 출처 추적 (docs/finance/report 중 어디서 왔는지)
c.diff()          # 기간간 텍스트 변화
```

### namespace 3개
```python
c.docs             # 원문 접근
c.finance          # 재무제표 접근
c.profile          # 통합 프로필
```

### finance 바로가기
```python
c.BS / c.IS / c.CF / c.CIS       # 재무제표
c.ratios / c.ratioSeries          # 비율
c.timeseries                      # 시계열
```

### 메타
```python
c.sections / c.topics             # sections 지도
c.filings()                       # 공시 목록
c.insights                        # 등급 카드
c.market / c.currency             # 시장 정보
```

## sections 접근 경로 ⚠️

`c.sections`는 **전체 docs + finance + report를 통합 로드**한다. 메모리 소비가 크다.

### 성능 벤치마크 (삼성전자 005930, 2026-03-31 측정)

| 경로 | 시간 | 메모리 peak | 용도 |
|------|------|------------|------|
| `c.show("IS")` | **0.65초** | 92MB | 특정 topic 조회 |
| `c.select("IS", [...])` | **0.01초** | (show 캐시) | 행/열 추출 + 차트 |
| `c.topicSummaries()` | **0.69초** | 경량 | AI 경로 탐색 |
| `c.sections` | **19초** | **409MB** | 전체 지도 필요 시만 |
| `c.review("수익성")` 첫 호출 | **25초** | 411MB | Company 초기화 포함 |
| `c.review()` x3 추가 | **8초** | 367MB | 캐시 재사용 |
| `c.review()` 전체 | **83초** | 424MB | ⚠ 타임아웃 위험 |
| `c.analysis("수익성")` | **0.03초** | 357MB | review 이후 빠름 |

**규칙**: show/select로 충분하면 c.sections에 접근하지 않는다.
review() 전체 호출은 83초 → AI 코드 실행(60초 제한)에서 금지.

## 편의성 3원칙 (최우선)

sections 사상과 함께 dartlab의 양대 축. 모든 공개 API는 이 3가지를 동시에 만족해야 한다.

### 접근성
- **종목코드 하나면 끝난다**: 공개 함수는 종목코드(str) 또는 Company 하나만 받는다.
- **2-Tier 접근**: 루트 함수(`dartlab.X("005930")`) + Company 메서드(`c.X()`) 양쪽 모두 제공. 루트 함수가 1차 시민.
- **`import dartlab` 하나로 모든 공개 기능 접근**. 내부 엔진 경로는 사용자에게 노출하지 않는다.

### 속도
- **첫 호출 5초 이내**: Company 생성부터 첫 결과 반환까지 체감 지연 최소화.
- **lazy load 기본**: finance·report·docs는 접근 시점에 로드.
- **캐시 재사용**: 같은 세션 내 동일 Company는 BoundedCache로 재사용.

### 신뢰성
- **숫자는 원본 그대로**: DART/EDGAR 원본 수치 보존.
- **없으면 None**: 데이터가 없을 때 추정값을 만들지 않는다. 사용자가 판단한다.
- **출처 추적 가능**: `trace(topic)`로 source(docs/finance/report)를 항상 확인 가능.
- **에러는 명시적으로**: 파싱 실패·매핑 누락은 숨기지 않고 드러낸다.

이 원칙은 기존/신규 모든 공개 API에 소급 적용한다.

## canHandle 라우팅

```
dartlab.Company("005930")
    ↓ canHandle() 체인
    providers/dart/company.py   (priority=10, 한국 종목코드)
    providers/edgar/company.py  (priority=20, 미국 ticker)
```

- `dartlab.Company`는 facade → 엔진(`providers/dart/`, `providers/edgar/`)으로 canHandle 라우팅
- **하위 엔진은 상위 facade를 import하지 않는다** (import 방향 CI 검증)
- 새 국가 추가 시 core 수정 0줄 — provider 패키지만 추가 + canHandle/priority 구현

## 메모리 안전 ⚠️

> Polars는 네이티브 Rust 힙. Python gc.collect()로 회수 불가.
> Company 1개 ≈ 200~500MB. 3개 동시 로드 = OOM. (2회 크래시 이력)

- 캐시는 BoundedCache(pressure_mb=800) 사용
- 새 데이터 로드 경로 추가 시 `check_memory_and_gc()` 호출 검토

## 설계 원칙

- 개별 property(dividend, employee 등)는 **show() 경로**로 접근한다
- 하위 엔진은 상위 facade를 import하지 않는다 (import 방향 CI 검증)
- 새 국가 추가 시 core 수정 0줄 — provider 패키지만 추가

## 동기화

- Company 기능 변경 시 README(영문+한국어) 동시 반영
- 노트북 코드는 실행 확인 후에만 커밋

## 관련 코드

| 파일 | 역할 |
|------|------|
| `src/dartlab/company.py` | 루트 facade (canHandle 체인 라우팅) |
| `src/dartlab/core/protocols.py` | CompanyProtocol (@runtime_checkable) |
| `src/dartlab/providers/dart/company.py` | DART 엔진 (canHandle, priority=10) |
| `src/dartlab/providers/edgar/company.py` | EDGAR 엔진 (canHandle, priority=20) |
| `src/dartlab/core/docs/` | diff, viewer, bridge, topicGraph |
| `src/dartlab/core/finance/` | ratios, extract, period, labels |
