# dartlab Capabilities

> v0.8.2 기준 자동 생성. 직접 수정 금지.  
> `uv run python scripts/generateSpec.py`로 재생성.


---

## Python API (27개)

`import dartlab` 후 사용 가능한 공개 API.

| 이름 | 종류 | 설명 |
|------|------|------|
| `Company` | function | 종목코드/회사명/ticker → 적절한 Company 인스턴스 생성. |
| `Fred` | class | FRED 경제지표 facade. |
| `OpenDart` | class | OpenDART API 통합 클라이언트. |
| `OpenEdgar` | class | SEC public API facade. |
| `config` | module | dartlab 전역 설정. |
| `ask` | function | LLM에게 기업에 대해 질문. |
| `chat` | function | 에이전트 모드: LLM이 도구를 선택하여 심화 분석. |
| `setup` | function | AI provider 설정 안내 + 인터랙티브 설정. |
| `search` | function | 공시 원문 검색. *(alpha)* |
| `listing` | function | 전체 상장법인 목록. |
| `collect` | function | 지정 종목 DART 데이터 수집 (OpenAPI). |
| `collectAll` | function | 전체 상장종목 DART 데이터 일괄 수집. |
| `downloadAll` | function | HuggingFace에서 전체 시장 데이터 다운로드. |
| `scan` | function | 시장 전체 횡단분석 -- 15축, 전부 Polars DataFrame. |
| `analysis` | function | 재무제표 완전 분석 — 20축, 단일 종목 심층. |
| `gather` | function | 외부 시장 데이터 통합 수집 — 8축, 전부 Polars DataFrame. |
| `credit` | function | 신용등급 산출 단일 진입점. |
| `quant` | function | 기술적 분석 진입점 — scan/gather와 동일한 호출 패턴. |
| `verbose` | module | bool(x) -> bool |
| `dataDir` | module | str(object='') -> str |
| `codeToName` | function | 종목코드 → 회사명. |
| `nameToCode` | function | 회사명 → 종목코드. 정확히 일치하는 첫 번째 결과. |
| `searchName` | function | 종목명/코드로 종목 찾기 (KR + US). |
| `Review` | class | 분석 리뷰 — 14축 전략분석 결과를 구조화 보고서로 렌더링. |
| `SelectResult` | class | select() 반환 객체 — DataFrame 위임 + 체이닝. |
| `ChartResult` | class | chart() 반환 객체 — 시각화 + 렌더링. |
| `capabilities` | function | dartlab 전체 기능 카탈로그 조회. |

### Python API 상세

#### Company
**Capabilities:** 종목코드 ("005930"), 회사명 ("삼성전자"), 영문 ticker ("AAPL") 모두 지원
canHandle() 체인: provider priority 순 자동 라우팅 (DART → EDGAR)
새 국가 추가 시 이 파일 수정 불필요 — provider 패키지만 추가
핵심 인터페이스: show(topic) / index / trace(topic) / diff()
namespace: docs (원문) / finance (숫자) / report (정형공시) / profile (merge)
바로가기: BS/IS/CF/CIS, ratios, ratioSeries, timeseries
메타: sections, topics, filings(), insights, market, currency
**Requires:** DART: 사전 다운로드 데이터 (dartlab.downloadAll() 또는 자동 다운로드).
EDGAR: 인터넷 연결 (On-demand 수집).
**AIContext:** 개별 종목 분석의 시작점. explore/finance/analysis 수퍼툴이 이 객체를 소비.
"삼성전자 분석해줘" → Company("005930") 생성 → briefing → LLM 해석.
**Guide:** "삼성전자 재무제표" -> c = Company("005930"); c.IS
"사업 개요 보여줘" -> c.show("businessOverview")
"어떤 데이터 있어?" -> c.index 또는 c.topics
"출처 추적" -> c.trace("revenue")
"기간 변화" -> c.diff()
"인사이트 등급" -> c.insights
"리뷰 보고서" -> c.review()
"Apple 분석" -> Company("AAPL") (자동 EDGAR 라우팅)
**SeeAlso:** search: 종목 검색 (종목코드 모를 때)
scan: 전종목 횡단분석 (기업 비교)
analysis: 14축 전략분석
gather: 주가/수급/거시 데이터

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
**Guide:** "삼성전자 분석해줘" -> ask("삼성전자 재무건전성 분석해줘")
"이 회사 괜찮아?" -> ask("종목코드", "이 회사 투자해도 괜찮아?")
"AI 설정 어떻게 해?" -> dartlab.setup()으로 provider/키 설정 안내
provider 미설정 시 자동 감지. 설정 방법: dartlab.llm.configure(provider="openai", api_key="sk-...")
보안: API 키는 로컬 .env에만 저장, 외부 전송 절대 없음
**SeeAlso:** chat: 대화형 연속 분석 (멀티턴)
Company: 프로그래밍 방식 데이터 접근
scan: 전종목 비교 (ask보다 직접적)

#### chat
**Capabilities:** LLM이 dartlab 도구를 자율적으로 선택/실행
원본 공시 탐색, 계정 시계열 비교, 섹터 통계 등 심화 분석
최대 N회 도구 호출 반복 (multi-turn)
도구 호출/결과 콜백으로 UI 연동
종목 없이도 동작 (시장 전체 질문, 메타 질문 등)
**Requires:** AI: provider 설정 (tool calling 지원 provider 권장)
**AIContext:** ask()와 동일한 기본 컨텍스트 + 저수준 도구 접근
LLM이 부족하다 판단하면 추가 데이터 자율 수집
company=None이면 scan/gather/system 도구만 활성화
**Guide:** "깊게 분석해줘" -> chat("005930", "배당 추세를 분석하고 이상 징후를 찾아줘")
"시장 전체 거버넌스 비교" -> chat("코스피 거버넌스 좋은 회사 찾아줘")
"dartlab 뭐 할 수 있어?" -> chat("dartlab 기능 알려줘")
ask()보다 심화 분석이 필요할 때 사용. LLM이 자율적으로 도구 호출
**SeeAlso:** ask: 단일 질문 (간단한 분석)
Company: 프로그래밍 방식 직접 접근
scan: 전종목 횡단분석

#### setup
**Capabilities:** 전체 AI provider 설정 현황 테이블 표시
provider별 대화형 설정 (키 입력 → .env 저장)
ChatGPT OAuth 브라우저 로그인
OpenAI/Gemini/Groq/Cerebras/Mistral API 키 설정
Ollama 로컬 LLM 설치 안내
**Requires:** 없음
**AIContext:** AI 분석 기능 사용 전 provider 설정 상태 확인
미설정 provider 감지 시 setup() 안내로 연결
설정 완료 여부를 프로그래밍 방식으로 체크 가능
**Guide:** "AI 설정 어떻게 해?" -> setup()으로 전체 현황 확인
"ChatGPT 연결하고 싶어" -> setup("chatgpt")
"OpenAI 키 등록" -> setup("openai")
"Ollama 어떻게 써?" -> setup("ollama")
**SeeAlso:** ask: AI 질문 (setup 완료 후 사용)
chat: AI 대화 (setup 완료 후 사용)
llm.configure: 프로그래밍 방식 provider 설정

#### search
**Capabilities:** 전체 공시 원문 검색 (수시공시 포함)
자연어 동의어 확장 ("돈을 빌렸다" → 사채/차입/전환사채)
종목/기간 필터 지원
DART 공시 뷰어 링크 포함 (dartUrl 컬럼)
**Requires:** 데이터: allFilings (수집 + buildIndex 필요)
**AIContext:** 공시 내용을 자연어로 찾을 때 사용. 결과의 dartUrl로 원문 확인 가능.
종목 찾기는 Company("삼성전자")를 사용.
**Guide:** "유상증자 한 회사?" -> search("유상증자 결정")
"삼성전자 최근 공시?" -> search("공시", corp="005930")
**SeeAlso:** Company: 종목코드/회사명으로 Company 생성
listing: 전체 상장법인 목록

#### listing
**Capabilities:** KR 전체 상장법인 목록 (KOSPI + KOSDAQ)
종목코드, 종목명, 시장구분, 업종 포함
US listing은 향후 지원 예정
**Requires:** 데이터: listing (자동 다운로드)
**AIContext:** 전종목 대상 필터링/통계에 사용. scan()과 조합하여 시장 전체 분석.
**Guide:** "상장된 회사 몇 개야?" -> listing()으로 전체 목록 조회 후 개수
"코스닥 회사 목록?" -> listing()에서 market 필터
API 키 불필요.
**SeeAlso:** search: 키워드로 특정 종목 검색
scan: 전종목 횡단 비교 분석

#### collect
**Capabilities:** 종목별 DART 공시 데이터 직접 수집 (finance, docs, report)
멀티키 병렬 수집 (DART_API_KEYS 쉼표 구분)
증분 수집 — 이미 있는 데이터는 건너뜀
카테고리별 선택 수집
**Requires:** API 키: DART_API_KEY
**AIContext:** 사용자가 특정 종목의 최신 데이터를 직접 수집할 때 사용.
**Guide:** "데이터 수집해줘" -> DART_API_KEY 필요. dartlab.setup("dart-key", "YOUR_KEY")로 설정 안내
"삼성전자 재무 데이터 수집" -> collect("005930", categories=["finance"])
보안: 키는 로컬 .env에만 저장, 외부 전송 절대 없음
**SeeAlso:** Company: 수집된 데이터로 Company 생성하여 분석
search: 종목코드 모를 때 먼저 검색

#### collectAll
**Capabilities:** 전체 상장종목 DART 공시 데이터 일괄 수집
미수집 종목만 선별 수집 (mode="new") 또는 전체 재수집 (mode="all")
멀티키 병렬 수집 (DART_API_KEYS 쉼표 구분)
카테고리별 선택 (finance, docs, report)
**Requires:** API 키: DART_API_KEY
**Guide:** "전종목 데이터 수집" -> collectAll() 안내. DART_API_KEY 필요
"재무 데이터만 수집" -> collectAll(categories=["finance"])
보안: 키는 로컬 .env에만 저장, 외부 전송 절대 없음
**SeeAlso:** collect: 특정 종목만 수집
downloadAll: HuggingFace 사전구축 데이터 (API 키 불필요, 더 빠름)

#### downloadAll
**Capabilities:** HuggingFace 사전 구축 데이터 일괄 다운로드
finance (~600MB, 2700+종목), docs (~8GB, 2500+종목), report (~320MB, 2700+종목)
이어받기/병렬 다운로드 지원 (huggingface_hub)
전사 분석(scanAccount, governance, digest 등)에 필요한 데이터 사전 준비
**Requires:** 없음 (HuggingFace 공개 데이터셋)
**Guide:** "데이터 어떻게 받아?" -> downloadAll("finance") 안내. API 키 불필요
"scan 쓰려면?" -> downloadAll("finance") + downloadAll("report") 필요
finance 먼저 (600MB), report 다음 (320MB), docs는 대용량 주의 (8GB)
**SeeAlso:** scan: 다운로드된 데이터로 전종목 비교
collect: DART API로 직접 수집 (최신 데이터, API 키 필요)

#### scan
**Capabilities:** governance: 최대주주 지분, 사외이사, 감사위원회 종합 등급
workforce: 임직원 수, 평균급여, 근속연수
capital: 배당수익률, 배당성향, 자사주
debt: 사채만기, 부채비율, ICR, 위험등급
account: 전종목 단일 계정 시계열 (매출액, 영업이익 등)
ratio: 전종목 단일 재무비율 시계열 (ROE, 부채비율 등)
cashflow: OCF/ICF/FCF + 현금흐름 패턴 분류
audit: 감사의견, 감사인변경, 특기사항, 감사독립성
insider: 최대주주 지분변동, 자기주식, 경영권 안정성
quality: Accrual Ratio + CF/NI -- 이익의 현금 뒷받침
liquidity: 유동비율 + 당좌비율 -- 단기 지급능력
growth: 매출/영업이익/순이익 CAGR + 성장 패턴 분류
profitability: 영업이익률/순이익률/ROE/ROA + 등급
digest: 시장 전체 공시 변화 다이제스트
network: 상장사 관계 네트워크 (출자/지분/계열)
**Requires:** 데이터: 축별로 다름 (dartlab.downloadAll() 참조)
governance/workforce/capital/debt/audit/insider: report
account/ratio: finance
network/digest: docs
**AIContext:** 시장 전체 비교/순위 질문에 사용. 개별 종목 분석은 Company 메서드 사용.
**Guide:** "다른 회사랑 비교 가능해?" -> scan("account") 또는 scan("ratio") 안내
"거버넌스 좋은 회사?" -> scan("governance")로 등급 A 필터
"배당 많이 주는 회사?" -> scan("capital")로 배당수익률 정렬
"ROE 높은 회사?" -> scan("ratio", "roe")로 전종목 비교
"삼성전자랑 SK하이닉스 비교" -> scan("account", "sales", code="005930,000660")
API 키 불필요. 사전 다운로드 데이터만으로 동작.
**SeeAlso:** analysis: 개별 종목 14축 전략분석
Company.insights: 단일 종목 7영역 종합 분석
gather: 주가/수급 데이터 (모멘텀 보완)

#### analysis
**Capabilities:** Part 1 — 사업구조: 수익구조, 자금조달, 자산구조, 현금흐름
Part 2 — 핵심비율: 수익성, 성장성, 안정성, 효율성, 종합평가
Part 3 — 심화분석: 이익품질, 비용구조, 자본배분, 투자효율, 재무정합성
Part 4 — 가치평가: DCF, DDM, 상대가치, RIM, 목표주가, 역내재성장률, 민감도
Part 5 — 비재무 심화: 지배구조, 공시변화감지, 비교분석
Part 6 — 전망분석: 매출전망, 예측신호
각 축은 Company를 받아 dict를 반환하는 순수 함수 집합
review()가 이 결과를 소비하여 구조화 보고서 생성
**Requires:** 데이터: finance (자동 다운로드)
**AIContext:** reviewer()가 analysis 결과를 소비하여 AI 해석 생성
ask()에서 재무분석 컨텍스트로 활용
70개 calc* 함수의 개별 결과를 LLM에 주입 가능
**Guide:** "이 회사 수익구조?" -> analysis("financial", "수익구조") — 매출원가율, 판관비율 등
"재무 건전한가?" -> analysis("financial", "안정성") — 부채비율, 유동비율, ICR
"이익이 진짜야?" -> analysis("financial", "이익품질") — 발생주의 비율, OCF/NI
"적정가치?" -> analysis("valuation", "가치평가") — DCF/DDM/상대/RIM/목표가
"전체 종합?" -> analysis("financial", "종합평가") — 15축 통합 스코어
15축 전부 보고 싶으면 review() 사용 권장
**SeeAlso:** review: analysis 결과를 구조화 보고서로 렌더링
scan: 전종목 비교 (analysis는 단일 종목 심층)
Company.insights: 7영역 인사이트 등급 (빠른 요약)

#### gather
**Capabilities:** price: OHLCV 시계열 (KR Naver/US Yahoo, 기본 1년, 최대 6000거래일)
flow: 외국인/기관 수급 동향 (KR 전용, Naver)
macro: ECOS(KR 12개) / FRED(US 25개) 거시지표 시계열
news: Google News RSS 뉴스 수집 (최근 30일)
sector: 업종 분류 (KR KIND+Naver)
insider: 내부자 거래 (KR DART)
ownership: 기관/외국인 지분 보유 (KR Naver)
peers: 동종업종 피어 종목 (시총 포함, KR Naver)
자동 fallback 체인, circuit breaker, TTL 캐시
**Requires:** price/flow/news: 없음 (공개 API)
macro: API 키 — ECOS_API_KEY (KR) 또는 FRED_API_KEY (US)
**AIContext:** ask()/chat()에서 주가/수급/거시 데이터를 컨텍스트로 주입 가능
기업 분석 시 시장 데이터 보충 자료로 활용
**Guide:** "주가 추이 보여줘" -> gather("price", "005930")
"외국인 매매 동향" -> gather("flow", "005930")
"금리 추이 알려줘" -> gather("macro", "BASE_RATE") 또는 gather("macro", "FEDFUNDS")
"최근 뉴스 찾아줘" -> gather("news", "삼성전자")
"업종 알려줘" -> gather("sector", "005930")
"내부자 거래 보여줘" -> gather("insider", "005930")
"지분 보유 현황" -> gather("ownership", "005930")
"동종업종 비교" -> gather("peers", "005930")
"미국 거시지표 전체" -> gather("macro", market="US") 또는 gather("US")
주가+수급은 scan과 다름. scan은 재무 기반 횡단, gather는 시장 실시간.
**SeeAlso:** scan: 재무 기반 전종목 횡단분석 (거버넌스, 현금흐름 등)
Company: 개별 종목 공시/재무 데이터
analysis: 14축 전략분석 (재무비율, 수익구조 등)

#### Review
**Capabilities:** buildReview(company): 템플릿 기반 전체 리뷰 자동 생성 (2부 14축)
Review([blocks...]): 블록 자유 조립 (맞춤 보고서)
Review(stockCode=..., sections=[...]): 직접 구성
render(fmt): rich/html/markdown/json 4종 렌더링
toHtml(), toMarkdown(), toJson() 편의 메서드
Jupyter/Colab/Marimo 자동 HTML 렌더링 (_repr_html_)
**Requires:** Company 객체 (buildReview 사용 시) 또는 Block 리스트.
**AIContext:** review 수퍼툴이 이 클래스의 기능을 AI에게 노출.
blocks action으로 블록 카탈로그, section으로 섹션별 리뷰.
**Guide:** "분석 보고서 보여줘" -> c.review() 또는 buildReview(company)
"수익구조만 보고 싶어" -> c.review("수익구조")
"HTML로 내보내기" -> review.toHtml()
"블록 목록 보여줘" -> blocks(company) (카탈로그 테이블)
"매출 성장률 블록만" -> b = blocks(c); b["growth"]
**SeeAlso:** analysis: 14축 전략분석 엔진 (Review의 데이터 공급원)
blocks: 블록 사전 (한글/영문/tab-complete)
Company.review: Company에서 바로 호출

#### capabilities
**Capabilities:** CAPABILITIES dict에서 부분 조회 가능.
key 없이 호출 시 전체 키 목록(summary 포함) 반환.
key 지정 시 해당 항목의 상세(guide, capabilities, seeAlso 등) 반환.
search 지정 시 자연어 질문 기반 관련 API 검색 (상위 10개).
**Requires:** 없음
**AIContext:** AI가 "dartlab에 뭐가 있는지" 모를 때 탐색용.
capabilities() → 목차 확인 → capabilities("analysis") → 상세 확인 → execute_code.
capabilities(search="재무건전성") → 질문 관련 API 검색 → 코드 생성.
**Guide:** "dartlab 뭐 할 수 있어?" -> capabilities()
"분석 기능 뭐 있어?" -> capabilities("analysis")
"scan 어떻게 써?" -> capabilities("scan")
"재무건전성 관련 API?" -> capabilities(search="재무건전성")
**SeeAlso:** ask: AI 질문 (capabilities로 기능 파악 후 ask로 분석)
setup: AI provider 설정 (capabilities 확인 후 설정)

---

## CLI (19개 명령)

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
| `update` | 로컬 데이터를 HuggingFace 최신으로 갱신 |
| `ai` | AI 분석 웹 인터페이스 실행 |
| `share` | 터널로 로컬 서버 외부 공유 |
| `status` | LLM 연결 상태 확인 |
| `setup` | LLM provider/API 키 설정 |
| `mcp` | MCP 서버 실행 (stdio) |
| `plugin` | 플러그인 관리 (list/create) |

---

## Server API (73개 엔드포인트)

FastAPI `/api/*` 엔드포인트. 모든 클라이언트의 단일 소비 경로.

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/status` | LLM provider 상태 확인 (설치/인증/모델 포함). |
| GET | `/api/suggest` | 회사 데이터 상태에 맞는 추천 질문 목록을 반환한다. |
| POST | `/api/provider/validate` | LLM provider 검증. 전역 상태는 변경하지 않는다. |
| POST | `/api/configure` | 구버전 alias. 현재는 provider 검증만 수행한다. |
| GET | `/api/ai/profile` | 공통 AI profile + provider catalog 반환. |
| PUT | `/api/ai/profile` | 공통 AI profile 갱신. |
| POST | `/api/ai/profile/secrets` | provider secret 저장/삭제. |
| POST | `/api/openapi/dart-key/validate` | OpenDART API 키 유효성만 검증한다. |
| PUT | `/api/openapi/dart-key` | 프로젝트 .env에 OpenDART API 키를 저장한다. |
| DELETE | `/api/openapi/dart-key` | 프로젝트 .env의 OpenDART API 키를 제거한다. |
| POST | `/api/channels/{platform}/start` | 외부 채널 어댑터 시작. |
| POST | `/api/channels/{platform}/stop` | 외부 채널 어댑터 정지. |
| GET | `/api/ai/profile/events` | profile 변경 SSE 스트림. |
| GET | `/api/models/{provider}` | Provider별 사용 가능한 모델 목록 — SDK/API 자동 조회, 실패시 fallback. |
| POST | `/api/codex/logout` | Codex CLI에 저장된 계정 인증을 제거한다. |
| GET | `/api/oauth/authorize` | ChatGPT OAuth 인증 시작 — 브라우저 로그인 URL 반환 + 로컬 콜백 서버 시작. |
| GET | `/api/oauth/status` | OAuth 인증 완료 여부 폴링. |
| POST | `/api/oauth/logout` | OAuth 토큰 제거. |
| POST | `/api/ollama/pull` | Ollama 모델 다운로드 (SSE 스트리밍 진행률). |
| GET | `/api/company/{code}/diff` | Company sections 전체 diff 요약. |
| GET | `/api/company/{code}/diff/matrix` | topic × period 변화 매트릭스 + 히트맵 스펙. |
| GET | `/api/company/{code}/diff/{topic}/summary` | 뷰어용 diff 요약 — changeRate + 최신 변경의 added/removed 미리보기. |
| GET | `/api/company/{code}/diff/{topic}` | Company 특정 topic의 두 기간 줄+글자 단위 diff. |
| GET | `/api/company/{code}/bridge/{topic}` | 텍스트-재무 숫자 교차 참조. |
| GET | `/api/company/{code}/topics/graph` | topic간 상호 참조 그래프. |
| GET | `/api/company/{code}/search` | 현재 회사의 sections 전체 텍스트에서 substring 검색. |
| GET | `/api/company/{code}/searchIndex` | MiniSearch 인덱스용 flat document list. |
| GET | `/api/company/{code}/modules` | 기업의 사용 가능한 데이터 모듈 목록. |
| POST | `/api/ask` | LLM 질문 — 종목이 있으면 데이터 기반 분석, 없으면 순수 대화. |
| GET | `/api/search` | 종목 검색 — substring 우선, 결과 없으면 fuzzy(초성/Levenshtein) fallback. |
| GET | `/api/company/{code}` | 종목 기본 정보 + 사용 가능 API surface 목록. |
| GET | `/api/company/{code}/index` | 회사 데이터 구조 인덱스 DataFrame. |
| GET | `/api/company/{code}/sections` | merged topic x period 수평화 테이블. |
| GET | `/api/company/{code}/init` | SPA 초기 로드용 번들 — toc + 첫 topic viewer + diff 요약. |
| GET | `/api/company/{code}/toc` | 목차(TOC) — chapter/topic 트리 구조. |
| GET | `/api/company/{code}/viewer/{topic}` | 단일 topic의 viewer 데이터 — sections 블록 + 텍스트 문서. |
| GET | `/api/company/{code}/viewer2/{topic}` | sections 기반 신구대조 뷰어 — viewer() dict 반환. |
| POST | `/api/company/{code}/viewer/batch` | 여러 topic의 viewer 데이터를 한 번에 반환 — chapter 확장 시 N+1 제거. |
| GET | `/api/company/{code}/show/{topic}/all` | topic의 전 기간 viewer 블록 일괄 반환. |
| POST | `/api/company/{code}/show/{topic}/{block_idx}/parse` | 원문 테이블 블록을 구조화 DataFrame으로 파싱. |
| GET | `/api/company/{code}/show/{topic}` | topic payload 조회 — show(topic) API 대응. |
| GET | `/api/company/{code}/trace/{topic}` | source provenance 조회 — trace(topic) API 대응. |
| GET | `/api/company/{code}/summary/{topic}` | topic 데이터를 LLM으로 요약하여 SSE 스트리밍 반환. |
| GET | `/api/company/{code}/insights` | 7영역 인사이트 등급 (A~F) + 이상 징후. |
| GET | `/api/company/{code}/network` | 관계사 네트워크 그래프 — ego 중심 N-hop. |
| GET | `/api/company/{code}/scan/{axis}` | 6-Axis 스캔 단일 축 결과 + 시장 내 위치. |
| GET | `/api/company/{code}/scan/position` | 6-Axis 전체 포지션 요약 — 사전 빌드 스냅샷 기반. |
| GET | `/api/company/{code}/insights/unified` | 통합 인사이트 — 등급 + 스캔 + 피어 결합. |
| GET | `/api/data/sources/{code}` | 경량 데이터 소스 목록 — registry 메타 + 파일 존재 여부만 확인 (빠름). |
| GET | `/api/data/preview/{code}/{module}` | 데이터 미리보기 — 모듈 데이터를 JSON으로 반환 (테이블/텍스트). |
| GET | `/api/data/stats` | 로컬 데이터 현황 — 문서/재무 파일 수, dartlab 버전. |
| GET | `/api/spec` | 시스템 스펙 조회 — LLM/MCP/외부 클라이언트용. |
| GET | `/api/export/modules/{code}` | Excel 내보내기 가능한 모듈 목록. |
| GET | `/api/export/sources/{code}` | 데이터 소스 디스커버리 — registry 기반 전체 소스 트리. |
| GET | `/api/export/templates` | 저장된 템플릿 목록 (프리셋 포함). |
| GET | `/api/export/templates/{template_id}` | 단일 템플릿 조회. |
| POST | `/api/export/templates` | 템플릿 저장 (신규 or 업데이트). |
| DELETE | `/api/export/templates/{template_id}` | 템플릿 삭제. |
| GET | `/api/export/excel/{code}` | Excel 파일 내보내기 — .xlsx 다운로드. |
| GET | `/api/fred/series/{series_id}` | FRED 시계열 조회 + 변환. |
| GET | `/api/fred/search` | FRED 시리즈 검색. |
| GET | `/api/fred/compare` | 복수 시계열 비교. |
| GET | `/api/fred/catalog` | 주요 경제지표 카탈로그. |
| GET | `/api/fred/correlation` | 시계열 상관분석 + 선행/후행. |
| POST | `/api/room/join` | 룸 참여 — member_id + 현재 상태 반환. |
| POST | `/api/room/leave` | 룸 퇴장. |
| POST | `/api/room/heartbeat` | 프레즌스 유지. |
| GET | `/api/room/state` | 현재 룸 상태. |
| GET | `/api/room/stream` | SSE 스트림 — 브로드캐스트 수신. |
| POST | `/api/room/ask` | 질문 → 전체 브로드캐스트. |
| POST | `/api/room/navigate` | 네비게이션 동기화. |
| POST | `/api/room/chat` | 채팅 메시지. |
| POST | `/api/room/react` | 이모지 반응. |

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

## AI Tools (0개)

LLM 에이전트가 tool calling으로 사용하는 도구. priority 내림차순.

---

## Scan Axis (20개 축)

`dartlab.scan(axis, target)` 형태로 전종목 횡단분석.

| 축 | 한글 | 설명 | target 파라미터 | 필수 | 반환타입 |
|----|------|------|----------------|------|---------|
| `governance` | 거버넌스 | 지배구조 (지분율, 사외이사, 보수비율, 감사의견, 소액주주 분산) | stockCode 필터 | - | DataFrame |
| `workforce` | 인력/급여 | 직원수, 평균급여, 인건비율, 1인당부가가치, 성장률, 고액보수 | stockCode 필터 | - | DataFrame |
| `capital` | 주주환원 | 배당, 자사주(취득/처분/소각), 증자/감자, 환원 분류 | stockCode 필터 | - | DataFrame |
| `debt` | 부채구조 | 사채만기, 부채비율, ICR, 위험등급 | stockCode 필터 | - | DataFrame |
| `account` | 계정 | 전종목 단일 계정 시계열 (매출액, 영업이익 등) | snakeId | O | DataFrame |
| `ratio` | 비율 | 전종목 단일 재무비율 시계열 (ROE, 부채비율 등) | ratioName | O | DataFrame |
| `network` | 네트워크 | 상장사 관계 네트워크 (출자/지분/계열) | stockCode 필터 | - | dict |
| `cashflow` | 현금흐름 | OCF/ICF/FCF + 현금흐름 패턴 분류 (8종) | stockCode 필터 | - | DataFrame |
| `audit` | 감사리스크 | 감사의견, 감사인변경, 특기사항, 감사독립성비율 | stockCode 필터 | - | DataFrame |
| `insider` | 내부자지분 | 최대주주 지분변동, 자기주식 현황, 경영권 안정성 | stockCode 필터 | - | DataFrame |
| `quality` | 이익의 질 | Accrual Ratio + CF/NI 비율 — 이익이 현금 뒷받침되는지 | stockCode 필터 | - | DataFrame |
| `liquidity` | 유동성 | 유동비율 + 당좌비율 — 단기 지급능력 | stockCode 필터 | - | DataFrame |
| `growth` | 성장성 | 매출/영업이익/순이익 CAGR + 성장 패턴 분류 (6종) | stockCode 필터 | - | DataFrame |
| `profitability` | 수익성 | 영업이익률/순이익률/ROE/ROA + 등급 | stockCode 필터 | - | DataFrame |
| `efficiency` | 효율성 | 자산/재고/매출채권 회전율 + CCC(현금전환주기) + 등급 | stockCode 필터 | - | DataFrame |
| `valuation` | 밸류에이션 | PER/PBR/PSR + 시가총액 + 등급 (네이버 실시간) | stockCode 필터 | - | DataFrame |
| `dividendTrend` | 배당추이 | DPS 3개년 시계열 + 패턴 분류 (연속증가/안정/감소/시작/중단) | stockCode 필터 | - | DataFrame |
| `macroBeta` | 거시베타 | 전종목 GDP/금리/환율 베타 횡단면 (OLS 회귀). 사전 수집: Ecos().series('GDP', enrich=True) | stockCode 필터 | - | DataFrame |
| `screen` | 스크리닝 | 멀티팩터 스크리닝 (value/dividend/growth/risk/quality 프리셋) | target | - | DataFrame |
| `disclosureRisk` | 공시리스크 | 공시 변화 기반 선행 리스크 (우발부채, 감사변경, 계열변화, 사업전환) | stockCode 필터 | - | DataFrame |

**한글 별칭:**

- `account`: 계정
- `audit`: 감사, 감사리스크
- `capital`: 주주환원, 배당
- `cashflow`: 현금흐름, 현금
- `debt`: 부채, 부채구조, 사채
- `disclosureRisk`: 공시리스크, 공시변화
- `dividendTrend`: 배당추이, 배당시계열, 배당트렌드
- `efficiency`: 효율성, 회전율
- `governance`: 거버넌스, 지배구조
- `growth`: 성장성, 성장
- `insider`: 내부자, 내부자지분, 지분
- `liquidity`: 유동성, 유동비율
- `macroBeta`: 거시베타, 매크로베타, 거시민감도
- `network`: 네트워크, 관계
- `profitability`: 수익성
- `quality`: 이익의질, 이익의 질, 이익품질, 어닝퀄리티
- `ratio`: 비율
- `screen`: 스크리닝, 스크린, 필터
- `valuation`: 밸류에이션, 밸류
- `workforce`: 인력, 급여, 인력/급여

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

## Gather Axis (8개 축)

`dartlab.gather(axis, target)` 형태로 외부 시장 데이터 수집.

| 축 | 한글 | 설명 | target 필수 |
|----|------|------|------------|
| `price` | 주가 | OHLCV 시계열 (기본 1년) — Naver/Yahoo/FMP fallback | O |
| `flow` | 수급 | 외국인/기관 매매 동향 (KR 전용) | O |
| `macro` | 거시지표 | ECOS(KR 12개) / FRED(US 25개) 거시 시계열 | - |
| `news` | 뉴스 | Google News RSS — 최근 30일 | O |
| `sector` | 업종 | 업종 분류 — KR(KIND+Naver) / US(Yahoo) | O |
| `insider` | 내부자거래 | 임원/주요주주 주식 거래 — KR(DART) / US(Yahoo) | O |
| `ownership` | 지분 | 기관/외국인 보유 현황 | O |
| `peers` | 피어 | 같은 업종 내 피어 종목 목록 (시총 포함) | O |

**한글 별칭:**

- `flow`: 수급
- `insider`: 내부자
- `macro`: 거시, 매크로
- `news`: 뉴스
- `ownership`: 지분
- `peers`: 피어, 동종업종
- `price`: 주가
- `sector`: 업종

**사용법:**

```python
import dartlab

dartlab.gather("price", "005930")   # 삼성전자 주가
dartlab.gather("flow", "005930")     # 수급 동향
dartlab.gather("macro")              # KR 거시지표 전체
dartlab.gather("news", "삼성전자")    # 뉴스
```

---


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

DartCompany에서 동적 추출 (65개).

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
| `credit` | method | 독립 신용평가 — dCR 20단계 등급. |
| `cumulative` | property | 분기별 누적 시계열 (연결 기준). |
| `currency` | property | 통화 코드 (DART 제공자는 항상 KRW). |
| `debt` | method | 부채 구조 분석 (차입금, 부채비율, 만기 구조). |
| `diff` | method | 기간간 텍스트 변경 비교. |
| `disclosure` | method | OpenDART 전체 공시 목록 조회. |
| `filings` | method | 공시 문서 목록 + DART 뷰어 링크. |
| `gather` | method | 외부 시장 데이터 수집 — 4축 (price/flow/macro/news). |
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
| `quant` | method | 기술적 분석 (25개 지표 + 종합 판단). |
| `rank` | property | 전체 시장 + 섹터 내 규모 순위 (매출/자산/성장률). |
| `ratioSeries` | property | 재무비율 연도별 시계열 (IS/BS/CF와 동일한 dict 구조). |
| `ratios` | property | 재무비율 시계열 (분류/항목 x 기간 DataFrame). |
| `rawDocs` | property | 공시 문서 원본 parquet 전체 (가공 전). |
| `rawFinance` | property | 재무제표 원본 parquet 전체 (가공 전). |
| `rawReport` | property | 정기보고서 원본 parquet 전체 (가공 전). |
| `readFiling` | method | 접수번호 또는 liveFilings row로 공시 원문을 읽는다. |
| `resolve` | method | 종목코드 또는 회사명 → 종목코드 변환. |
| `retrievalBlocks` | property | 원문 markdown 보존 retrieval block DataFrame. |
| `review` | method | 재무제표 구조화 보고서 — 14개 섹션 데이터 검토서. |
| `reviewer` | method | AI 분석 보고서 — review() + 섹션별 AI 종합의견. |
| `sceMatrix` | property | 자본변동표 연도별 매트릭스 (연결 기준). |
| `search` | method | 회사명 부분 검색 (KIND 목록 기준). |
| `sections` | property | sections — docs + finance + report 통합 지도. |
| `sector` | property | WICS 투자 섹터 분류 (KIND 업종 + 키워드 기반). |
| `sectorParams` | property | 현재 종목의 섹터별 밸류에이션 파라미터. |
| `select` | method | show() 결과에서 행(indList) + 열(colList) 필터. |
| `show` | method | topic의 데이터를 반환. |
| `sources` | property | docs/finance/report 3개 source의 가용 현황 요약. |
| `status` | method | 로컬에 보유한 전체 종목 인덱스. |
| `table` | method | subtopic wide 셀의 markdown table을 구조화 DataFrame으로 파싱. |
| `timeseries` | property | 분기별 standalone 시계열 (연결 기준). |
| `topicSummaries` | method | 토픽별 요약 dict — AI가 경로 탐색에 사용. |
| `topics` | property | topic별 요약 DataFrame -- 전체 데이터 지도. |
| `trace` | method | topic 데이터의 출처(docs/finance/report)와 선택 근거 추적. |
| `update` | method | 누락된 최신 공시를 증분 수집. |
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
**Guide:** "재무상태표 보여줘" → c.BS
"자산/부채 구조" → c.BS로 확인
"유동비율은?" → c.ratios 또는 c.BS에서 계산
**SeeAlso:** IS: 손익계산서 (수익성 분석)
CF: 현금흐름표 (현금창출력)
ratios: 재무비율 (BS 기반 안정성 비율 포함)
select: 특정 계정만 추출 + 시각화

#### Company.CF
**Capabilities:** XBRL 정규화 현금흐름표 (finance 우선)
docs 서술형 fallback
영업/투자/재무 활동 분류
**Requires:** 데이터: finance 또는 docs (자동 다운로드)
**AIContext:** ask()/chat()에서 현금창출력/투자/재무활동 분석 컨텍스트
**Guide:** "현금흐름표 보여줘" → c.CF
"영업현금흐름 추이" → c.select("CF", ["영업활동으로인한현금흐름"])
"FCF 확인" → c.ratios에서 FCF 비율 또는 c.CF에서 직접 계산
**SeeAlso:** IS: 손익계산서 (발생주의 vs 현금주의 비교)
BS: 재무상태표 (현금성자산 확인)
ratios: 재무비율 (현금흐름 관련 비율 포함)

#### Company.CIS
**Capabilities:** XBRL 정규화 포괄손익계산서 (finance 우선)
docs 서술형 fallback
기타포괄손익 항목 포함
**Requires:** 데이터: finance 또는 docs (자동 다운로드)
**AIContext:** ask()/chat()에서 기타포괄손익/총포괄이익 분석 컨텍스트
**Guide:** "포괄손익계산서 보여줘" → c.CIS
"기타포괄손익 항목은?" → c.CIS
**SeeAlso:** IS: 일반 손익계산서 (당기순이익까지)
SCE: 자본변동표 (포괄손익이 자본에 미치는 영향)

#### Company.IS
**Capabilities:** XBRL 정규화 손익계산서 (finance 우선)
docs 서술형 fallback
최대 10년 분기별 시계열
**Requires:** 데이터: finance 또는 docs (자동 다운로드)
**AIContext:** ask()/chat()에서 수익성/매출 구조 분석 컨텍스트
**Guide:** "손익계산서 보여줘" → c.IS
"매출/영업이익 추이" → c.IS 또는 c.select("IS", ["매출액", "영업이익"])
"수익 구조 분석" → c.IS + c.analysis("financial", "수익구조")
**SeeAlso:** BS: 재무상태표 (자산/부채 구조)
CF: 현금흐름표 (실제 현금 기반)
CIS: 포괄손익계산서 (기타포괄손익 포함)
select: 특정 계정 추출 + 시각화

#### Company.SCE
**Capabilities:** XBRL 정규화 자본변동표
연결 기준 자본 구성요소별 변동
연도별 시계열
**Requires:** 데이터: finance (자동 다운로드)
**AIContext:** ask()/chat()에서 자본 구조 변동 분석 컨텍스트
**Guide:** "자본변동표 보여줘" → c.SCE
"자본 구성 변화" → c.SCE
**SeeAlso:** sceMatrix: 3차원 매트릭스 형태 (원인별 상세 추적)
CIS: 포괄손익계산서 (자본변동의 원천)
BS: 재무상태표 (자본 잔액)

#### Company.analysis
**Capabilities:** 14축 분석: 수익구조, 자금조달, 자산구조, 현금흐름, 수익성, 성장성, 안정성, 효율성, 종합평가, 이익품질, 비용구조, 자본배분, 투자효율, 재무정합성
축 없이 호출 시 14축 가이드 반환
개별 축 분석 시 Company 바인딩 (self 자동 전달)
2-level 호출: c.analysis("financial", "수익성"), c.analysis("valuation", "가치평가")
**Requires:** 데이터: finance (자동 다운로드)
**AIContext:** ask()/chat()에서 분석 결과를 컨텍스트로 주입
review/reviewer가 내부적으로 analysis 결과를 소비
**Guide:** "14축 분석 뭐가 있어?" → c.analysis() (가이드 반환)
"수익구조 분석해줘" → c.analysis("financial", "수익구조")
"안정성 분석" → c.analysis("financial", "안정성")
"가치평가 해줘" → c.analysis("valuation", "가치평가")
"매출전망" → c.analysis("forecast", "매출전망")
**SeeAlso:** review: 14축 분석을 14개 섹션 보고서로 조합
insights: 7영역 등급 요약 (analysis보다 요약적)
ratios: 재무비율 시계열 (analysis의 입력 데이터)

#### Company.annual
**Capabilities:** BS/IS/CF 계정별 연도 시계열
분기 데이터를 연도 단위로 집계
finance XBRL 정규화 기반
**Requires:** 데이터: finance (자동 다운로드)
**AIContext:** 연도 단위 추세 분석 — forecast, ratioSeries의 기초 데이터
**Guide:** "연���별 시계열" → c.annual
"연간 매출 추이" → series, years = c.annual; series["IS"]["sales"]
**SeeAlso:** timeseries: 분기별 시계열 (더 세밀)
cumulative: 분기별 누적 시계열
ratioSeries: 연도별 재무비율 시계열

#### Company.ask
**Capabilities:** 엔진 계산 결과를 컨텍스트로 조립하여 LLM에 전달
질문 분류 기반 분석 패키지 자동 선택 (financial, valuation, risk 등)
멀티 provider 지원 (openai, ollama, codex 등)
스트리밍 응답 지원
**Requires:** API 키: LLM provider API 키 (OPENAI_API_KEY 등)
**AIContext:** AI가 분석 전 과정을 주도. dartlab 엔진(analysis, scan, gather 등)을
도구로 호출하여 데이터 수집, 계산, 판단, 해석을 수행.
**Guide:** "영업이익률 분석해줘" → c.ask("영업이익률 추세는?")
"AI한테 질문하고 싶어" → c.ask("질문")
"스트리밍으로 답변받기" → c.ask("질문", stream=True)
**SeeAlso:** chat: 에이전트 모드 (tool calling 기반 심화 분석)
reviewer: 구조화된 AI 보고서 (자유 질문이 아닌 섹션별)
review: AI 없는 데이터 검토서

#### Company.audit
**Capabilities:** 감사의견 추이 (적정/한정/부적정/의견거절)
감사인 변경 이력 + 사유
계속기업 불확실성 플래그
핵심감사사항 (KAM) 추출
내부회계관리제도 검토의견
**Requires:** 데이터: docs + report (자동 다운로드)
**AIContext:** 감사 리스크 종합 평가 — 투자 의사결정의 핵심 안전장치
감사의견 변경, 계속기업 불확실성은 최고 경고 수준
**Guide:** "감사의견 확인" → c.audit()
"감사인 바뀌었어?" → c.audit()["auditorChanges"]
"계속기업 의문은?" → c.audit()["goingConcern"]
**SeeAlso:** governance: 지배구조 분석 (감사위원회 구성 포함)
insights: 종합 등급 (감사 리스크도 반영)
review: 재무정합성 섹션에서 감사 결과 활용

#### Company.capital
**Capabilities:** 배당수익률 + 배당성향 추이
자사주 매입/소각 이력
총주주환원율 (배당 + 자사주)
시장 전체 주주환원 횡단 비교
**Requires:** 데이터: DART 정기보고서 (자동 수집)
**AIContext:** 주주환원 정책 평가 — 배당수익률/성향/자사주 정량 데이터
시장 횡단 비교로 상대적 환원 수준 판단
**Guide:** "배당 정보" → c.capital() 또는 c.show("dividend")
"주주환원율은?" → c.capital()
"전체 상장사 배당 비교" → c.capital("all")
**SeeAlso:** show: c.show("dividend")로 docs 기반 배당 상세
sceMatrix: 자본변동표 (배당/자사주가 자본에 미치는 영향)
debt: 부채 구조 (자본 정책의 다른 면)

#### Company.chat
**Capabilities:** Tier 2 LLM 주도 분석 (tool calling)
LLM이 부족한 정보를 자율적으로 도구 호출하여 보충
원본 시계열, 공시 텍스트 검색, 복수 기업 비교 등 심화 탐색
멀티 턴 대화 지원
**Requires:** API 키: tool calling 지원 LLM provider API 키
**AIContext:** Tier 2 에이전트 모드. Tier 1 결과를 본 LLM이 부족하다고 판단하면
저수준 tool(시계열 조회, 공시 검색 등)을 직접 호출하여 심화 분석.
**Guide:** "심층 분석해줘" → c.chat("질문")
"AI가 직접 데이터 찾아서 분석" → c.chat("질문")
"여러 단계 분석 필요한 질문" → c.chat("복합 질문")
**SeeAlso:** ask: 단일 턴 질문 (chat보다 빠르지만 덜 심층)
reviewer: 구조화된 AI 보고서

#### Company.contextSlices
**Capabilities:** retrievalBlocks를 LLM 컨텍스트 윈도우에 맞게 슬라이싱
토큰 예산 내에서 최대한 많은 관련 정보를 담는 압축 포맷
topic/period 기준 우선순위 정렬
**Requires:** 데이터: docs (자동 다운로드)
**AIContext:** ask()/chat()의 시스템 프롬프트에 직접 주입되는 데이터
LLM이 소비하는 최종 형태의 컨텍스트
**Guide:** "LLM에 들어가는 컨텍스트" → c.contextSlices
"AI가 보는 데이터" → c.contextSlices
**SeeAlso:** retrievalBlocks: 슬라이싱 전 전체 retrieval 블록
ask: contextSlices를 내부적으로 소비하는 AI 질문 인터페이스

#### Company.cumulative
**Capabilities:** IS/CF 계정별 분기 누적(YTD) 시계열
Q1→Q2→Q3→Q4 누적 합산
finance XBRL 정규화 기반
**Requires:** 데이터: finance (자동 다운로드)
**AIContext:** Q4 누적이 연간 실적 — 연중 진행률 파악에 활용
**Guide:** "누적 시계열" → c.cumulative
"올해 누적 매출" → series, periods = c.cumulative
**SeeAlso:** timeseries: 분기별 standalone (누적이 아닌 개별 분기)
annual: 연도별 집계

#### Company.debt
**Capabilities:** 총차입금 + 순차입금 규모
부채비율 + 차입금의존도
단기/장기 차입금 비율
시장 전체 부채 구조 횡단 비교
**Requires:** 데이터: DART 정기보고서 (자동 수집)
**AIContext:** 부채 구조/건전성 정량 평가 — 차입금 의존도, 만기 구조
시장 횡단 비교로 상대적 재무 안정성 판단
**Guide:** "부채 구조 분석" → c.debt()
"부채비율은?" → c.debt() 또는 c.ratios
"전체 상장사 부채 비교" → c.debt("all")
**SeeAlso:** BS: 재무상태표 (부채 원본 데이터)
ratios: 재무비율 (부채비율 포함)
capital: 주주환원 (자본 정책의 다른 면)

#### Company.diff
**Capabilities:** 전체 topic 변경 요약 (변경량 스코어링)
특정 topic 기간별 변경 이력
두 기간 줄 단위 diff (추가/삭제/변경)
**Requires:** 데이터: docs (2개 이상 기간 필요)
**AIContext:** 기간간 공시 변경 감지 — 사업 방향 전환, 리스크 요인 변화 탐지
watch()보다 세밀한 줄 단위 변경 추적
**Guide:** "공시에서 뭐가 바뀌었어?" → c.diff()
"사업개요 변경 이력" → c.diff("businessOverview")
"2023 vs 2024 차이" → c.diff("businessOverview", "2023", "2024")
**SeeAlso:** watch: 변화 중요도 스코어링 (diff보다 요약적)
keywordTrend: 키워드 ��도 추이 (텍스트 변화의 다른 관점)
show: 특정 기간 원문 조회

#### Company.disclosure
**Capabilities:** 전체 공시유형 조회 (정기, 주요사항, 발행, 지분, 외부감사 등)
기간, 유형, 키워드 필터링
최종보고서만 필터 (정정 이전 제외)
**Requires:** API 키: DART_API_KEY
**AIContext:** 특정 유형 공시 존재 여부 확인 → 분석 범위 동적 결정
최근 공시 빈도/유형 패턴으로 기업 이벤트 감지
**Guide:** "최근 공시 뭐 나왔어?" → c.disclosure(days=30)
"주요사항 공시 있어?" → c.disclosure(type="B")
"사업보고서 언제 나왔어?" → c.disclosure(keyword="사업보고서")
**SeeAlso:** liveFilings: 실시간 최신 공시 (정규화된 포맷)
readFiling: 공시 원문 텍스트 읽기
filings: 로컬 보유 공시 목록

#### Company.filings
**Capabilities:** 로컬에 보유한 공시 문서 목록
기간별, 문서유형별 정리
DART 뷰어 링크 포함
**Requires:** 데이터: docs (자동 다운로드)
**AIContext:** 어떤 공시가 보유돼 있는지 확인하여 분석 범위 결정에 활용
**Guide:** "이 회사 공시 목록 보여줘" → c.filings()
"어떤 보고서가 있어?" → c.filings()로 보유 문서 확인
**SeeAlso:** disclosure: OpenDART API 기반 실시간 공시 목록 (로컬 보유가 아닌 전체)
liveFilings: 최신 공시 실시간 조회
update: 누락 공시 증분 수집

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
**Guide:** "주가 데이터" → c.gather("price")
"외국인/기관 수급" → c.gather("flow")
"거시경제 지표" → c.gather("macro")
"뉴스 수집" → c.gather("news") 또는 c.news()
**SeeAlso:** news: 뉴스 전용 단축 메서드
ask: gather 데이터를 컨텍스트로 활용한 AI 분석

#### Company.governance
**Capabilities:** 사외이사 비율 + 감사위원회 구성
최대주주 지분율 + 특수관계인
시장 전체 거버넌스 횡단 비교
**Requires:** 데이터: DART 정기보고서 (자동 수집)
**AIContext:** 지배구조 리스크 평가 — 사외이사/감사위원/최대주주 정량 데이터
시장 횡단 비교로 상대적 거버넌스 수준 판단
**Guide:** "지배구조 분석" → c.governance()
"사외이사 비율은?" → c.governance()
"전체 상장사 거버넌스 비교" → c.governance("all")
**SeeAlso:** network: 출자/계열사 관계 (거버넌스의 다른 관점)
audit: 감사 리스크 (감사위원회와 연관)

#### Company.index
**Capabilities:** docs sections + finance + report 전체를 하나의 목차로 통합
각 항목의 chapter, topic, label, kind, source, periods, shape, preview 제공
sections 메타데이터 + 존재 확인만으로 구성 (파서 미호출, lazy)
viewer/렌더러가 소비하는 메타데이터 원천
**Requires:** 데이터: docs/finance/report 중 하나 이상 (자동 다운로드)
**AIContext:** LLM이 Company 전체 구조를 파악하는 핵심 진입점
ask()에서 어떤 데이터를 참조할지 결정하는 기초 정보
**Guide:** "전체 목차 보여줘" → c.index
"어떤 데이터가 있는지 구조적으로" → c.index
**SeeAlso:** topics: topic 단위 요약 (index보다 간결)
sections: 전체 sections 지도 (index의 원본)
profile: 통합 프로필 접근자

#### Company.insights
**Capabilities:** 7영역 등급 평가 (실적, 수익성, 성장, 안정성, 현금흐름, 효율, 밸류에이션)
이상치 자동 탐지 (급변, 임계 초과)
텍스트 요약 + 투자 프로파일 분류
**Requires:** 데이터: finance (자동 다운로드)
**AIContext:** ask()/chat()에서 재무 건전성 종합 판단의 핵심 데이터
7영역 등급 + 이상치 + 투자 프로파일을 컨텍스트로 주입
**Guide:** "이 회사 재무 등급은?" → c.insights.grades()
"이상 징후 있어?" → c.insights.anomalies
"투자 프로파일" → c.insights.profile
**SeeAlso:** analysis: 14축 개별 상세 분석 (insights보다 세밀)
review: 14섹션 보고서 (insights를 내부적으로 참조)
ratios: 재무비율 시계열 (insights의 입력 데이터)

#### Company.keywordTrend
**Capabilities:** 공시 텍스트에서 키워드 빈도 추이 분석
54개 내장 키워드 세트 (AI, ESG, 탄소중립 등)
topic별 x 기간별 빈도 매트릭스
복수 키워드 동시 검색
**Requires:** 데이터: docs (자동 다운로드)
**AIContext:** 공시 텍스트의 키워드 빈도 변화로 전략 방향 전환 감지
AI, ESG, 탄소중립 등 트렌드 키워드 모니터링
**Guide:** "AI 언급 추이" → c.keywordTrend("AI")
"ESG 관련 변화" → c.keywordTrend("ESG")
"전체 키워드 트렌드" → c.keywordTrend()
**SeeAlso:** diff: 텍스트 줄 단위 변경 비교 (키워드가 아닌 전체 변경)
watch: 변화 중요도 스코어링

#### Company.listing
**Capabilities:** KOSPI + KOSDAQ 전체 상장법인
종목코드, 종목명, 시장구분, 업종
**Requires:** 데이터: listing (자동 다운로드)

#### Company.liveFilings
**Capabilities:** OpenDART API 실시간 공시 조회
기간, 건수, 키워드 필터링
정규화된 컬럼 (docId, filedAt, title, formType 등)
**Requires:** API 키: DART_API_KEY
**AIContext:** 최신 공시 모니터링으로 기업 이벤트(배당, 유증, 합병 등) 실시간 감지
readFiling()과 조합하여 최신 공시 원문 분석
**Guide:** "최근 공시 확인해줘" → c.liveFilings()
"이번 주 공시 있어?" → c.liveFilings(days=7)
"배당 관련 공시" → c.liveFilings(keyword="배당")
**SeeAlso:** disclosure: 과거 전체 공시 이력 조회
readFiling: 공시 원문 텍스트 읽기
watch: 공시 변화 중요도 스코어링

#### Company.network
**Capabilities:** 그룹 계열사 목록 (members)
출자/피출자 연결 + 지분율 (edges)
순환출자 경로 탐지 (cycles)
ego 서브그래프 (peers)
인터랙티브 네트워크 시각화 (브라우저)
**Requires:** 데이터: DART 대량보유/임원 공시 (자동 수집)
**AIContext:** 그룹 계열사/출자 구조 파악 — 지배구조 분석의 기초 데이터
순환출자 탐지로 거버넌스 리스크 감지
**Guide:** "계열사 관계도" → c.network() 또는 c.network().show()
"같은 그룹 계열사" → c.network("members")
"출자/지분 구조" → c.network("edges")
"순환출자 있어?" → c.network("cycles")
**SeeAlso:** governance: 이사회/감사위원/최대주주 분석
capital: 주주환원 분석

#### Company.news
**Capabilities:** Google News RSS 기반 뉴스 수집
제목, 날짜, 소스, 링크
기간 조절 가능
**Requires:** 없음 (공개 RSS)
**AIContext:** 최근 뉴스로 시장 반응, 이슈, 이벤트 파악
ask()/chat()에서 정성적 시장 맥락 보충
**Guide:** "최근 뉴스 보여줘" → c.news()
"이번 주 뉴스" → c.news(days=7)
**SeeAlso:** liveFilings: 최신 공시 (뉴스가 아닌 공식 공시)
gather: 뉴스 포함 4축 외부 데이터 수집

#### Company.notes
**Capabilities:** K-IFRS 재무제표 주석(notes) 데이터 접근
주석 항목별 조회
**Requires:** 데이터: HuggingFace finance parquet (자동 다운로드)
**AIContext:** K-IFRS 주석에서 회계정책, 우발부채, 관계사 거래 등 정성 정보 추출
**Guide:** "주석사항 보여줘" → c.notes
"회계정책 확인" → c.notes에서 해당 항목 조회
**SeeAlso:** BS: 재무상태표 (주석이 보충하는 본문)
rawFinance: 재무 원본 데이터

#### Company.profile
**Capabilities:** docs sections를 spine으로, finance/report 데이터를 merge하여 통합 뷰 제공
profile.sections로 source 우선순위(finance > report > docs) 적용된 sections 접근
profile.show(topic)으로 merge된 결과 조회
**Requires:** 데이터: docs (자동 다운로드). finance/report는 있으면 자동 merge.
**AIContext:** c.sections는 내부적으로 profile.sections를 반환
분석/리뷰에서 통합된 데이터를 소비하는 기본 경로
**Guide:** "통합 프로필" → c.profile
"merge된 sections" → c.profile.sections
**SeeAlso:** sections: profile.sections의 단축 접근
show: profile 기반 topic 데이터 조회

#### Company.rank
**Capabilities:** 전체 시장 내 매출/자산 순위
섹터 내 상대 순위
매출 성장률 기반 규모 분류 (large/mid/small)
**Requires:** 데이터: buildSnapshot() 사전 실행 필요
**AIContext:** 시장/섹터 내 상대 위치 파악 — 피어 비교 분석의 기초
sizeClass로 대형/중형/소형주 분류
**Guide:** "이 회사 순위는?" → c.rank
"시장에서 몇 등이야?" → c.rank.revenueRank
"대형주야?" → c.rank.sizeClass
**SeeAlso:** sector: 섹터 분류 (rank의 기준 그룹)
insights: 종합 등급 평가

#### Company.ratioSeries
**Capabilities:** 수익성/안정성/성장성/효율성/밸류에이션 비율
연도별 dict 구조 (timeseries/annual과 동일 형태)
finance XBRL 기반 정확한 비율
**Requires:** 데이터: finance (자동 다운로드)
**AIContext:** 프로그래밍 방식 비율 접근 — insights/analysis 엔진이 내부적으로 소비
**Guide:** "비율 시계열 dict" → c.ratioSeries
"ROE 연도별 리스트" → series, years = c.ratioSeries; series["RATIO"]["roe"]
**SeeAlso:** ratios: DataFrame 형태 재무비율 (사용자 열람용)
annual: 연도별 재무 시계열 (비율이 아닌 원본 금액)

#### Company.ratios
**Capabilities:** 수익성/안정성/성장성/효율성/밸류에이션 5대 분류
분기별 시계열 비율 자동 계산
finance XBRL 기반 정확한 비율
**Requires:** 데이터: finance (자동 다운로드)
**AIContext:** ask()/chat()에서 재무 건전성/수익성 평가의 핵심 데이터
insights, review가 내부적으로 ratios를 소비
**Guide:** "재무비율 보여줘" → c.ratios
"ROE 추이" → c.ratios에서 ROE 행 확인
"부채비율은?" → c.ratios에서 안정성 분류 확인
**SeeAlso:** ratioSeries: dict 구조 재무비율 (프로그래밍 용도)
insights: 재무비율 기반 등급 + 이상치 분석
select: c.select("ratios", ["ROE"]) 특정 비율 추출

#### Company.rawDocs
**Capabilities:** HuggingFace docs 카테고리 원본 데이터 직접 접근
가공/정규화 이전 상태 그대로 반환
**Requires:** 데이터: HuggingFace docs parquet (자동 다운로드)
**AIContext:** 원본 데이터 구조 파악 — 파싱 전 상태로 디버깅/검증에 활용
**Guide:** "원본 공시 데이터 보여줘" → c.rawDocs
"가공 전 데이터 확인" → c.rawDocs
**SeeAlso:** sections: docs 가공 후 topic x period 통합 지도
rawFinance: 재무제표 원본 데이터
rawReport: 정기보고서 원본 데이터

#### Company.rawFinance
**Capabilities:** HuggingFace finance 카테고리 원본 데이터 직접 접근
XBRL 정규화 이전 상태 그대로 반환
**Requires:** 데이터: HuggingFace finance parquet (자동 다운로드)
**AIContext:** XBRL 정규화 전 원본 구조 파악 — 매핑 검증에 활용
**Guide:** "원본 재무 데이터 보여줘" → c.rawFinance
"XBRL 원본 확인" → c.rawFinance
**SeeAlso:** BS: 가공된 재무상태표
IS: 가공된 손익계산서
rawDocs: 공시 문서 원본

#### Company.rawReport
**Capabilities:** HuggingFace report 카테고리 원본 데이터 직접 접근
정기보고서 API 데이터 가공 이전 상태 반환
**Requires:** 데이터: HuggingFace report parquet (자동 다운로드)
**AIContext:** 정기보고서 API 원본 확인 — report topic 매핑 검증에 활용
**Guide:** "원본 보고서 데이터 보여줘" → c.rawReport
"정기보고서 원본 확인" → c.rawReport
**SeeAlso:** rawDocs: 공시 문서 원본
rawFinance: 재무제표 원본
show: 가공된 topic 데이터 조회

#### Company.readFiling
**Capabilities:** 접수번호(str) 직접 지정 또는 DataFrame row 자동 파싱
전문 텍스트 또는 ZIP 기반 구조화 섹션 반환
텍스트 길이 제한 (truncation) 지원
**Requires:** API 키: DART_API_KEY
**AIContext:** 공시 원문 텍스트를 LLM 컨텍스트에 주입하여 심층 분석 수행
sections=True로 구조화하면 특정 섹션만 선택적 분석 가능
**Guide:** "이 공시 내용 보여줘" → c.readFiling(접수번호)
"공시 원문 분석해줘" → c.readFiling()으로 원문 확보 후 ask()로 분석
**SeeAlso:** liveFilings: 최신 공시 목록에서 접수번호 확인
disclosure: 과거 공시 목록에서 접수번호 확인

#### Company.retrievalBlocks
**Capabilities:** docs 원문을 markdown 형태 그대로 보존한 검색용 블록
각 블록은 topic/subtopic/period 단위로 분할
RAG, 벡터 검색, 원문 참조에 최적화된 포맷
**Requires:** 데이터: docs (자동 다운로드)
**AIContext:** ask()/chat()에서 원문 기반 답변 생성 시 소스로 사용
retrieval 기반 컨텍스트 주입의 원천 데이터
**Guide:** "원문 검색용 블록" → c.retrievalBlocks
"RAG용 데이터" → c.retrievalBlocks
**SeeAlso:** contextSlices: retrievalBlocks를 LLM 윈도우에 맞게 슬라이싱한 결과
sections: 구조화된 데이터 지도 (retrievalBlocks의 원본)

#### Company.review
**Capabilities:** 14개 섹션 전체 보고서 (수익구조~재무정합성)
단일 섹션 지정 가능
4개 출력 형식 (rich, html, markdown, json)
섹션간 순환 서사 자동 감지
프리셋 지원 (executive/audit/credit/growth/valuation)
스토리 템플릿 (사이클/프랜차이즈/턴어라운드/성장/자본집약/지주/현금부자)
detail=False로 요약만 표시
레이아웃 커스텀
**Requires:** 데이터: finance + report (자동 다운로드)
**AIContext:** reviewer()가 이 결과를 소비하여 AI 해석 생성
ask()에서 재무분석 컨텍스트로 활용
**Guide:** "재무 검토서 만들어줘" -> c.review()
"수익구조 분석" -> c.review("수익구조")
"감사용 리뷰" -> c.review(preset="audit")
"이 회사 스토리는?" -> c.review(template="auto")
"요약만 보여줘" -> c.review(detail=False)
"AI 의견 포함 보고서" -> c.reviewer() (review + AI 해석)
**SeeAlso:** reviewer: review() + AI 섹션별 종합의견 (AI 해석 포함)
analysis: 14축 개별 분석 (review가 내부적으로 소비)
insights: 7영역 등급 + 이상치 요약

#### Company.reviewer
**Capabilities:** review() 데이터 위에 AI 섹션별 종합의견 추가
도메인 특화 가이드로 분석 관점 지정 가능
각 섹션 시작에 AI 해석 삽입
**Requires:** AI: provider 설정 (dartlab.setup() 참조)
데이터: finance + report (자동 다운로드)
**AIContext:** review() 결과(재무비율, 추세, 동종업계 비교)를 LLM에 제공
LLM이 각 섹션을 해석하여 종합의견 생성
guide 파라미터로 분석 관점 커스텀
**Guide:** "AI가 분석한 보고서" → c.reviewer()
"반도체 관점에서 분석" → c.reviewer(guide="반도체 사이클 관점에서 평가해줘")
"특정 섹션만 AI 분석" → c.reviewer("수익구조")
**SeeAlso:** review: AI 없는 순수 데이터 검토서 (reviewer의 기반)
ask: 자유 질문 기반 AI 분석
chat: 에이전트 모드 심화 분석

#### Company.sceMatrix
**Capabilities:** 원인(cause) x 세부(detail) x 연도 3차원 매트릭스
자본 구성요소별 변동 원인 추적
finance XBRL 정규화 기반
**Requires:** 데이터: finance (자동 다운로드)
**AIContext:** 자본 변동 원인 분석 — 배당/자사주/유증 등 자본 이벤트 추적
**Guide:** "자본변동표 매트릭스" → c.sceMatrix
"자본 변동 원인 추적" → matrix, years = c.sceMatrix
**SeeAlso:** SCE: DataFrame 형태 자본변동표 (sceMatrix의 2D 뷰)
BS: 재무상태표 (자본 잔액 확인)
capital: 주주환원 분석 (배당/자사주)

#### Company.sections
**Capabilities:** topic × period 수평화 통합 DataFrame
docs/finance/report 3-source 병합
show(topic)/trace(topic)/diff() 의 근간 데이터
**Requires:** 데이터: docs (필수), finance/report (선택, 자동 다운로드)
**AIContext:** 전체 지도가 필요할 때만 사용. 개별 topic은 show(topic) 추천
메모리 부하가 크므로 AI 코드에서 직접 접근 지양
**Guide:** "이 회사 전체 데이터 지도" → c.sections
"어떤 topic이 있어?" → c.topics (경량)
**SeeAlso:** topics: sections 기반 topic 요약 (더 간결)
show: 특정 topic 데이터 조회
index: 전체 구조 메타데이터 목차

#### Company.sector
**Capabilities:** WICS 11대 섹터 + 하위 산업그룹 자동 분류
KIND 업종명 + 주요제품 키워드 기반 매칭
override 테이블 우선 → 키워드 → 업종명 순 fallback
**Requires:** 데이터: KIND 상장사 목록 (자동 로드)
**AIContext:** 섹터 분류 결과로 동종업계 비교, 섹터 파라미터 자동 선택
analysis/valuation에서 섹터별 벤치마크 기준으로 활용
**Guide:** "이 회사 어떤 섹터야?" → c.sector
"업종 분류" → c.sector
**SeeAlso:** sectorParams: 섹터별 밸���에이션 파라미터 (할인율, PER 등)
rank: 섹�� 내 규모 순위
insights: 섹터 기준 등급 평가

#### Company.sectorParams
**Capabilities:** 섹터별 할인율, 성장률, PER 멀티플 제공
섹터 분류 결과에 연동된 파라미터 자동 선택
**Requires:** 데이터: sector 분류 결과 (자동 연산)
**AIContext:** valuation()에서 DCF 할인율, 성장률 자동 적용
섹터 특성 반영된 밸류에이션 파라미터
**Guide:** "이 섹터 할인율은?" → c.sectorParams.discountRate
"PER 멀티플" → c.sectorParams.perMultiple
**SeeAlso:** sector: 섹터 분류 정보 (sectorParams의 기반)
valuation: 밸류에이션 (sectorParams를 내부적으로 소비)

#### Company.select
**Capabilities:** show() 결과에서 특정 계정/항목만 추출
기간 필터링 (특정 연도만)
.chart() 체이닝으로 바로 시각화
한글/영문 계정명 모두 지원
**Requires:** 데이터: docs (자동 다운로드)
**AIContext:** 특정 계정의 시계열 추출 — 추세 분석 및 차트 생성의 기본 도구
.chart() 체이닝으로 시각화까지 한 번에
**Guide:** "매출액 추이 그래프" → c.select("IS", ["매출액"]).chart()
"영업이익만 뽑아줘" → c.select("IS", ["영업이익"])
"2023-2024 자본 비교" → c.select("BS", ["자본총계"], ["2024", "2023"])
**SeeAlso:** show: 전체 topic ��이터 조회 (select의 원본)
table: docs 마크다운 테이블 구조화 파싱

#### Company.show
**Capabilities:** 120+ topic 접근 (재무제표, 사업내용, 지배구조, 임원현황 등)
기간별 수평화 (topic × period 매트릭스)
블록 단위 drill-down (목차 → 상세)
docs/finance/report 3개 소스 자동 통합
세로 뷰 (period 리스트 전달 시)
**Requires:** 데이터: docs (자동 다운로드). finance topic은 finance 데이터도 필요.
**AIContext:** 120+ topic에 대한 단일 접근점 — LLM이 데이터를 조회하는 핵심 도구
period 리스트로 기간 비교 뷰 생성 가능
**Guide:** "배당 정보 보여줘" → c.show("dividend")
"사업 개요 확인" → c.show("businessOverview")
"2023년 손익계산서" → c.show("IS", period="2023")
"연도별 비교" → c.show("IS", period=["2022", "2023"])
**SeeAlso:** select: show() 결과에서 특정 행/열 필터 + 차트
trace: 데이터 출처 추적
topics: 사용 가능한 topic 전체 목록
diff: 기간간 텍스트 변경 비교

#### Company.sources
**Capabilities:** 3개 데이터 source(docs, finance, report) 존재 여부/규모 한눈에 확인
각 source의 row/col 수와 shape 문자열 제공
데이터 로드 전 가용성 사전 점검
**Requires:** 없음 (메타데이터만 조회, 데이터 파싱 불필요)
**AIContext:** 데이터 가용성 사전 점검 — 분석 가능 범위 판단의 기초
**Guide:** "데이터 뭐가 있어?" → c.sources
"docs/finance/report 상태" → c.sources
**SeeAlso:** topics: topic 단위 상세 데이터 지도
trace: 특정 topic의 출처 추적

#### Company.status
**Capabilities:** 로컬 데이터 현황 (종목별 docs/finance/report 보유 여부)
최종 업데이트 일시

#### Company.table
**Capabilities:** docs 원문의 markdown table을 Polars DataFrame으로 변환
subtopic 지정으로 특정 표만 추출
numeric 모드로 금액 문자열을 float 변환
period 필터로 특정 기간 컬럼만 선택
**Requires:** 데이터: docs (자동 다운로드)
**AIContext:** docs 원문 테이블을 구조화하여 정량 분석에 활용
numeric=True로 금액 문자열을 수치화하면 계산 가능
**Guide:** "직원 현황 테이블" → c.table("employee")
"표 데이터를 숫자로" → c.table(topic, numeric=True)
**SeeAlso:** show: topic 전체 데이터 (table은 subtopic 단위 파싱)
select: show() 결과에서 행/열 필터

#### Company.timeseries
**Capabilities:** BS/IS/CF 계정별 분기 standalone 시계열
최대 10년 분기별 데이터
finance XBRL 정규화 기반
**Requires:** 데이터: finance (자동 다운로드)
**AIContext:** insights, forecast, valuation 등 분석 엔진의 핵심 입력 데이터
분기별 추세 분석의 기초
**Guide:** "분기별 시계열 데이터" → c.timeseries
"매출 분기별 추이" → series, periods = c.timeseries; series["IS"]["sales"]
**SeeAlso:** annual: 연도별 집계 시계열
cumulative: 분기별 누적(YTD) 시계열
BS: DataFrame 형태 재무상태표 (timeseries의 다른 뷰)

#### Company.topics
**Capabilities:** docs/finance/report 모든 source의 topic을 하나의 DataFrame으로 통합
chapter 순서대로 정렬, 각 topic의 블록 수/기간 수/최신 기간 표시
어떤 데이터가 있는지 한눈에 파악
**Requires:** 데이터: docs/finance/report 중 하나 이상 (자동 다운로드)
**AIContext:** LLM이 가용 topic 목록을 파악하는 데 사용
분석 범위 결정 시 참조
**Guide:** "어떤 데이터가 있어?" → c.topics
"topic 목록" → c.topics
**SeeAlso:** show: 특정 topic 데이터 조회
sections: topic x period 전체 지도 (topics보다 상세)
index: 전체 구조 메타데이터 목차

#### Company.trace
**Capabilities:** topic별 데이터 출처 확인 (docs, finance, report)
출처 선택 이유 (우선순위, fallback 경로)
각 출처별 데이터 행 수, 기간 수, 커버리지
**Requires:** 데이터: docs + finance + report (보유한 것만 추적)
**AIContext:** 데이터 출처 신뢰도 판단 — finance > report > docs 우선순위 확인
분석 결과의 근거 투명성 확보
**Guide:** "이 데이터 어디서 온 거야?" → c.trace("BS")
"데이터 출처 확인" → c.trace(topic)
**SeeAlso:** show: topic 데이터 조회 (trace로 출처 확인 후 열람)
sources: 3개 source 전체 가용 현황

#### Company.update
**Capabilities:** DART API로 최신 공시 확인 후 누락분만 수집
카테고리별 선택 수집
**Requires:** API 키: DART_API_KEY
**AIContext:** 데이터 최신성 유지에 활용 — 분석 전 자동 갱신 트리거 가능
**Guide:** "최신 공시 반영해줘" → c.update()
"데이터 업데이트" → c.update()로 증분 수집
**SeeAlso:** filings: 현재 보유 공시 목록 확인
disclosure: OpenDART 전체 공시 조회

#### Company.view
**Capabilities:** 로컬 서버 기반 공시 뷰어 실행
브라우저에서 sections/index 탐색
**Requires:** 데이터: HuggingFace docs parquet (자동 다운로드)
**AIContext:** 시각적 탐색 인터페이스 — 사용자가 브라우저에서 직접 데이터 탐색
**Guide:** "공시 뷰어 열어줘" → c.view()
"브라우저에서 보기" → c.view()
**SeeAlso:** index: 뷰어가 소비하는 메타데이터 (프로그래밍 접근)
sections: 뷰어의 원본 데��터

#### Company.watch
**Capabilities:** 전체 topic 변화 중요도 스코어링
텍스트 변화량 + 재무 영향 통합 평가
특정 topic 상세 변화 내역
**Requires:** 데이터: docs (자동 다운로드)
**AIContext:** 공시 변화 중요도 자동 평가 — 분석 우선순위 결정에 활용
텍스트 변화량 + 재무 영향 통합 스코어
**Guide:** "뭐가 크게 바뀌었어?" → c.watch()
"리스크 관련 변화" → c.watch("riskManagement")
**SeeAlso:** diff: 줄 단위 상세 변경 비교 (watch보다 세밀)
keywordTrend: 키워드 빈도 추이

#### Company.workforce
**Capabilities:** 직원수 + 정규직/비정규직 비율
평균 급여 + 1인당 매출
평균 근속연수
시장 전체 인력 횡단 비교
**Requires:** 데이터: DART 정기보고서 (자동 수집)
**AIContext:** 인력 효율성/근무환경 정량 평가 — 1인당 매출, 급여 수준 비교
시장 횡단 비교로 인적자원 경쟁력 판단
**Guide:** "직원 현황" → c.workforce()
"평균 급여는?" → c.workforce()
"전체 상장사 인력 비교" → c.workforce("all")
**SeeAlso:** governance: 이사회/감사위원 구성 (인력의 다른 관점)
show: c.show("employee")로 docs 기반 직원 상세

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
| `beta` | `float` | 1.0 |
| `exitMultiple` | `float` | 0.0 |

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
