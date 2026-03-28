# dartlab API Reference (Skills용)

이 문서는 `scripts/generateSpec.py`에 의해 자동 생성됩니다.


---

## Python API (48개)

`import dartlab` 후 사용 가능한 공개 API.

| 이름 | 종류 | 설명 |
|------|------|------|
| `Company` | function | 종목코드/회사명/ticker → 적절한 Company 인스턴스 생성. |
| `Fred` | class | FRED 경제지표 facade. |
| `OpenDart` | class | OpenDART API 통합 클라이언트. |
| `OpenEdgar` | class | SEC public API facade. |
| `config` | module | dartlab 전역 설정. |
| `core` | module | - |
| `engines` | - | - |
| `llm` | module | LLM 기반 기업분석 엔진. |
| `ask` | function | LLM에게 기업에 대해 질문. |
| `chat` | function | 에이전트 모드: LLM이 도구를 선택하여 심화 분석. |
| `setup` | function | AI provider 설정 안내 + 인터랙티브 설정. |
| `search` | function | 종목 검색 (KR + US 통합). |
| `listing` | function | 전체 상장법인 목록. |
| `collect` | function | 지정 종목 DART 데이터 수집 (OpenAPI). |
| `collectAll` | function | 전체 상장종목 DART 데이터 일괄 수집. |
| `downloadAll` | function | HuggingFace에서 전체 시장 데이터 다운로드. |
| `scan` | function | 시장 전체 횡단분석 — 13축, 전부 Polars DataFrame. |
| `analysis` | function | 재무제표 완전 분석 — 14축, 단일 종목 심층. |
| `gather` | function | 외부 시장 데이터 통합 수집 — 4축, 전부 Polars DataFrame. |
| `network` | function | 한국 상장사 전체 관계 지도. |
| `audit` | function | 감사 Red Flag 분석. |
| `forecast` | function | 매출 앙상블 예측. |
| `valuation` | function | 종합 밸류에이션 (DCF + DDM + 상대가치). |
| `insights` | function | 7영역 등급 분석. |
| `simulation` | function | 경제 시나리오 시뮬레이션. |
| `governance` | function | 한국 상장사 전체 지배구조 스캔. |
| `workforce` | function | 한국 상장사 전체 인력/급여 스캔. |
| `capital` | function | 한국 상장사 전체 주주환원 스캔. |
| `debt` | function | 한국 상장사 전체 부채 구조 스캔. |
| `research` | function | 종합 기업분석 리포트. |
| `digest` | function | 시장 전체 공시 변화 다이제스트. |
| `scanAccount` | function | 전종목 단일 계정 시계열. |
| `scanRatio` | function | 전종목 단일 재무비율 시계열. |
| `plugins` | function | 로드된 플러그인 목록 반환. |
| `reload_plugins` | function | 플러그인 재스캔 — pip install 후 재시작 없이 즉시 인식. |
| `verbose` | module | bool(x) -> bool |
| `dataDir` | module | str(object='') -> str |
| `getKindList` | function | KRX KIND 상장법인 전체 목록. |
| `codeToName` | function | 종목코드 → 회사명. |
| `nameToCode` | function | 회사명 → 종목코드. 정확히 일치하는 첫 번째 결과. |
| `searchName` | function | 회사명 부분 검색. |
| `fuzzySearch` | function | 한글 fuzzy 종목 검색 — 초성 매칭 + Levenshtein 거리. |
| `chart` | module | Plotly 기반 재무 차트 도구. |
| `table` | module | 재무 테이블 가공 도구. |
| `text` | module | 텍스트 분석 도구. |
| `Review` | class | 분석 리뷰 — AnalysisReport + core/Report 통합. |
| `SelectResult` | class | select() 반환 객체 — DataFrame 위임 + 체이닝. |
| `ChartResult` | class | chart() 반환 객체 — 시각화 + 렌더링. |

### Python API 상세

#### ask
**Capabilities:** 자연어로 기업 분석 질문 (종목 자동 감지)
스트리밍 출력 (기본) / 배치 반환 / Generator 직접 제어
엔진 자동 계산 → LLM 해석 (Engine-First)
데이터 모듈 include/exclude로 분석 범위 제어
자체 검증 (reflect=True)
**Requires:** AI: provider 설정 (dartlab.setup() 참조)
**AIContext:** 재무비율, 추세, 동종업계 비교를 자동 계산하여 LLM에 제공
sections 서술형 데이터 + finance 숫자 데이터 동시 주입
tool calling provider에서는 LLM이 추가 데이터 자율 탐색

#### chat
**Capabilities:** LLM이 dartlab 도구를 자율적으로 선택/실행
원본 공시 탐색, 계정 시계열 비교, 섹터 통계 등 심화 분석
최대 N회 도구 호출 반복 (multi-turn)
도구 호출/결과 콜백으로 UI 연동
**Requires:** AI: provider 설정 (tool calling 지원 provider 권장)
**AIContext:** ask()와 동일한 기본 컨텍스트 + 저수준 도구 접근
LLM이 부족하다 판단하면 추가 데이터 자율 수집

#### setup
**Capabilities:** 전체 AI provider 설정 현황 테이블 표시
provider별 대화형 설정 (키 입력 → .env 저장)
ChatGPT OAuth 브라우저 로그인
OpenAI/Gemini/Groq/Cerebras/Mistral API 키 설정
Ollama 로컬 LLM 설치 안내
**Requires:** 없음

#### search
**Capabilities:** 한글 입력 시 DART 종목 검색 (종목명, 종목코드)
영문 입력 시 EDGAR 종목 검색 (ticker, 회사명)
부분 일치, 초성 검색 지원 (KR)
**Requires:** 데이터: listing (자동 다운로드)

#### listing
**Capabilities:** KR 전체 상장법인 목록 (KOSPI + KOSDAQ)
종목코드, 종목명, 시장구분, 업종 포함
US listing은 향후 지원 예정
**Requires:** 데이터: listing (자동 다운로드)

#### collect
**Capabilities:** 종목별 DART 공시 데이터 직접 수집 (finance, docs, report)
멀티키 병렬 수집 (DART_API_KEYS 쉼표 구분)
증분 수집 — 이미 있는 데이터는 건너뜀
카테고리별 선택 수집
**Requires:** API 키: DART_API_KEY

#### collectAll
**Capabilities:** 전체 상장종목 DART 공시 데이터 일괄 수집
미수집 종목만 선별 수집 (mode="new") 또는 전체 재수집 (mode="all")
멀티키 병렬 수집 (DART_API_KEYS 쉼표 구분)
카테고리별 선택 (finance, docs, report)
**Requires:** API 키: DART_API_KEY

#### downloadAll
**Capabilities:** HuggingFace 사전 구축 데이터 일괄 다운로드
finance (~600MB, 2700+종목), docs (~8GB, 2500+종목), report (~320MB, 2700+종목)
이어받기/병렬 다운로드 지원 (huggingface_hub)
전사 분석(scanAccount, governance, digest 등)에 필요한 데이터 사전 준비
**Requires:** 없음 (HuggingFace 공개 데이터셋)

#### scan
**Capabilities:** governance: 최대주주 지분, 사외이사, 감사위원회
workforce: 임직원 수, 평균급여, 근속연수
capital: 배당수익률, 배당성향, 자사주
debt: 부채비율, 차입금 의존도, 이자보상
account: 전종목 단일 계정 시계열 (매출액, 영업이익 등)
ratio: 전종목 단일 재무비율 시계열 (ROE, 영업이익률 등)
screen: 재무 조건 스크리닝
peer: 동종업계 피어 그룹
audit: 감사의견, 감사인 변경
insider: 최대주주 변동, 자기주식
network: 기업 관계 네트워크
watch: 공시 변화 모니터링
digest: 시장 전체 변화 다이제스트
**Requires:** 데이터: 축별로 다름 (dartlab.downloadAll() 참조)
governance/workforce/capital/debt/audit/insider: report
account/ratio/screen: finance
network/watch/digest: docs
**AIContext:** ask()/chat()에서 시장 전체 데이터를 컨텍스트로 주입
종목간 비교 분석의 데이터 소스

#### analysis
**Capabilities:** Part 1 — 사업구조: 수익구조, 자금조달, 자산구조, 현금흐름
Part 2 — 핵심비율: 수익성, 성장성, 안정성, 효율성, 종합평가
Part 3 — 심화분석: 이익품질, 비용구조, 자본배분, 투자효율, 재무정합성
각 축은 Company를 받아 dict를 반환하는 순수 함수 집합
review()가 이 결과를 소비하여 구조화 보고서 생성
**Requires:** 데이터: finance (자동 다운로드)
**AIContext:** reviewer()가 analysis 결과를 소비하여 AI 해석 생성
ask()에서 재무분석 컨텍스트로 활용
70개 calc* 함수의 개별 결과를 LLM에 주입 가능

#### gather
**Capabilities:** price: OHLCV 시계열 (KR Naver/US Yahoo, 기본 1년, 최대 6000거래일)
flow: 외국인/기관 수급 동향 (KR 전용, Naver)
macro: ECOS(KR 12개) / FRED(US 25개) 거시지표 시계열
news: Google News RSS 뉴스 수집 (최근 30일)
자동 fallback 체인, circuit breaker, TTL 캐시
**Requires:** price/flow/news: 없음 (공개 API)
macro: API 키 — ECOS_API_KEY (KR) 또는 FRED_API_KEY (US)
**AIContext:** ask()/chat()에서 주가/수급/거시 데이터를 컨텍스트로 주입 가능
기업 분석 시 시장 데이터 보충 자료로 활용

#### network
**Capabilities:** 상장사 간 지분 관계 네트워크 시각화
브라우저에서 인터랙티브 그래프 표시
노드(기업) + 엣지(지분 관계) 구조
**Requires:** 데이터: docs (자동 다운로드)

#### audit
**Capabilities:** 감사의견 추이 (최근 5년, 적정/한정/부적정/의견거절)
감사인 변경 이력 + 변경 사유
계속기업 불확실성 플래그
핵심감사사항 (KAM) 추출
내부회계관리제도 검토의견
**Requires:** 데이터: docs + report (자동 다운로드)

#### forecast
**Capabilities:** 매출 시계열 기반 앙상블 예측 (ARIMA + 선형 + 지��평활)
업종 성장률 가중 보정
신뢰구간 (80%, 95%) 제공
최대 N년 전망 (기본 3년)
**Requires:** 데이터: finance (자동 다운로드)

#### valuation
**Capabilities:** DCF (잉여현금흐름 할인 모형)
DDM (배당할인 모형)
상대가치 (PER/PBR/EV-EBITDA 동종업계 비교)
적정주가 범위 산출
**Requires:** 데이터: finance (자동 다운로드)

#### insights
**Capabilities:** 수익성, 성장성, 안정성, 효율성, 현금흐름, 밸류에이션, 배당 — 7영역
각 영역 A~F 등급 부여 + 근거 지표
종합 등급 + 강점/약점 요약
동종업계 백분위 위치
**Requires:** 데이터: finance (자동 다운로드)

#### simulation
**Capabilities:** 거시경제 시나리오별 재무 영향 시뮬레이션
기본 시나리오: 금리 인상, 경기 침체, 원��재 급등, 환율 변동
매출/영업이익/순이익 변동 추정
업종별 민감도 차등 적용
**Requires:** 데이터: finance (자동 다운로드)

#### governance
**Capabilities:** 전체 상장사 지배구조 횡단 비교
최대주주 지분율, 사외이사 비율, 감사위원회 설치 여부
지분 변동 추이, 특수관계인 거래
**Requires:** 데이터: report (dartlab.downloadAll("report")로 사전 다운로드)

#### workforce
**Capabilities:** 전체 상장사 임직원 현황 횡단 비교
임직원 수, 평균 근속연수, 평균 급여, 성별 비율
업종별/규모별 비교
**Requires:** 데이터: report (dartlab.downloadAll("report")로 사전 다운로드)

#### capital
**Capabilities:** 전체 상장사 주주환원 정책 횡단 비교
배당수익률, 배당성향, 자사주 매입/소각 이력
유상증자/무상증자 이력
**Requires:** 데이터: report (dartlab.downloadAll("report")로 사전 다운로드)

#### debt
**Capabilities:** 전체 상장사 부채 구조 횡단 비교
부채비율, 차입금 의존도, 이자보상배율
단기/장기 차입금 구성, 사채 발행 현황
**Requires:** 데이터: report (dartlab.downloadAll("report")로 사전 다운로드)

#### research
**Capabilities:** 재무분석 + 시장분석 통합 리포트
섹션별 선택 생성 가능
재무비율 추세, 동종업계 비교, 시장 포지션
구조화된 마크다운 출력
**Requires:** 데이터: finance + docs (자동 다운로드)

#### digest
**Capabilities:** 전체 상장사 공시 변화 중요도 순위
섹터별 필터링
텍스트 변화량 + 재무 변화 통합 스코어링
DataFrame/마크다운/JSON 출력
**Requires:** 데이터: docs (dartlab.downloadAll("docs")로 사전 다운로드)

#### scanAccount
**Capabilities:** 전체 상장종목의 특정 계정 시계열 횡단 비교
한글/영문 계정명 모두 지원 ("매출액" = "sales")
DART(KR) + EDGAR(US) 양쪽 지원
분기별/연간 선택, 연결/별도 선택
**Requires:** 데이터: finance (dartlab.downloadAll("finance")로 사전 다운로드)

#### scanRatio
**Capabilities:** 전체 상장종목의 특정 재무비율 시계열 횡단 비교
ROE, 영업이익률, 부채비율 등 주요 비율 지원
DART(KR) + EDGAR(US) 양쪽 지원
분기별/연간 선택
**Requires:** 데이터: finance (dartlab.downloadAll("finance")로 사전 다운로드)

#### plugins
**Capabilities:** 설치된 dartlab 플러그인 자동 탐색
플러그인 메타데이터 (이름, 버전, 제공 topic) 조회
**Requires:** 없음

#### reload_plugins
**Capabilities:** 새로 설치한 플러그인 즉시 인식 (세션 재시작 불필요)
entry_points 재스캔
**Requires:** 없음

---

## CLI (18개 명령)

`dartlab <command>` 형태로 사용.

| 명령 | 설명 |
|------|------|
| `show` | topic 기반 데이터 조회 |
| `search` | 종목코드/회사명 검색 |
| `statement` | 재무제표 출력 (BS/IS/CIS/CF/SCE) |
| `sections` | docs 수평화 sections 출력 |
| `profile` | Company index/facts 출력 |
| `modules` | 사용 가능한 데이터 모듈 목록 |
| `ask` | 자연어 원스톱 AI 분석 |
| `chat` | 대화형 AI 분석 REPL |
| `report` | Markdown 분석 보고서 생성 |
| `excel` | 기업 데이터 Excel 내보내기 |
| `review` | 기업 분석 검토서 (데이터/AI) |
| `collect` | DART/EDGAR 데이터 수집 |
| `ai` | AI 분석 웹 인터페이스 실행 |
| `share` | 터널로 로컬 서버 외부 공유 |
| `status` | LLM 연결 상태 확인 |
| `setup` | LLM provider/API 키 설정 |
| `mcp` | MCP 서버 실행 (stdio) |
| `plugin` | 플러그인 관리 (list/create) |

---

## Data Modules (69개)

`core/registry.py` DataEntry 기반. 모듈 추가 = 한 줄 → 7곳 자동 반영.

### 시계열 재무제표 (finance)

| name | label | dataType | description |
|------|-------|----------|-------------|
| `annual.IS` | 손익계산서(연도별) | `timeseries` | 연도별 손익계산서 시계열. 매출액, 영업이익, 순이익 등 전체 계정. |
| `annual.BS` | 재무상태표(연도별) | `timeseries` | 연도별 재무상태표 시계열. 자산, 부채, 자본 전체 계정. |
| `annual.CF` | 현금흐름표(연도별) | `timeseries` | 연도별 현금흐름표 시계열. 영업/투자/재무활동 현금흐름. |
| `timeseries.IS` | 손익계산서(분기별) | `timeseries` | 분기별 손익계산서 standalone 시계열. |
| `timeseries.BS` | 재무상태표(분기별) | `timeseries` | 분기별 재무상태표 시점잔액 시계열. |
| `timeseries.CF` | 현금흐름표(분기별) | `timeseries` | 분기별 현금흐름표 standalone 시계열. |

### 공시 파싱 모듈 (report)

| name | label | dataType | description |
|------|-------|----------|-------------|
| `BS` | 재무상태표 | `dataframe` | K-IFRS 연결 재무상태표. finance XBRL 정규화(snakeId) 기반, 회사간 비교 가능. finance 없으면 docs fallback. |
| `IS` | 손익계산서 | `dataframe` | K-IFRS 연결 손익계산서. finance XBRL 정규화 기반. 매출액, 영업이익, 순이익 등 전체 계정 포함. |
| `CF` | 현금흐름표 | `dataframe` | K-IFRS 연결 현금흐름표. finance XBRL 정규화 기반. 영업/투자/재무활동 현금흐름. |
| `fsSummary` | 요약재무정보 | `dataframe` | DART 공시 요약재무정보. 다년간 주요 재무지표 비교. |
| `segments` | 부문정보 | `dataframe` | 사업부문별 매출·이익 데이터. 부문간 수익성 비교 가능. |
| `tangibleAsset` | 유형자산 | `dataframe` | 유형자산 변동표. 취득/처분/감가상각 내역. |
| `costByNature` | 비용성격별분류 | `dataframe` | 비용을 성격별로 분류한 시계열. 원재료비, 인건비, 감가상각비 등. |
| `dividend` | 배당 | `dataframe` | 배당 시계열. 연도별 DPS, 배당총액, 배당성향, 배당수익률. |
| `majorHolder` | 최대주주 | `dataframe` | 최대주주 지분율 시계열. 지분 변동은 경영권 안정성의 핵심 지표. |
| `employee` | 직원현황 | `dataframe` | 직원 수, 평균 근속연수, 평균 연봉 시계열. |
| `subsidiary` | 자회사투자 | `dataframe` | 종속회사 투자 시계열. 지분율, 장부가액 변동. |
| `bond` | 채무증권 | `dataframe` | 사채, CP 등 채무증권 발행·상환 시계열. |
| `shareCapital` | 주식현황 | `dataframe` | 발행주식수, 자기주식, 유통주식수 시계열. |
| `executive` | 임원현황 | `dataframe` | 등기임원 구성 시계열. 사내이사/사외이사/비상무이사 구분. |
| `executivePay` | 임원보수 | `dataframe` | 임원 유형별 보수 시계열. 등기이사/사외이사/감사 구분. |
| `audit` | 감사의견 | `dataframe` | 외부감사인의 감사의견과 감사보수 시계열. 적정 외 의견은 중대 위험 신호. |
| `boardOfDirectors` | 이사회 | `dataframe` | 이사회 구성 및 활동 시계열. 개최횟수, 출석률 포함. |
| `capitalChange` | 자본변동 | `dataframe` | 자본금 변동 시계열. 보통주/우선주 주식수·액면 변동. |
| `contingentLiability` | 우발부채 | `dataframe` | 채무보증, 소송 현황. 잠재적 재무 리스크 지표. |
| `internalControl` | 내부통제 | `dataframe` | 내부회계관리제도 감사의견 시계열. |
| `relatedPartyTx` | 관계자거래 | `dataframe` | 대주주 등과의 매출·매입 거래 시계열. 이전가격 리스크 확인. |
| `rnd` | R&D | `dataframe` | 연구개발비용 시계열. 기술 투자 강도 판단. |
| `sanction` | 제재현황 | `dataframe` | 행정제재, 과징금, 영업정지 등 규제 조치 이력. |
| `affiliateGroup` | 계열사 | `dataframe` | 기업집단 소속 계열회사 현황. 상장/비상장 구분. |
| `fundraising` | 증자감자 | `dataframe` | 유상증자, 무상증자, 감자 이력. |
| `productService` | 주요제품 | `dataframe` | 주요 제품/서비스별 매출액과 비중. |
| `salesOrder` | 매출수주 | `dataframe` | 매출실적 및 수주 현황. |
| `riskDerivative` | 위험관리 | `dataframe` | 환율·이자율·상품가격 리스크 관리. 파생상품 보유 현황. |
| `articlesOfIncorporation` | 정관 | `dataframe` | 정관 변경 이력. 사업목적 추가·변경으로 신사업 진출 파악. |
| `otherFinance` | 기타재무 | `dataframe` | 대손충당금, 재고자산 관련 기타 재무 데이터. |
| `companyHistory` | 연혁 | `dataframe` | 회사 주요 연혁 이벤트 목록. |
| `shareholderMeeting` | 주주총회 | `dataframe` | 주주총회 안건 및 의결 결과. |
| `auditSystem` | 감사제도 | `dataframe` | 감사위원회 구성 및 활동 현황. |
| `affiliate` | 관계기업투자 | `dataframe` | 관계기업/공동기업 투자 변동 시계열. 지분법손익, 기초/기말 장부가 포함. |
| `investmentInOther` | 타법인출자 | `dataframe` | 타법인 출자 현황. 투자목적, 지분율, 장부가 등. |
| `companyOverviewDetail` | 회사개요 | `dict` | 설립일, 상장일, 대표이사, 주소, 주요사업 등 기본 정보. |
| `holderOverview` | 주주현황 | `custom` | 5% 이상 주주, 소액주주 현황, 의결권 현황. majorHolder보다 상세한 주주 구성. |

### 서술형 공시 (disclosure)

| name | label | dataType | description |
|------|-------|----------|-------------|
| `business` | 사업의내용 | `text` | 사업보고서 '사업의 내용' 서술. 사업 구조와 현황 파악. |
| `companyOverview` | 회사개요정량 | `dict` | 공시 기반 회사 정량 개요 데이터. |
| `mdna` | MD&A | `text` | 이사의 경영진단 및 분석의견. 경영진 시각의 실적 평가와 전망. |
| `rawMaterial` | 원재료설비 | `dict` | 원재료 매입, 유형자산 현황, 시설투자 데이터. |
| `sections` | 사업보고서섹션 | `dataframe` | 사업보고서 전체 섹션 텍스트를 topic(행) × period(열) DataFrame으로 구조화. leaf title 기준 수평 비교 가능. 연간+분기+반기 전 기간 포함. |

### K-IFRS 주석 (notes)

| name | label | dataType | description |
|------|-------|----------|-------------|
| `notes.receivables` | 매출채권 | `dataframe` | K-IFRS 매출채권 주석. 채권 잔액 및 대손충당금 내역. |
| `notes.inventory` | 재고자산 | `dataframe` | K-IFRS 재고자산 주석. 원재료/재공품/제품 내역별 금액. |
| `notes.tangibleAsset` | 유형자산(주석) | `dataframe` | K-IFRS 유형자산 변동 주석. 토지, 건물, 기계 등 항목별 변동. |
| `notes.intangibleAsset` | 무형자산 | `dataframe` | K-IFRS 무형자산 주석. 영업권, 개발비 등 항목별 변동. |
| `notes.investmentProperty` | 투자부동산 | `dataframe` | K-IFRS 투자부동산 주석. 공정가치 및 변동 내역. |
| `notes.affiliates` | 관계기업(주석) | `dataframe` | K-IFRS 관계기업 투자 주석. 지분법 적용 내역. |
| `notes.borrowings` | 차입금 | `dataframe` | K-IFRS 차입금 주석. 단기/장기 차입 잔액 및 이자율. |
| `notes.provisions` | 충당부채 | `dataframe` | K-IFRS 충당부채 주석. 판매보증, 소송, 복구 등. |
| `notes.eps` | 주당이익 | `dataframe` | K-IFRS 주당이익 주석. 기본/희석 EPS 계산 내역. |
| `notes.lease` | 리스 | `dataframe` | K-IFRS 리스 주석. 사용권자산, 리스부채 내역. |
| `notes.segments` | 부문정보(주석) | `dataframe` | K-IFRS 부문정보 주석. 사업부문별 상세 데이터. |
| `notes.costByNature` | 비용의성격별분류(주석) | `dataframe` | K-IFRS 비용의 성격별 분류 주석. |

### 원본 데이터 (raw)

| name | label | dataType | description |
|------|-------|----------|-------------|
| `rawDocs` | 공시 원본 | `dataframe` | 공시 문서 원본 parquet. 가공 전 전체 테이블과 텍스트. |
| `rawFinance` | XBRL 원본 | `dataframe` | XBRL 재무제표 원본 parquet. 매핑/정규화 전 원본 데이터. |
| `rawReport` | 보고서 원본 | `dataframe` | 정기보고서 API 원본 parquet. 파싱 전 원본 데이터. |

### 분석 엔진 (analysis)

| name | label | dataType | description |
|------|-------|----------|-------------|
| `ratios` | 재무비율 | `ratios` | financeEngine이 자동계산한 수익성·안정성·밸류에이션 비율. |
| `insight` | 인사이트 | `custom` | 7영역 A~F 등급 분석 (실적, 수익성, 건전성, 현금흐름, 지배구조, 리스크, 기회). |
| `sector` | 섹터분류 | `custom` | WICS 11대 섹터 분류. 대분류/중분류 + 섹터별 파라미터. |
| `rank` | 시장순위 | `custom` | 전체 시장 및 섹터 내 매출/자산/성장률 순위. |
| `keywordTrend` | 키워드 트렌드 | `dataframe` | 공시 텍스트 키워드 빈도 추이 (topic × period × keyword). 54개 내장 키워드 또는 사용자 지정. |
| `news` | 뉴스 | `dataframe` | 최근 뉴스 수집 (KR: Google News 한국어, US: Google News 영어). 날짜/제목/출처/URL. |

---

## Scan Axis (13개 축)

`dartlab.scan(axis, target)` 형태로 전종목 횡단분석.

| 축 | 한글 | 설명 | target 파라미터 | 필수 | 반환타입 |
|----|------|------|----------------|------|---------|
| `governance` | 거버넌스 | 지배구조 (지분율, 사외이사, 보수비율, 감사의견) | stockCode 필터 | - | DataFrame |
| `workforce` | 인력/급여 | 직원수, 평균급여, 성장률, 고액보수 | stockCode 필터 | - | DataFrame |
| `capital` | 주주환원 | 배당, 자사주(취득/처분/소각), 증자/감자, 환원 분류 | stockCode 필터 | - | DataFrame |
| `debt` | 부채구조 | 사채만기, 부채비율, ICR, 위험등급 | stockCode 필터 | - | DataFrame |
| `account` | 계정 | 전종목 단일 계정 시계열 (매출액, 영업이익 등) | snakeId | O | DataFrame |
| `ratio` | 비율 | 전종목 단일 재무비율 시계열 (ROE, 부채비율 등) | ratioName | O | DataFrame |
| `digest` | 다이제스트 | 시장 전체 공시 변화 다이제스트 | stockCode 필터 | - | DataFrame |
| `network` | 네트워크 | 상장사 관계 네트워크 (출자/지분/계열) | stockCode 필터 | - | dict |
| `cashflow` | 현금흐름 | OCF/ICF/FCF + 현금흐름 패턴 분류 (8종) | stockCode 필터 | - | DataFrame |
| `audit` | 감사리스크 | 감사의견, 감사인변경, 특기사항, 감사독립성비율 | stockCode 필터 | - | DataFrame |
| `insider` | 내부자지분 | 최대주주 지분변동, 자기주식 현황, 경영권 안정성 | stockCode 필터 | - | DataFrame |
| `quality` | 이익의 질 | Accrual Ratio + CF/NI 비율 — 이익이 현금 뒷받침되는지 | stockCode 필터 | - | DataFrame |
| `liquidity` | 유동성 | 유동비율 + 당좌비율 — 단기 지급능력 | stockCode 필터 | - | DataFrame |

**한글 별칭:**

- `account`: 계정
- `audit`: 감사, 감사리스크
- `capital`: 주주환원, 배당
- `cashflow`: 현금흐름, 현금
- `debt`: 부채
- `digest`: 다이제스트, 변화
- `governance`: 거버넌스, 지배구조
- `insider`: 내부자, 지분
- `liquidity`: 유동성, 유동비율
- `network`: 네트워크, 관계
- `quality`: 이익의질, 이익품질, 어닝퀄리티
- `ratio`: 비율
- `workforce`: 인력, 급여

**사용법:**

```python
import dartlab

dartlab.scan("governance")              # 전 상장사 거버넌스
dartlab.scan("governance", "005930")    # 삼성전자만 필터
dartlab.scan("ratio", "roe")            # 전종목 ROE
dartlab.scan("account", "sales")        # 전종목 매출액 시계열
dartlab.scan.topics()                   # 가용 축 목록
```

---

## Gather Axis (4개 축)

`dartlab.gather(axis, target)` 형태로 외부 시장 데이터 수집.

| 축 | 한글 | 설명 | target 필수 |
|----|------|------|------------|
| `price` | 주가 | OHLCV 시계열 (기본 1년) — Naver/Yahoo/FMP fallback | O |
| `flow` | 수급 | 외국인/기관 매매 동향 (KR 전용) | O |
| `macro` | 거시지표 | ECOS(KR 12개) / FRED(US 25개) 거시 시계열 | - |
| `news` | 뉴스 | Google News RSS — 최근 30일 | O |

**한글 별칭:**

- `flow`: 수급
- `macro`: 거시, 매크로
- `news`: 뉴스
- `price`: 주가

**사용법:**

```python
import dartlab

dartlab.gather("price", "005930")   # 삼성전자 주가
dartlab.gather("flow", "005930")     # 수급 동향
dartlab.gather("macro")              # KR 거시지표 전체
dartlab.gather("news", "삼성전자")    # 뉴스
```

---

## Company (통합 facade)

입력을 자동 판별하여 DART 또는 EDGAR 시장 전용 Company를 생성한다.
현재 DART Company의 공개 진입점은 **index -> show(topic) -> trace(topic)** 이다.

```python
import dartlab

kr = dartlab.Company("005930")
kr = dartlab.Company("삼성전자")
us = dartlab.Company("AAPL")

kr.market                    # "KR"
us.market                    # "US"
```

### 판별 규칙

| 입력 | 결과 | 예시 |
|------|------|------|
| 6자리 숫자 | DART Company | `Company("005930")` |
| 한글 포함 | DART Company | `Company("삼성전자")` |
| 영문 1~5자리 | EDGAR Company | `Company("AAPL")` |


### Company 메서드/프로퍼티

DartCompany에서 동적 추출 (69개).

| 이름 | 종류 | 설명 |
|------|------|------|
| `BS` | property | 재무상태표 (Balance Sheet) — 계정명 × 기간 DataFrame. |
| `CF` | property | 현금흐름표 (Cash Flow Statement) — 계정명 × 기간 DataFrame. |
| `CIS` | property | 포괄손익계산서 (Comprehensive Income Statement) — 계정명 × 기간 DataFrame. |
| `IS` | property | 손익계산서 (Income Statement) — 계정명 × 기간 DataFrame. |
| `SCE` | property | 자본변동표 (Statement of Changes in Equity) — 계정명 × 연도 DataFrame. |
| `analysis` | method | 재무제표 완전 분석 — 14축, 단일 종목 심층. |
| `annual` | property | 연도별 시계열 (연결 기준). |
| `ask` | method | LLM에게 이 기업에 대해 질문. |
| `audit` | method | 감사 리스크 종합 분석. |
| `canHandle` | method | DART 종목코드(6자) 또는 한글 회사명이면 처리 가능. |
| `capital` | method | 주주환원 분석 (배당, 자사주, 총환원율). |
| `chat` | method | 에이전트 모드: LLM이 도구를 선택하여 심화 분석. |
| `codeName` | method | 종목코드 → 회사명 변환. |
| `contextSlices` | property | LLM 투입용 context slice DataFrame. |
| `cumulative` | property | 분기별 누적 시계열 (연결 기준). |
| `currency` | property | 통화 코드 (DART 제공자는 항상 KRW). |
| `debt` | method | 부채 구조 분석 (차입금, 부채비율, 만기 구조). |
| `diff` | method | 기간간 텍스트 변경 비교. |
| `disclosure` | method | OpenDART 전체 공시 목록 조회. |
| `eventStudy` | method | 공시 발표일 전후 주가 비정상 수익률(CAR) 분석. |
| `filings` | method | 공시 문서 목록 + DART 뷰어 링크. |
| `forecast` | method | 매출 앙상블 예측 (다중 모델 가중 평균). |
| `gather` | method | 외부 시장 데이터 수집 — 4축 (price/flow/macro/news). |
| `getRatios` | method | Deprecated — use ``c.ratios`` property instead. |
| `getTimeseries` | method | Deprecated — use ``c.timeseries`` property instead. |
| `governance` | method | 지배구조 분석 (이사회, 감사위원, 최대주주). |
| `index` | property | 현재 공개 Company 구조 인덱스 DataFrame -- 전체 데이터 목차. |
| `insights` | property | 종합 인사이트 분석 (7영역 등급 + 이상치 + 요약). |
| `keywordTrend` | method | 공시 텍스트 키워드 빈도 추이 (topic x period x keyword). |
| `listing` | method | KRX 전체 상장법인 목록 (KIND 기준). |
| `liveFilings` | method | OpenDART 기준 실시간 공시 목록 조회. |
| `market` | property | 시장 코드 (DART 제공자는 항상 KR). |
| `network` | method | 관계 네트워크 (지분출자 + 그룹 계열사 지도). |
| `news` | method | 최근 뉴스 수집. |
| `notes` | property | K-IFRS 주석사항 접근자. |
| `priority` | method | 낮을수록 먼저 시도. DART=10 (기본 provider). |
| `profile` | property | docs spine + finance/report merge layer -- 통합 프로필 접근자. |
| `rank` | property | 전체 시장 + 섹터 내 규모 순위 (매출/자산/성장률). |
| `ratioSeries` | property | 재무비율 연도별 시계열 (IS/BS/CF와 동일한 dict 구조). |
| `ratios` | property | 재무비율 시계열 (분류/항목 × 기간 DataFrame). |
| `rawDocs` | property | 공시 문서 원본 parquet 전체 (가공 전). |
| `rawFinance` | property | 재무제표 원본 parquet 전체 (가공 전). |
| `rawReport` | property | 정기보고서 원본 parquet 전체 (가공 전). |
| `readFiling` | method | 접수번호 또는 liveFilings row로 공시 원문을 읽는다. |
| `research` | method | 종합 기업분석 리포트 (재무 + 시장 + 공시 통합). |
| `resolve` | method | 종목코드 또는 회사명 → 종목코드 변환. |
| `retrievalBlocks` | property | 원문 markdown 보존 retrieval block DataFrame. |
| `review` | method | 재무제표 구조화 보고서 — 14개 섹션 데이터 검토서. |
| `reviewer` | method | AI 분석 보고서 — review() + 섹션별 AI 종합의견. |
| `sce` | property | 자본변동표 DataFrame (연결 기준). |
| `sceMatrix` | property | 자본변동표 연도별 매트릭스 (연결 기준). |
| `search` | method | 회사명 부분 검색 (KIND 목록 기준). |
| `sections` | property | sections — docs + finance + report 통합 지도. |
| `sector` | property | WICS 투자 섹터 분류 (KIND 업종 + 키워드 기반). |
| `sectorParams` | property | 현재 종목의 섹터별 밸류에이션 파라미터. |
| `select` | method | show() 결과에서 행(indList) + 열(colList) 필터. |
| `show` | method | topic의 데이터를 반환. |
| `simulation` | method | 경제 시나리오 시뮬레이션 (거시경제 충격 → 재무 영향). |
| `sources` | property | docs/finance/report 3개 source의 가용 현황 요약. |
| `status` | method | 로컬에 보유한 전체 종목 인덱스. |
| `table` | method | subtopic wide 셀의 markdown table을 구조화 DataFrame으로 파싱. |
| `timeseries` | property | 분기별 standalone 시계열 (연결 기준). |
| `topics` | property | topic별 요약 DataFrame -- 전체 데이터 지도. |
| `trace` | method | topic 데이터의 출처(docs/finance/report)와 선택 근거 추적. |
| `update` | method | 누락된 최신 공시를 증분 수집. |
| `valuation` | method | 종합 밸류에이션 (DCF + DDM + 상대가치). |
| `view` | method | 브라우저에서 공시 뷰어를 엽니다. |
| `watch` | method | 공시 변화 감지 — 중요도 스코어링 기반 변화 요약. |
| `workforce` | method | 인력/급여 분석 (직원수, 평균급여, 근속연수). |

### Company 메서드 상세

#### Company.BS
**Capabilities:** XBRL 정규화 재무상태표 (finance 우선)
docs 서술형 fallback
최대 10년 분기별 시계열
**Requires:** 데이터: finance 또는 docs (자동 다운로드)
**AIContext:** ask()/chat()에서 자산/부채/자본 구조 분석 컨텍스트

#### Company.CF
**Capabilities:** XBRL 정규화 현금흐름표 (finance 우선)
docs 서술형 fallback
영업/투자/재무 활동 분류
**Requires:** 데이터: finance 또는 docs (자동 다운로드)
**AIContext:** ask()/chat()에서 현금창출력/투자/재무활동 분석 컨텍스트

#### Company.CIS
**Capabilities:** XBRL 정규화 포괄손익계산서 (finance 우선)
docs 서술형 fallback
기타포괄손익 항목 포함
**Requires:** 데이터: finance 또는 docs (자동 다운로드)
**AIContext:** ask()/chat()에서 기타포괄손익/총포괄이익 분석 컨텍스트

#### Company.IS
**Capabilities:** XBRL 정규화 손익계산서 (finance 우선)
docs 서술형 fallback
최대 10년 분기별 시계열
**Requires:** 데이터: finance 또는 docs (자동 다운로드)
**AIContext:** ask()/chat()에서 수익성/매출 구조 분석 컨텍스트

#### Company.SCE
**Capabilities:** XBRL 정규화 자본변동표
연결 기준 자본 구성요소별 변동
연도별 시계열
**Requires:** 데이터: finance (자동 다운로드)
**AIContext:** ask()/chat()에서 자본 구조 변동 분석 컨텍스트

#### Company.analysis
**Capabilities:** 14축 분석: 수익구조, 자금조달, 자산구조, 현금흐름, 수익성, 성장성, 안정성, 효율성, 종합평가, 이익품질, 비용구조, 자본배분, 투자효율, 재무정합성
축 없이 호출 시 14축 가이드 반환
개별 축 분석 시 Company 바인딩 (self 자동 전달)
**Requires:** 데이터: finance (자동 다운로드)
**AIContext:** ask()/chat()에서 분석 결과를 컨텍스트로 주입
review/reviewer가 내부적으로 analysis 결과를 소비

#### Company.annual
**Capabilities:** BS/IS/CF 계정별 연도 시계열
분기 데이터를 연도 단위로 집계
finance XBRL 정규화 기반
**Requires:** 데이터: finance (자동 다운로드)

#### Company.ask
**Capabilities:** 엔진 계산 결과를 컨텍스트로 조립하여 LLM에 전달
질문 분류 기반 분석 패키지 자동 선택 (financial, valuation, risk 등)
멀티 provider 지원 (openai, ollama, codex 등)
스트리밍 응답 지원
**Requires:** API 키: LLM provider API 키 (OPENAI_API_KEY 등)
**AIContext:** Tier 1 시스템 주도 분석. 질문 분류 후 엔진이 계산한 결과를
컨텍스트로 조립하여 LLM이 해석/설명만 수행.

#### Company.audit
**Capabilities:** 감사의견 추이 (적정/한정/부적정/의견거절)
감사인 변경 이력 + 사유
계속기업 불확실성 플래그
핵심감사사항 (KAM) 추출
내부회계관리제도 검토의견
**Requires:** 데이터: docs + report (자동 다운로드)

#### Company.capital
**Capabilities:** 배당수익률 + 배당성향 추이
자사주 매입/소각 이력
총주주환원율 (배당 + 자사주)
시장 전체 주주환원 횡단 비교
**Requires:** 데이터: DART 정기보고서 (자동 수집)

#### Company.chat
**Capabilities:** Tier 2 LLM 주도 분석 (tool calling)
LLM이 부족한 정보를 자율적으로 도구 호출하여 보충
원본 시계열, 공시 텍스트 검색, 복수 기업 비교 등 심화 탐색
멀티 턴 대화 지원
**Requires:** API 키: tool calling 지원 LLM provider API 키
**AIContext:** Tier 2 에이전트 모드. Tier 1 결과를 본 LLM이 부족하다고 판단하면
저수준 tool(시계열 조회, 공시 검색 등)을 직접 호출하여 심화 분석.

#### Company.contextSlices
**Capabilities:** retrievalBlocks를 LLM 컨텍스트 윈도우에 맞게 슬라이싱
토큰 예산 내에서 최대한 많은 관련 정보를 담는 압축 포맷
topic/period 기준 우선순위 정렬
**Requires:** 데이터: docs (자동 다운로드)
**AIContext:** ask()/chat()의 시스템 프롬프트에 직접 주입되는 데이터
LLM이 소비하는 최종 형태의 컨텍스트

#### Company.cumulative
**Capabilities:** IS/CF 계정별 분기 누적(YTD) 시계열
Q1→Q2→Q3→Q4 누적 합산
finance XBRL 정규화 기반
**Requires:** 데이터: finance (자동 다운로드)

#### Company.debt
**Capabilities:** 총차입금 + 순차입금 규모
부채비율 + 차입금의존도
단기/장기 차입금 비율
시장 전체 부채 구조 횡단 비교
**Requires:** 데이터: DART 정기보고서 (자동 수집)

#### Company.diff
**Capabilities:** 전체 topic 변경 요약 (변경량 스코어링)
특정 topic 기간별 변경 이력
두 기간 줄 단위 diff (추가/삭제/변경)
**Requires:** 데이터: docs (2개 이상 기간 필요)

#### Company.disclosure
**Capabilities:** 전체 공시유형 조회 (정기, 주요사항, 발행, 지분, 외부감사 등)
기간, 유형, 키워드 필터링
최종보고서만 필터 (정정 이전 제외)
**Requires:** API 키: DART_API_KEY

#### Company.eventStudy
**Capabilities:** 공시 발표일 전후 주가 비정상 수익률 산출
이벤트 윈도우 커스텀 가능
공시 유형별 필터링
통계적 유의성 검정
**Requires:** 데이터: docs (자동 다운로드)
추가 패키지: pip install dartlab[event]

#### Company.filings
**Capabilities:** 로컬에 보유한 공시 문서 목록
기간별, 문서유형별 정리
DART 뷰어 링크 포함
**Requires:** 데이터: docs (자동 다운로드)

#### Company.forecast
**Capabilities:** 선형회귀 + CAGR + 이동평균 앙상블
섹터별 성장률 보정
신뢰구간 (상한/하한) 제공
**Requires:** 데이터: finance (자동 다운로드)

#### Company.gather
**Capabilities:** price: OHLCV 주가 시계열 (KR Naver / US Yahoo)
flow: 외국인/기관 수급 동향 (KR 전용)
macro: ECOS(KR) / FRED(US) 거시지표 시계열
news: Google News RSS 뉴스 수집
자동 fallback 체인, circuit breaker, TTL 캐시
**Requires:** price/flow/news: 없음 (공개 API)
macro: API 키 -- ECOS_API_KEY (KR) 또는 FRED_API_KEY (US)
**AIContext:** ask()/chat()에서 주가/수급/거시 데이터를 컨텍스트로 주입
기업 분석 시 시장 데이터 보충 자료로 활용

#### Company.governance
**Capabilities:** 사외이사 비율 + 감사위원회 구성
최대주주 지분율 + 특수관계인
시장 전체 거버넌스 횡단 비교
**Requires:** 데이터: DART 정기보고서 (자동 수집)

#### Company.index
**Capabilities:** docs sections + finance + report 전체를 하나의 목차로 통합
각 항목의 chapter, topic, label, kind, source, periods, shape, preview 제공
sections 메타데이터 + 존재 확인만으로 구성 (파서 미호출, lazy)
viewer/렌더러가 소비하는 메타데이터 원천
**Requires:** 데이터: docs/finance/report 중 하나 이상 (자동 다운로드)
**AIContext:** LLM이 Company 전체 구조를 파악하는 핵심 진입점
ask()에서 어떤 데이터를 참조할지 결정하는 기초 정보

#### Company.insights
**Capabilities:** 7영역 등급 평가 (실적, 수익성, 성장, 안정성, 현금흐름, 효율, 밸류에이션)
이상치 자동 탐지 (급변, 임계 초과)
텍스트 요약 + 투자 프로파일 분류
**Requires:** 데이터: finance (자동 다운로드)

#### Company.keywordTrend
**Capabilities:** 공시 텍스트에서 키워드 빈도 추이 분석
54개 내장 키워드 세트 (AI, ESG, 탄소중립 등)
topic별 x 기간별 빈도 매트릭스
복수 키워드 동시 검색
**Requires:** 데이터: docs (자동 다운로드)

#### Company.listing
**Capabilities:** KOSPI + KOSDAQ 전체 상장법인
종목코드, 종목명, 시장구분, 업종
**Requires:** 데이터: listing (자동 다운로드)

#### Company.liveFilings
**Capabilities:** OpenDART API 실시간 공시 조회
기간, 건수, 키워드 필터링
정규화된 컬럼 (docId, filedAt, title, formType 등)
**Requires:** API 키: DART_API_KEY

#### Company.network
**Capabilities:** 그룹 계열사 목록 (members)
출자/피출자 연결 + 지분율 (edges)
순환출자 경로 탐지 (cycles)
ego 서브그래프 (peers)
인터랙티브 네트워크 시각화 (브라우저)
**Requires:** 데이터: DART 대량보유/임원 공시 (자동 수집)

#### Company.news
**Capabilities:** Google News RSS 기반 뉴스 수집
제목, 날짜, 소스, 링크
기간 조절 가능
**Requires:** 없음 (공개 RSS)

#### Company.notes
**Capabilities:** K-IFRS 재무제표 주석(notes) 데이터 접근
주석 항목별 조회
**Requires:** 데이터: HuggingFace finance parquet (자동 다운로드)

#### Company.profile
**Capabilities:** docs sections를 spine으로, finance/report 데이터를 merge하여 통합 뷰 제공
profile.sections로 source 우선순위(finance > report > docs) 적용된 sections 접근
profile.show(topic)으로 merge된 결과 조회
**Requires:** 데이터: docs (자동 다운로드). finance/report는 있으면 자동 merge.
**AIContext:** c.sections는 내부적으로 profile.sections를 반환
분석/리뷰에서 통합된 데이터를 소비하는 기본 경로

#### Company.rank
**Capabilities:** 전체 시장 내 매출/자산 순위
섹터 내 상대 순위
매출 성장률 기반 규모 분류 (large/mid/small)
**Requires:** 데이터: buildSnapshot() 사전 실행 필요

#### Company.ratioSeries
**Capabilities:** 수익성/안정성/성장성/효율성/밸류에이션 비율
연도별 dict 구조 (timeseries/annual과 동일 형태)
finance XBRL 기반 정확한 비율
**Requires:** 데이터: finance (자동 다운로드)

#### Company.ratios
**Capabilities:** 수익성/안정성/성장성/효율성/밸류에이션 5대 분류
분기별 시계열 비율 자동 계산
finance XBRL 기반 정확한 비율
**Requires:** 데이터: finance (자동 다운로드)

#### Company.rawDocs
**Capabilities:** HuggingFace docs 카테고리 원본 데이터 직접 접근
가공/정규화 이전 상태 그대로 반환
**Requires:** 데이터: HuggingFace docs parquet (자동 다운로드)

#### Company.rawFinance
**Capabilities:** HuggingFace finance 카테고리 원본 데이터 직접 접근
XBRL 정규화 이전 상태 그대로 반환
**Requires:** 데이터: HuggingFace finance parquet (자동 다운로드)

#### Company.rawReport
**Capabilities:** HuggingFace report 카테고리 원본 데이터 직접 접근
정기보고서 API 데이터 가공 이전 상태 반환
**Requires:** 데이터: HuggingFace report parquet (자동 다운로드)

#### Company.readFiling
**Capabilities:** 접수번호(str) 직접 지정 또는 DataFrame row 자동 파싱
전문 텍스트 또는 ZIP 기반 구조화 섹션 반환
텍스트 길이 제한 (truncation) 지원
**Requires:** API 키: DART_API_KEY

#### Company.research
**Capabilities:** 재무 분석 (수익성, 성장, 안정성, 현금흐름)
시장 포지션 + 섹터 비교
공시 기반 정성 분석 (사업모델, 리스크)
섹션별 선택적 생성
**Requires:** 데이터: finance + docs (자동 다운로드)

#### Company.retrievalBlocks
**Capabilities:** docs 원문을 markdown 형태 그대로 보존한 검색용 블록
각 블록은 topic/subtopic/period 단위로 분할
RAG, 벡터 검색, 원문 참조에 최적화된 포맷
**Requires:** 데이터: docs (자동 다운로드)
**AIContext:** ask()/chat()에서 원문 기반 답변 생성 시 소스로 사용
retrieval 기반 컨텍스트 주입의 원천 데이터

#### Company.review
**Capabilities:** 14개 섹션 전체 보고서 (수익구조~재무정합성)
단일 섹션 지정 가능
4개 출력 형식 (rich, html, markdown, json)
섹션간 순환 서사 자동 감지
레이아웃 커스텀
**Requires:** 데이터: finance + report (자동 다운로드)
**AIContext:** reviewer()가 이 결과를 소비하여 AI 해석 생성
ask()에서 재무분석 컨텍스트로 활용

#### Company.reviewer
**Capabilities:** review() 데이터 위에 AI 섹션별 종합의견 추가
도메인 특화 가이드로 분석 관점 지정 가능
각 섹션 시작에 AI 해석 삽입
**Requires:** AI: provider 설정 (dartlab.setup() 참조)
데이터: finance + report (자동 다운로드)
**AIContext:** review() 결과(재무비율, 추세, 동종업계 비교)를 LLM에 제공
LLM이 각 섹션을 해석하여 종합의견 생성
guide 파라미터로 분석 관점 커스텀

#### Company.sceMatrix
**Capabilities:** 원인(cause) × 세부(detail) × 연도 3차원 매트릭스
자본 구성요소별 변동 원인 추적
finance XBRL 정규화 기반
**Requires:** 데이터: finance (자동 다운로드)

#### Company.sections
**Capabilities:** topic × period 수평화 통합 DataFrame
docs/finance/report 3-source 병합
show(topic)/trace(topic)/diff() 의 근간 데이터
**Requires:** 데이터: docs (필수), finance/report (선택, 자동 다운로드)
**AIContext:** 회사 전체 지도 — 모든 분석의 출발점
ask()/chat()에서 topic 탐색 컨텍스트

#### Company.sector
**Capabilities:** WICS 11대 섹터 + 하위 산업그룹 자동 분류
KIND 업종명 + 주요제품 키워드 기반 매칭
override 테이블 우선 → 키워드 → 업종명 순 fallback
**Requires:** 데이터: KIND 상장사 목록 (자동 로드)

#### Company.sectorParams
**Capabilities:** 섹터별 할인율, 성장률, PER 멀티플 제공
섹터 분류 결과에 연동된 파라미터 자동 선택
**Requires:** 데이터: sector 분류 결과 (자동 연산)

#### Company.select
**Capabilities:** show() 결과에서 특정 계정/항목만 추출
기간 필터링 (특정 연도만)
.chart() 체이닝으로 바로 시각화
한글/영문 계정명 모두 지원
**Requires:** 데이터: docs (자동 다운로드)

#### Company.show
**Capabilities:** 120+ topic 접근 (재무제표, 사업내용, 지배구조, 임원현황 등)
기간별 수평화 (topic × period 매트릭스)
블록 단위 drill-down (목차 → 상세)
docs/finance/report 3개 소스 자동 통합
세로 뷰 (period 리스트 전달 시)
**Requires:** 데이터: docs (자동 다운로드). finance topic은 finance 데이터도 필요.

#### Company.simulation
**Capabilities:** 기본 시나리오: 금리인상, 경기침체, 원화약세, 수요급감 등
시나리오별 매출/영업이익/현금흐름 영향 추정
섹터 민감도 반영
**Requires:** 데이터: finance (자동 다운로드)

#### Company.sources
**Capabilities:** 3개 데이터 source(docs, finance, report) 존재 여부/규모 한눈에 확인
각 source의 row/col 수와 shape 문자열 제공
데이터 로드 전 가용성 사전 점검
**Requires:** 없음 (메타데이터만 조회, 데이터 파싱 불필요)

#### Company.status
**Capabilities:** 로컬 데이터 현황 (종목별 docs/finance/report 보유 여부)
최종 업데이트 일시

#### Company.table
**Capabilities:** docs 원문의 markdown table을 Polars DataFrame으로 변환
subtopic 지정으로 특정 표만 추출
numeric 모드로 금액 문자열을 float 변환
period 필터로 특정 기간 컬럼만 선택
**Requires:** 데이터: docs (자동 다운로드)

#### Company.timeseries
**Capabilities:** BS/IS/CF 계정별 분기 standalone 시계열
최대 10년 분기별 데이터
finance XBRL 정규화 기반
**Requires:** 데이터: finance (자동 다운로드)

#### Company.topics
**Capabilities:** docs/finance/report 모든 source의 topic을 하나의 DataFrame으로 통합
chapter 순서대로 정렬, 각 topic의 블록 수/기간 수/최신 기간 표시
어떤 데이터가 있는지 한눈에 파악
**Requires:** 데이터: docs/finance/report 중 하나 이상 (자동 다운로드)
**AIContext:** LLM이 가용 topic 목록을 파악하는 데 사용
분석 범위 결정 시 참조

#### Company.trace
**Capabilities:** topic별 데이터 출처 확인 (docs, finance, report)
출처 선택 이유 (우선순위, fallback 경로)
각 출처별 데이터 행 수, 기간 수, 커버리지
**Requires:** 데이터: docs + finance + report (보유한 것만 추적)

#### Company.update
**Capabilities:** DART API로 최신 공시 확인 후 누락분만 수집
카테고리별 선택 수집
**Requires:** API 키: DART_API_KEY

#### Company.valuation
**Capabilities:** DCF (현금흐름 할인) 모델
DDM (배당 할인) 모델
상대가치 (PER/PBR/EV-EBITDA) 비교
모델별 적정가 + 종합 가중 평균
**Requires:** 데이터: finance (자동 다운로드)

#### Company.view
**Capabilities:** 로컬 서버 기반 공시 뷰어 실행
브라우저에서 sections/index 탐색
**Requires:** 데이터: HuggingFace docs parquet (자동 다운로드)

#### Company.watch
**Capabilities:** 전체 topic 변화 중요도 스코어링
텍스트 변화량 + 재무 영향 통합 평가
특정 topic 상세 변화 내역
**Requires:** 데이터: docs (자동 다운로드)

#### Company.workforce
**Capabilities:** 직원수 + 정규직/비정규직 비율
평균 급여 + 1인당 매출
평균 근속연수
시장 전체 인력 횡단 비교
**Requires:** 데이터: DART 정기보고서 (자동 수집)

---

## 주요 데이터 타입

### RatioResult

비율 계산 결과 (최신 단일 시점).

| 필드 | 타입 | 기본값 |
|------|------|--------|
| `revenueTTM` | `float | None` | None |
| `operatingIncomeTTM` | `float | None` | None |
| `netIncomeTTM` | `float | None` | None |
| `operatingCashflowTTM` | `float | None` | None |
| `investingCashflowTTM` | `float | None` | None |
| `totalAssets` | `float | None` | None |
| `totalEquity` | `float | None` | None |
| `ownersEquity` | `float | None` | None |
| `totalLiabilities` | `float | None` | None |
| `currentAssets` | `float | None` | None |
| `currentLiabilities` | `float | None` | None |
| `cash` | `float | None` | None |
| `shortTermBorrowings` | `float | None` | None |
| `longTermBorrowings` | `float | None` | None |
| `bonds` | `float | None` | None |
| `grossProfit` | `float | None` | None |
| `costOfSales` | `float | None` | None |
| `sga` | `float | None` | None |
| `inventories` | `float | None` | None |
| `receivables` | `float | None` | None |
| `payables` | `float | None` | None |
| `tangibleAssets` | `float | None` | None |
| `intangibleAssets` | `float | None` | None |
| `retainedEarnings` | `float | None` | None |
| `profitBeforeTax` | `float | None` | None |
| `incomeTaxExpense` | `float | None` | None |
| `financeIncome` | `float | None` | None |
| `financeCosts` | `float | None` | None |
| `capex` | `float | None` | None |
| `dividendsPaid` | `float | None` | None |
| `depreciationExpense` | `float | None` | None |
| `noncurrentAssets` | `float | None` | None |
| `noncurrentLiabilities` | `float | None` | None |
| `roe` | `float | None` | None |
| `roa` | `float | None` | None |
| `roce` | `float | None` | None |
| `operatingMargin` | `float | None` | None |
| `netMargin` | `float | None` | None |
| `preTaxMargin` | `float | None` | None |
| `grossMargin` | `float | None` | None |
| `ebitdaMargin` | `float | None` | None |
| `costOfSalesRatio` | `float | None` | None |
| `sgaRatio` | `float | None` | None |
| `effectiveTaxRate` | `float | None` | None |
| `incomeQualityRatio` | `float | None` | None |
| `debtRatio` | `float | None` | None |
| `currentRatio` | `float | None` | None |
| `quickRatio` | `float | None` | None |
| `cashRatio` | `float | None` | None |
| `equityRatio` | `float | None` | None |
| `interestCoverage` | `float | None` | None |
| `netDebt` | `float | None` | None |
| `netDebtRatio` | `float | None` | None |
| `noncurrentRatio` | `float | None` | None |
| `workingCapital` | `float | None` | None |
| `revenueGrowth` | `float | None` | None |
| `operatingProfitGrowth` | `float | None` | None |
| `netProfitGrowth` | `float | None` | None |
| `assetGrowth` | `float | None` | None |
| `equityGrowthRate` | `float | None` | None |
| `revenueGrowth3Y` | `float | None` | None |
| `totalAssetTurnover` | `float | None` | None |
| `fixedAssetTurnover` | `float | None` | None |
| `inventoryTurnover` | `float | None` | None |
| `receivablesTurnover` | `float | None` | None |
| `payablesTurnover` | `float | None` | None |
| `operatingCycle` | `float | None` | None |
| `fcf` | `float | None` | None |
| `operatingCfMargin` | `float | None` | None |
| `operatingCfToNetIncome` | `float | None` | None |
| `operatingCfToCurrentLiab` | `float | None` | None |
| `capexRatio` | `float | None` | None |
| `dividendPayoutRatio` | `float | None` | None |
| `fcfToOcfRatio` | `float | None` | None |
| `roic` | `float | None` | None |
| `dupontMargin` | `float | None` | None |
| `dupontTurnover` | `float | None` | None |
| `dupontLeverage` | `float | None` | None |
| `debtToEbitda` | `float | None` | None |
| `ccc` | `float | None` | None |
| `dso` | `float | None` | None |
| `dio` | `float | None` | None |
| `dpo` | `float | None` | None |
| `piotroskiFScore` | `int | None` | None |
| `piotroskiMaxScore` | `int` | 9 |
| `altmanZScore` | `float | None` | None |
| `beneishMScore` | `float | None` | None |
| `sloanAccrualRatio` | `float | None` | None |
| `ohlsonOScore` | `float | None` | None |
| `ohlsonProbability` | `float | None` | None |
| `altmanZppScore` | `float | None` | None |
| `springateSScore` | `float | None` | None |
| `zmijewskiXScore` | `float | None` | None |
| `eps` | `float | None` | None |
| `bps` | `float | None` | None |
| `dps` | `float | None` | None |
| `per` | `float | None` | None |
| `pbr` | `float | None` | None |
| `psr` | `float | None` | None |
| `evEbitda` | `float | None` | None |
| `marketCap` | `float | None` | None |
| `sharesOutstanding` | `int | None` | None |
| `ebitdaEstimated` | `bool` | True |
| `currency` | `str` | KRW |
| `warnings` | `list` | [] |

### InsightResult

단일 영역 분석 결과.

| 필드 | 타입 | 기본값 |
|------|------|--------|
| `grade` | `str` |  |
| `summary` | `str` |  |
| `details` | `list` | [] |
| `risks` | `list` | [] |
| `opportunities` | `list` | [] |

### Anomaly

이상치 탐지 결과.

| 필드 | 타입 | 기본값 |
|------|------|--------|
| `severity` | `str` |  |
| `category` | `str` |  |
| `text` | `str` |  |
| `value` | `Optional` | None |

### Flag

리스크/기회 플래그.

| 필드 | 타입 | 기본값 |
|------|------|--------|
| `level` | `str` |  |
| `category` | `str` |  |
| `text` | `str` |  |

### AnalysisResult

종합 분석 결과.

| 필드 | 타입 | 기본값 |
|------|------|--------|
| `corpName` | `str` |  |
| `stockCode` | `str` |  |
| `isFinancial` | `bool` |  |
| `performance` | `InsightResult` |  |
| `profitability` | `InsightResult` |  |
| `health` | `InsightResult` |  |
| `cashflow` | `InsightResult` |  |
| `governance` | `InsightResult` |  |
| `risk` | `InsightResult` |  |
| `opportunity` | `InsightResult` |  |
| `predictability` | `Optional` | None |
| `uncertainty` | `Optional` | None |
| `coreEarnings` | `Optional` | None |
| `anomalies` | `list` | [] |
| `distress` | `Optional` | None |
| `summary` | `str` |  |
| `profile` | `str` |  |

### SectorInfo

섹터 분류 결과.

| 필드 | 타입 | 기본값 |
|------|------|--------|
| `sector` | `Sector` |  |
| `industryGroup` | `IndustryGroup` |  |
| `confidence` | `float` |  |
| `source` | `str` |  |

### SectorParams

섹터별 밸류에이션 파라미터.

| 필드 | 타입 | 기본값 |
|------|------|--------|
| `discountRate` | `float` |  |
| `growthRate` | `float` |  |
| `perMultiple` | `float` |  |
| `pbrMultiple` | `float` |  |
| `evEbitdaMultiple` | `float` |  |
| `label` | `str` |  |
| `description` | `str` |  |

### RankInfo

단일 종목의 랭크 정보.

| 필드 | 타입 | 기본값 |
|------|------|--------|
| `stockCode` | `str` |  |
| `corpName` | `str` |  |
| `sector` | `str` |  |
| `industryGroup` | `str` |  |
| `revenue` | `Optional` | None |
| `totalAssets` | `Optional` | None |
| `revenueGrowth3Y` | `Optional` | None |
| `revenueRank` | `Optional` | None |
| `revenueTotal` | `int` | 0 |
| `revenueRankInSector` | `Optional` | None |
| `revenueSectorTotal` | `int` | 0 |
| `assetRank` | `Optional` | None |
| `assetTotal` | `int` | 0 |
| `assetRankInSector` | `Optional` | None |
| `assetSectorTotal` | `int` | 0 |
| `growthRank` | `Optional` | None |
| `growthTotal` | `int` | 0 |
| `growthRankInSector` | `Optional` | None |
| `growthSectorTotal` | `int` | 0 |
| `sizeClass` | `str` |  |
