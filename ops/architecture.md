# dartlab 아키텍처 — 전체 청사진

> 이 문서가 dartlab의 전체 축. 신규 기능/엔진 추가 시 이 문서를 먼저 확인하고, 체계를 벗어나지 않게 한다.

## 레이어 아키텍처

```
L0 (인프라)     core/          protocols, finance, docs, registry, search
L1 (데이터)     providers/     DART, EDGAR, EDINET
                gather/        외부 시장 데이터 (주가, 수급, 매크로, 뉴스)
                scan/          시장 횡단분석
                quant/         기술적 분석 (순수 NumPy 계산)
L2 (분석)       analysis/      재무 + 전망 + 가치평가
                credit/        독립 신용평가
                review/        블록식 조합 보고서 (analysis + credit)
L3 (AI)         ai/            적극적 분석가
L4 (표현)       vscode/        VSCode 확장

교차 관심사     guide/         안내 데스크 (모든 레이어에서 import 가능)
                viz/           시각화 (차트 + 다이어그램)
```

### import 방향 규칙

**L0 ← L1 ← L2 ← L3. 역방향 금지.**

- core/는 다른 레이어를 import하지 않는다
- gather/, scan/, quant/는 core/만 import
- analysis/, credit/는 core/ + L1만 import
- **analysis ↛ credit, credit ↛ analysis** — 같은 L2지만 상호 import 금지
- review만 analysis + credit 양쪽 소비
- ai/는 모든 하위 레이어 소비 가능
- guide/는 교차 관심사 — 모든 레이어에서 import 가능 (lazy import)

## 엔진 목록

| 엔진 | 레이어 | 진입점 | 역할 |
|------|--------|--------|------|
| Company | L0/L1 | `dartlab.Company("005930")` | 단일 기업 객체 (facade) |
| scan | L1 | `dartlab.scan("축")` | 시장 횡단분석 |
| gather | L1 | `c.gather("축")` | 외부 시장 데이터 수집 |
| quant | L1 | `c.quant()`, `dartlab.quant()` | 기술적 분석 |
| analysis | L2 | `c.analysis("그룹", "축")` | 재무 심층분석 |
| credit | L2 | `c.credit()` | 독립 신용평가 |
| review | L2 | `c.review()` | 블록식 조합 보고서 |
| search | L0 | `dartlab.search("키워드")` | 공시 원문 검색 |
| ai | L3 | `dartlab.ask("질문")` | AI 분석가 |
| viz | 교차 | `dartlab.viz.revenue(c)` | 시각화 |

## 호출 패턴

모든 엔진이 동일 패턴: `엔진("축")` 또는 `엔진("그룹", "축")`.

```python
# analysis — 2단계 (그룹 + 축)
c.analysis("financial", "수익성")
c.analysis("valuation", "가치평가")
c.analysis("forecast", "매출전망")

# scan — 2단계 (financial 그룹) 또는 1단계 (단일 축)
dartlab.scan("financial", "profitability")
dartlab.scan("governance")

# quant — 1단계 (metric)
c.quant()                    # 종합 판단
c.quant("indicators")        # 지표
c.quant("divergence")        # 재무-기술적 괴리

# credit — 단일
c.credit()
c.credit(detail=True)

# gather — 1단계
c.gather("price")
c.gather("ownership")

# 한글/영문 양방향 alias
c.analysis("financial", "profitability")  # 영문
c.analysis("financial", "수익성")         # 한글 — 동일 결과
```

## 데이터 출력 규칙

### scan 결과

**모든 scan 축은 동일한 컬럼 구조를 따른다:**

1. 첫 2컬럼: `종목코드`, `종목명` (필수)
2. 나머지: 축별 데이터 컬럼 (한글)
3. `_enrichWithKorean()` 함수가 영문→한글 변환 + 종목명 추가를 담당
4. 개별 축 구현에서 직접 한글 컬럼을 만들지 않는다 — `_enrichWithKorean`을 경유

**금지:**
- `corpName` 컬럼 반환 → `종목명`으로 통일
- 종목명 없는 결과 반환
- 영문 컬럼명과 한글 컬럼명 혼용

### analysis 결과

- dict 반환. keys는 camelCase (marginTrend, returnTrend 등)
- 시계열 데이터: `{"history": [{period, ...}, ...]}` 패턴
- None: 데이터 없으면 None 반환 (추정값 생성 금지)
- 금액: 원본 원 단위 (AI가 억/조로 변환)

### credit 결과

- dict 반환. `grade`, `healthScore`, `score`, `pdEstimate` 등
- `healthScore` = 100 - score (높을수록 건전)
- `detail=True`: narratives, metricsHistory 포함

## 신규 기능 추가 체크리스트

새 기능/엔진/축을 추가할 때 반드시 확인:

- [ ] **위치**: 기존 엔진에 들어가는가? 새 엔진이 필요한가?
- [ ] **레이어**: import 방향 규칙 준수하는가?
- [ ] **ops/ 문서**: 해당 엔진 ops/*.md 업데이트했는가?
- [ ] **guide 연동**: checkReady, handleError 구현했는가?
- [ ] **테스트**: 전용 unit test 작성했는가?
- [ ] **README**: 영문 + 한국어 양쪽 반영했는가?
- [ ] **시스템 프롬프트**: AI가 새 기능을 사용할 수 있는가?
- [ ] **CAPABILITIES**: generateSpec.py 재실행했는가?
- [ ] **데이터 일관성**: scan이면 종목코드+종목명 첫 2컬럼인가?
- [ ] **MEMORY.md**: 운영 방침 업데이트 필요한가?

## 관련 문서

| 문서 | 역할 |
|------|------|
| `ops/README.md` | 운영문서 진입점 |
| `ops/testing.md` | 테스트 체계 |
| `ops/{엔진}.md` | 엔진별 상세 설계 |
| `MEMORY.md` | AI 운영 방침 (메모리) |
