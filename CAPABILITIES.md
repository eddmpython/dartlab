# dartlab Capabilities

> v0.7.12 기준 자동 생성. 직접 수정 금지.  
> `uv run python scripts/generateSpec.py`로 재생성.


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
| `collect` | function | 지정 종목 DART 데이터 수집 (OpenAPI). 멀티키 시 병렬. |
| `collectAll` | function | 전체 상장종목 DART 데이터 수집. DART_API_KEY(S) 필요. 멀티키 시 병렬. |
| `downloadAll` | function | HuggingFace에서 전체 시장 데이터를 다운로드. |
| `scan` | function | 시장 전체 횡단분석 통합 엔트리포인트. |
| `network` | function | 한국 상장사 전체 관계 지도. |
| `news` | function | 기업 뉴스 수집. |
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
| `scanRatioList` | function | 사용 가능한 비율 목록. |
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

## AI Tools (101개)

LLM 에이전트가 tool calling으로 사용하는 도구. priority 내림차순.

### explore (priority: 95, category: company)

기업 공시 데이터 탐색 — 사업보고서, 리스크, 배당, 주석 등 공시 원문 조회.

**Actions:**

| action | 설명 |
|--------|------|
| `show` | topic 데이터 조회 (target 필수). 예: explore(action='show', target='businessOverview') |
| `topics` | 사용 가능한 전체 topic 목록. topic을 모를 때 먼저 호출 |
| `trace` | topic 출처 추적 (target 필수) |
| `diff` | 기간간 변화 분석 (target 선택). 예: explore(action='diff', target='riskFactor') |
| `info` | 기업 기본 정보 (업종, 대표자, 상장일) |
| `filings` | 공시 문서 목록 |
| `search` | 키워드로 topic 검색 (keyword 필수). 예: explore(action='search', keyword='비용의 성격별분류') |

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `target` | string | - | target 파라미터 (company별 동적 생성) |
| `block` | string | - | 블록번호 (action=show일 때). 비워두면 목차, 숫자면 해당 블록 |
| `keyword` | string | - | 검색어 (action=search일 때) |

**질문 유형**: 건전성, 수익성, 성장성, 배당, 리스크, 지배구조, 투자, 공시, 사업, 종합

### show_topic (priority: 95, category: company)

공시 topic의 데이터를 조회합니다. 공시 원문(텍스트/테이블)을 읽을 때 가장 먼저 사용하세요. block 없이 호출 → 블록 목차(block번호, type, source, period, preview). block=N → 해당 블록의 실제 데이터(원문 텍스트 또는 수치 테이블). **여러 기간의 블록이 존재하므로, 기간간 비교가 필요하면 각 기간의 block을 순서대로 조회하세요.** 사용 시점: 사업 내용, 리스크, 배당 정책, 부문별 매출, 원재료, 비용의 성격별분류 등 공시 원문이 필요할 때. 사용하지 말 것: 단순 재무 수치만 필요하면 get_data(BS/IS/CF)가 더 빠릅니다. topic을 모르면 먼저 list_topics를 호출하세요.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `topic` | string | O | topic 파라미터 (company별 동적 생성) |
| `block` | string | - | 블록 인덱스. 비워두면 블록 목차, 숫자면 해당 블록 데이터 |

**질문 유형**: 건전성, 수익성, 성장성, 배당, 리스크, 지배구조, 투자, 공시, 사업, 종합

### finance (priority: 90, category: finance)

재무 숫자 데이터 조회/분석 — 재무제표(IS/BS/CF), 재무비율, 성장률, 배당, 임원보수 등.

**Actions:**

| action | 설명 |
|--------|------|
| `data` | 재무제표 조회 (module 필수). 예: finance(action='data', module='IS') |
| `modules` | 사용 가능한 모듈 목록. 어떤 module이 있는지 모를 때 호출 |
| `ratios` | 재무비율 자동 계산 (ROE, 부채비율 등) |
| `growth` | CAGR 성장률 (module 필수) |
| `yoy` | 전년대비 변동률 (module 필수). 예: finance(action='yoy', module='IS') |
| `anomalies` | 이상치 탐지 (module 필수) |
| `report` | 정기보고서 정형 데이터 (apiType 필수). 예: finance(action='report', apiType='dividend') |
| `search` | 키워드로 데이터 검색 (keyword 필수) |
| `quality` | 이익의 질 종합 (Accrual Ratio, Beneish M-Score, OCF/NI, CCC) |
| `decompose` | DuPont 3요소 분해 시계열 (ROE = 순이익률 x 자산회전율 x 레버리지) |

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `module` | string | - | module 파라미터 (company별 동적 생성) |
| `apiType` | string | - | apiType 파라미터 (company별 동적 생성) |
| `keyword` | string | - | 검색 키워드 (action=search일 때) |

**질문 유형**: 건전성, 수익성, 성장성, 배당, 리스크, 종합

### get_data (priority: 90, category: finance)

기업의 재무/공시 데이터를 조회합니다. 모듈명을 모르면 먼저 `list_modules`를 호출하세요.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `module_name` | string | O | module_name 파라미터 (company별 동적 생성) |

**질문 유형**: 건전성, 수익성, 성장성, 배당, 리스크, 종합

### get_insight (priority: 85, category: analysis)

기업의 7영역 인사이트 종합 분석을 실행합니다. 영역: 실적, 수익성, 재무건전성, 현금흐름, 지배구조, 리스크, 기회 (각각 A~F 등급). 프로파일: premium/growth/stable/caution/distress 분류. 이상치 자동 탐지 포함. 사용 시점: 종합 분석, '이 회사 어때?', 투자 판단 근거가 필요할 때. 사용하지 말 것: 특정 재무 수치만 필요하면 get_data/compute_ratios가 빠릅니다.

**질문 유형**: 건전성, 수익성, 리스크, 종합

### list_topics (priority: 85, category: company)

이 기업에서 조회 가능한 모든 공시 topic 목록을 반환합니다. 각 topic의 라벨, 데이터 종류(docs/finance/report), 기간 수를 포함합니다. 사용 시점: show_topic에 넣을 topic을 모를 때, '어떤 공시가 있어?' 질문에 답할 때. 사용하지 말 것: 이미 topic을 알고 있으면 바로 show_topic을 호출하세요.

**질문 유형**: 건전성, 수익성, 성장성, 배당, 리스크, 지배구조, 투자, 공시, 사업, 종합

### intrinsic_value (priority: 85, category: valuation)

내재가치를 추정합니다. DCF(현금흐름할인), DDM(배당할인), 상대가치(섹터배수) 3가지 모델을 지원합니다. 사용 시점: 적정 주가/기업가치 판단, 저평가/고평가 분석. model 파라미터: 'all'(종합), 'dcf', 'ddm', 'relative' 중 선택.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `model` | string | - | 밸류에이션 모델 (all, dcf, ddm, relative) |

**질문 유형**: 투자

### price_target (priority: 85, category: valuation)

확률 가중 주가 목표가를 산출합니다. 5개 매크로 시나리오(기준/금리인상/중국둔화/반도체하강/경기침체)별 Pro-Forma 재무제표 → DCF 밸류에이션 → Monte Carlo 5000회 시뮬레이션을 수행합니다. P10~P90 분포, 현재가 대비 업사이드, 투자 신호(strong_buy~strong_sell)를 제공합니다. 사용 시점: 종합적인 주가 분석, 매수/매도 판단 근거 도출.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `current_price` | string | - | 현재 주가(원). 빈 문자열이면 market 데이터에서 자동 조회. |
| `shares` | string | - | 발행주식수. 빈 문자열이면 market 데이터에서 자동 조회. |
| `mc_iterations` | string | - | Monte Carlo 반복 횟수 (기본 5000) |

**질문 유형**: 투자

### search_dart_filings (priority: 85, category: global)

OpenDART 전체 시장 공시목록을 검색합니다. 최근 며칠 공시, 수주공시, 계약공시, 단일판매공급계약 질문에 우선 사용하세요.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `corp` | string | - | 회사명/종목코드/corp_code. 비우면 전체 시장 |
| `start` | string | - | 시작일 YYYYMMDD |
| `end` | string | - | 종료일 YYYYMMDD |
| `days` | integer | - | 최근 N일 |
| `weeks` | integer | - | 최근 N주 |
| `disclosure_type` | string | - | 공시유형 A~J |
| `market_code` | string | - | 법인구분 Y/K/N/E |
| `final_only` | boolean | - | 최종보고서만 |
| `keywords` | string | - | 제목 키워드 쉼표 목록 |
| `limit` | integer | - | 최대 건수 |

**질문 유형**: 공시, 사업

### analyze (priority: 80, category: analysis)

기업 심층 분석 — 인사이트 등급, 섹터, 밸류에이션, 변화감지 등.

**Actions:**

| action | 설명 |
|--------|------|
| `insight` | 7영역 인사이트 등급 (수익성, 안정성, 성장성, 효율성, 배당, 밸류에이션, 거버넌스) |
| `sector` | WICS 섹터 정보 + 업종 비교 |
| `rank` | 시가총액 순위 |
| `valuation` | DCF/상대가치 밸류에이션 |
| `changes` | 공시 텍스트 변화 감지 |
| `audit` | 재무 감사 이상치 분석 |
| `research` | 기관급 종합 리서치 리포트 |
| `distress` | 부도 예측 4모델 종합 |
| `watch` | 현재 기업 공시 변화 점수화 (scored changes) |
| `digest` | 전종목 공시 변화 다이제스트 (상위 변화 종목) |

**질문 유형**: 건전성, 수익성, 성장성, 배당, 리스크, 지배구조, 투자, 종합

### compute_ratios (priority: 80, category: finance)

재무상태표(BS)와 손익계산서(IS)로 핵심 재무비율을 자동 계산합니다. 반환: 부채비율, 유동비율, 영업이익률, 순이익률, ROE, ROA (연도별 테이블). 사용 시점: 건전성/수익성 분석, 비율 추세 확인. 사용하지 말 것: 원본 BS/IS 수치 자체가 필요하면 get_data를 사용하세요.

**질문 유형**: 건전성, 수익성, 종합

### forecast_revenue (priority: 80, category: valuation)

매출 앙상블 예측 v3. 7소스(시계열+컨센서스+ROIC+매크로+세그먼트+수주잔고+환율) 결합. 세그먼트 Bottom-Up 예측, 3-시나리오(Base/Bull/Bear) 출력, 수주잔고 선행지표 포함. 사용 시점: 매출 전망, 성장성 평가, 밸류에이션 입력. forecast 도구와의 차이: forecast는 단일 시계열, forecast_revenue는 다중 소스 앙상블.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `horizon` | string | - | 예측 기간 (년, 1~5) |

**질문 유형**: 투자, 성장성

### get_current_price (priority: 80, category: market)

종목의 현재 주가, 등락률, 거래량을 조회합니다. 네이버 → 야후 파이낸스 fallback 체인으로 실시간 데이터를 가져옵니다. 사용 시점: '현재 주가', '오늘 주가', '시세', '거래량' 질문.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `stockCode` | string | O | 종목코드 (예: '005930') 또는 티커 (예: 'AAPL') |
| `market` | string | - | 시장 ('KR' 또는 'US') |

**질문 유형**: 투자, 밸류에이션

### run_audit (priority: 75, category: analysis)

감사 Red Flag 분석을 실행합니다. 감사의견, 내부통제, 계속기업 가정, 우발채무, 관련 당사자 거래 등을 종합 점검합니다. 사용 시점: '감사 이슈', '리스크 총점검', '내부통제 문제', '부실 징후' 질문. 사용하지 말 것: 일반적인 재무비율 분석에는 compute_ratios가 적절합니다.

**질문 유형**: 리스크, 종합

### run_valuation (priority: 75, category: analysis)

DCF, DDM, 상대가치(PER/PBR) 등 다중 모델로 적정 주가를 산출합니다. 각 모델의 산출 근거와 가중평균 목표가를 반환합니다. 사용 시점: '적정 주가', '목표가', 'DCF', '밸류에이션', '저평가/고평가' 질문. 사용하지 말 것: 단순 PER/PBR 비율은 compute_ratios가 빠릅니다.

**질문 유형**: 밸류에이션, 투자, 종합

### get_company_info (priority: 75, category: company)

기업의 기본 정보(기업명, 종목코드, 대표자, 주요사업, 업종)를 조회합니다. 사용 시점: 기업 개요 파악, 분석 시작 시 기본 정보 확인. 사용하지 말 것: 재무 수치가 필요하면 get_data, 공시 원문은 show_topic을 사용하세요.

**질문 유형**: 종합

### list_modules (priority: 75, category: finance)

이 기업에서 조회 가능한 모든 데이터 모듈(BS, IS, CF, dividend, audit 등) 목록을 반환합니다. 사용 시점: get_data에 넣을 모듈명을 모를 때. 사용하지 말 것: 공시 원문(sections) 목록이 필요하면 list_topics를 사용하세요. list_modules는 재무/정형 데이터, list_topics는 공시 문서 목록입니다.

### get_report_data (priority: 75, category: finance)

DART 정기보고서 API의 표준화된 정형 데이터를 조회합니다. 사용 시점: 배당·직원·임원·주주 등 정형화된 수치가 필요할 때. get_data(BS/IS)와는 다른 소스. 사용하지 말 것: 공시 원문 텍스트가 필요하면 show_topic을 사용하세요.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `api_type` | string | O | api_type 파라미터 (company별 동적 생성) |

**질문 유형**: 배당, 지배구조, 공시

### scenario (priority: 75, category: valuation)

Bull/Base/Bear 3개 시나리오별 DCF 분석을 수행하고 확률 가중 적정가치를 산출합니다. 사용 시점: 투자 의사결정 시 다양한 가능성 검토, 리스크-보상 분석.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `current_price` | string | - | 현재 주가 (원, 선택사항) |

**질문 유형**: 투자

### get_consensus (priority: 75, category: market)

증권사 컨센서스 목표가와 투자의견을 조회합니다. 사용 시점: '목표가', '컨센서스', '증권사 의견', '투자 등급' 질문.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `stockCode` | string | O | 종목코드 (예: '005930') |

**질문 유형**: 투자, 밸류에이션

### get_dart_filing_text (priority: 75, category: global)

OpenDART 접수번호(rcept_no) 기준으로 공시 원문 텍스트를 가져옵니다. 목록에서 중요 공시를 골라 본문을 읽을 때 사용하세요.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `rcept_no` | string | O | 접수번호 |
| `max_chars` | integer | - | 최대 글자수 |

**질문 유형**: 공시, 사업

### checkDataReady (priority: 75, category: global)

종목의 데이터 준비 상태(docs/finance/report)를 확인합니다. 분석 전 데이터가 있는지 확인할 때 사용하세요.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `stockCode` | string | O | 종목코드 (예: 005930) |

### market (priority: 70, category: global)

시장/주가/재무 데이터 조회 + 전종목 비교 분석.

**Actions:**

| action | 설명 |
|--------|------|
| `price` | 현재 주가 (code 필수) |
| `consensus` | 애널리스트 컨센서스 (code 필수) |
| `history` | 주가 이력 (code, days) |
| `scan` | 종목 포지셔닝 (시총순위, 핵심지표). code 필수 |
| `financials` | 재무제표 (code, statement=BS/IS/CF/CIS) |
| `ratios` | 재무비율 (code 필수) |
| `scanAccount` | 전종목 단일 계정 시계열. snakeId 필수 (예: sales, operatingIncome). code로 특정 종목 필터링 가능 (쉼표... |
| `scanRatio` | 전종목 단일 비율 시계열. ratioName 필수 (예: roe, debtRatio). code로 필터링 가능 |
| `scanRatioList` | 사용 가능한 비율 목록 |
| `governance` | 전종목 지배구조 스캔 (지분율, 사외이사, 보수, 감사의견) |
| `workforce` | 전종목 인력/급여 스캔 (직원수, 평균급여, 근속년수) |
| `capital` | 전종목 주주환원 스캔 (배당, 자사주, 증자) |
| `debt` | 전종목 부채구조 스캔 (사채, 부채비율, ICR) |

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `code` | string | - | 종목코드 (예: 005930). scanAccount/scanRatio에서 쉼표 구분으로 복수 종목 필... |
| `snakeId` | string | - | 계정ID (action=scanAccount). 예: sales, operatingIncome, tot... |
| `ratioName` | string | - | 비율명 (action=scanRatio). 예: roe, debtRatio, operatingMargi... |
| `days` | string | - | 주가이력 기간(일). 기본 365 |
| `statement` | string | - | 재무제표 종류 (action=financials): BS/IS/CF/CIS |

**질문 유형**: 투자, 종합

### get_sector_info (priority: 70, category: analysis)

기업의 WICS 섹터 분류(대/중분류)와 섹터 기준 밸류에이션(PER, PBR, 할인율)을 조회합니다. 사용 시점: 업종 비교, 밸류에이션 판단, '동종업계 대비 어때?' 질문. 사용하지 말 것: 기업 자체 재무비율은 compute_ratios를 사용하세요.

**질문 유형**: 투자, 종합

### run_forecast (priority: 70, category: analysis)

매출, 영업이익, 순이익의 향후 실적을 예측합니다. 과거 추세와 성장률 기반으로 3년 예측치와 성장률을 반환합니다. 사용 시점: '향후 실적', '매출 전망', '이익 예측', '성장 가능성' 질문.

**질문 유형**: 밸류에이션, 성장성, 투자

### diff_topic (priority: 70, category: company)

공시 텍스트의 기간간 변화를 분석합니다. topic 없이 호출 → 전체 topic의 변화율 요약 (어디가 많이 바뀌었는지). topic 지정 → 해당 topic의 기간별 상세 변화(추가/삭제/수정). 사용 시점: '뭐가 바뀌었어?', '리스크 변화', '사업 구조 변경' 같은 변화 감지 질문. 사용하지 말 것: 현재 시점의 데이터만 필요하면 show_topic이 적절합니다.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `topic` | string | - | 분석할 topic. 비워두면 전체 요약 |

**질문 유형**: 리스크, 성장성, 공시, 사업, 배당, 종합

### search_company (priority: 70, category: meta)

종목명/종목코드로 기업을 검색합니다. 종목코드를 모를 때 사용하세요.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `keyword` | string | O | 검색 키워드 (예: '삼성', '현대차', '반도체') |

### detect_anomalies (priority: 70, category: finance)

재무 데이터에서 이상치(급격한 YoY 변동, 부호 반전)를 자동 탐지합니다. 사용 시점: 리스크 분석, 이상 징후 확인, '뭔가 이상한 게 있어?' 질문. 사용하지 말 것: 정상적인 재무 추세 분석에는 compute_ratios나 yoy_analysis가 적절합니다.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `module_name` | string | O | 분석할 모듈명 (예: BS, IS, CF) |
| `threshold_pct` | number | - | 이상치 판정 기준 YoY 변동률 (기본 50%) |

**질문 유형**: 리스크

### compute_growth (priority: 70, category: finance)

다기간 CAGR(복합연간성장률) 매트릭스를 계산합니다. 1Y, 2Y, 3Y, 5Y 성장률 반환. 사용 시점: 성장성 분석, '매출 성장률이 어떻게 돼?' 질문. 사용하지 말 것: 단순 전년 대비는 yoy_analysis가 더 적절합니다.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `module_name` | string | O | 분석할 모듈명 (예: IS, dividend) |

**질문 유형**: 성장성

### forecast (priority: 70, category: valuation)

매출/영업이익/순이익/영업CF의 미래 값을 예측합니다. 선형회귀, CAGR 감속, 평균 회귀 중 데이터에 맞는 방법을 자동 선택합니다. 사용 시점: 미래 실적 전망, DCF 입력값 확인. metric: revenue(매출), operating_income(영업이익), net_income(순이익), operating_cashflow(영업CF).

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `metric` | string | - | 예측 대상 (revenue, operating_income, net_income, operating_c... |
| `horizon` | string | - | 예측 기간 (년, 1~5) |

**질문 유형**: 투자, 성장성

### run_simulation (priority: 70, category: valuation)

경제 시나리오 시뮬레이션을 실행합니다. 기준/금리인상/금리인하/경기침체/기술하강 등 매크로 시나리오별 재무 영향을 추정합니다. 사용 시점: '경기침체 시 이 회사는?', '금리 인상 영향', '시나리오 분석' 질문. 사용하지 말 것: 과거 실적 분석에는 compute_ratios/get_data가 적절합니다.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `scenarios` | string | - | 시나리오 이름 (쉼표 구분). 비워두면 전체 프리셋. 예: baseline,adverse,rate_hike |

**질문 유형**: 투자, 종합

### call_dart_openapi (priority: 70, category: global)

DART OpenAPI를 직접 호출합니다. action 예시: search, company, corp_code, corp_codes, filings, document_text, finstate, report, major_shareholders, executive_shares, report_types, filing_types, markets, xbrl_taxonomy.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `corp` | string | - | 회사명/종목코드/corp_code |
| `query` | string | - | search용 검색어 |
| `start` | string | - | 시작일 또는 연도 |
| `end` | string | - | 종료일 또는 종료 연도 |
| `quarter` | integer | - | 분기. 0~4 또는 null |
| `report_type` | string | - | 예: 배당, 직원, 임원 |
| `listed` | boolean | - | 상장사만 검색 |
| `disclosure_type` | string | - | 공시유형 예: A |
| `final` | boolean | - | 최종보고서만 |
| `market_code` | string | - | 법인구분 Y/K/N/E |
| `consolidated` | boolean | - | 연결 기준 |
| `full` | boolean | - | 전체 계정 |
| `taxonomy_category` | string | - | xbrl taxonomy 카테고리 |
| `rcept_no` | string | - | document_text용 접수번호 |
| `max_chars` | integer | - | document_text 최대 글자수 |

**질문 유형**: 공시, 사업

### get_scan_data (priority: 70, category: analysis)

기업의 종합 스캔 분석을 조회합니다. 거버넌스(지분율/사외이사/보수비율/감사의견 등급), 인력(직원수/평균급여/성장률/인건비부담), 주주환원(배당/자사주/증자 → 환원형/중립/희석형), 부채구조(부채비율/ICR → 안전/관찰/주의/고위험). 사용자가 '거버넌스', '인력현황', '주주환원', '부채위험', '종합진단' 등을 물을 때 사용하세요.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `axis` | enum(all, governance, workforce, capital, debt) | - | 스캔 축. all=전체, governance=지배구조, workforce=인력, capital=주주환원... |

**질문 유형**: 지배구조, 건전성, 종합

### get_system_spec (priority: 70, category: meta)

DartLab 시스템의 전체 스펙(엔진 목록, 데이터 종류, 기능)을 조회합니다. 사용자가 '어떤 데이터가 있어?', '무슨 분석이 가능해?' 같은 메타 질문을 할 때 사용하세요.

### estimateTime (priority: 70, category: global)

작업의 예상 소요 시간을 안내합니다. 오래 걸리는 작업 전에 사용자에게 미리 안내할 때 사용하세요. operation: company_load, full_analysis, forecast, valuation, simulation, market_scan, download_docs, download_finance, download_single.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `operation` | string | O | 작업 종류 |
| `stockCode` | string | - | 종목코드 (선택) |

### read_filing (priority: 66, category: company)

특정 공시의 원문 본문을 조회합니다. DART는 rceptNo, EDGAR는 filing URL 또는 accession 메타를 받아 본문을 회수합니다. 사용 시점: 목록에서 고른 공시를 실제로 읽고 요약할 때. 사용하지 말 것: 어떤 공시가 있는지 모르면 먼저 list_live_filings를 사용하세요.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `doc_id` | string | - | DART rceptNo 또는 EDGAR accessionNo |
| `doc_url` | string | - | EDGAR filing URL 또는 DART viewer URL |
| `max_chars` | integer | - | 본문 최대 길이 |

**질문 유형**: 공시, 사업, 리스크, 종합

### research (priority: 65, category: global)

외부 웹 검색 + URL 추출 -- 실시간 뉴스, 산업 동향, 규제 변화 조사.

**Actions:**

| action | 설명 |
|--------|------|
| `search` | 일반 웹 검색 (query 필수) |
| `news` | 뉴스 검색 (query 필수, days 선택 기본 7일) |
| `read_url` | URL 본문을 마크다운으로 추출 (url 필수) |
| `industry` | 산업/규제 검색 (query 필수, region 선택 kr/us/jp) |

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `query` | string | - | 검색어 (action=search/news/industry) |
| `url` | string | - | 읽을 URL (action=read_url) |
| `maxResults` | string | - | 최대 결과 수. 기본 8 |
| `days` | string | - | 검색 기간(일). news 기본 7 |
| `region` | enum(kr, us, jp) | - | 산업검색 지역 (action=industry). 기본 kr |

**질문 유형**: 뉴스, 산업, 규제, 동향, 실시간, 종합, 리스크

### get_disclosure_changes (priority: 65, category: analysis)

최근 공시에서 무엇이 바뀌었는지 중요도 순으로 보여줍니다. sections diff + 중요도 스코어링(0~100)으로 주목할 변화를 탐지합니다. 사용 시점: '뭐가 바뀌었어?', '최근 변화', '공시 변경 사항', '주목할 부분' 질문. topic 파라미터로 특정 항목(예: 'riskManagement')만 필터 가능.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `topic` | string | - | 특정 topic 필터 (비워두면 전체 스캔) |

**질문 유형**: 변화, 공시, 리스크, 종합

### analyze_disclosure_change (priority: 65, category: company)

공시 텍스트 변화를 종합 분석합니다: diff 요약 + 키워드 빈도 추이. keyword를 지정하면 해당 키워드의 topic별 연도 빈도를 추가로 보여줍니다. 사용 시점: '공시 변화 분석', '키워드 트렌드', 'AI 언급이 늘었나', '리스크 변화 추이'. diff_topic보다 넓은 시야 — 전체 변화 요약 + 키워드 기반 인사이트.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `keyword` | string | - | 추적할 키워드 (예: 'AI', '공급망', '소송'). 비워두면 54개 내장 키워드 전체 분석 |

**질문 유형**: 리스크, 성장성, 공시, 종합

### search_data (priority: 65, category: finance)

키워드로 모든 데이터 모듈을 검색합니다. 특정 계정과목(예: '매출액', '부채'), 지표명, 또는 컬럼명으로 검색합니다. 어떤 모듈에 데이터가 있는지 모를 때 유용합니다.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `keyword` | string | O | 검색할 키워드 (예: '매출', '부채비율', 'R&D', '이자비용') |

### yoy_analysis (priority: 65, category: finance)

데이터의 전년 대비(YoY) 변동률을 계산합니다. 각 항목의 연도별 증감률(%)을 반환. 사용 시점: '작년 대비 어떻게 변했어?', 수익성/배당 추이 분석. 사용하지 말 것: 다년간 CAGR이 필요하면 compute_growth를 사용하세요.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `module_name` | string | O | 분석할 모듈명 (예: IS, BS, dividend) |

**질문 유형**: 성장성

### get_ratio_series (priority: 65, category: finance)

재무비율의 연도별 시계열 데이터를 조회합니다. ratio를 지정하면 해당 비율만, 비워두면 전체 비율 시계열을 반환합니다. 사용 시점: '부채비율 추이', 'ROE 3년간 변화', '비율 트렌드' 같은 추세 분석. 사용하지 말 것: 현재 시점 비율만 필요하면 compute_ratios가 빠릅니다.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `ratio` | string | - | 조회할 비율명 (예: roe, debtRatio, currentRatio). 비워두면 전체 |

**질문 유형**: 건전성, 수익성, 성장성

### economic_forecast (priority: 65, category: valuation)

거시경제 시나리오(GDP/금리/환율)에 따른 3년 실적 시뮬레이션을 수행합니다. 업종별 경기감응도(β)를 자동 적용하여 매출·영업이익·FCF 경로를 추정합니다. 사용 시점: 경기침체/금리인상/중국둔화 등 거시 변수가 기업에 미치는 영향 분석. 사전 정의 시나리오: baseline(기준), adverse(경기침체), china_slowdown(중국둔화), rate_hike(금리인상), semiconductor_down(반도체불황), all(전체).

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `scenario` | string | - | 시나리오 이름 (baseline/adverse/china_slowdown/rate_hike/semico... |

**질문 유형**: 리스크, 투자

### proforma_forecast (priority: 65, category: valuation)

3-Statement Pro-Forma 재무제표를 생성합니다. 과거 비율(중위값) 기반으로 IS→BS→CF 연결 모델을 구축하고 BS 균형을 검증합니다. 매출 성장 경로를 입력하면 5년간 예측 재무제표가 생성됩니다. 사용 시점: 기업의 미래 재무 상태 시뮬레이션, 투자 분석.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `growth` | string | - | 연도별 매출 성장률(%), 콤마 구분. 예: '5,4,3,2.5,2' |
| `scenario_name` | string | - | 시나리오 이름 (예: base, optimistic, pessimistic) |

**질문 유형**: 투자, 성장성

### get_fund_flow (priority: 65, category: market)

기관, 외국인, 개인의 매매 동향(순매수)을 조회합니다. 사용 시점: '수급', '외국인', '기관 동향', '순매수' 질문.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `stockCode` | string | O | 종목코드 (예: '005930') |

**질문 유형**: 투자

### network_graph (priority: 65, category: analysis)

기업의 투자/주주 관계망(계열사, 투자관계, 순환출자)을 조회합니다. 사용자가 '삼성 계열사', '관계 지도', '순환출자', '지배구조' 같은 요청을 할 때 사용하세요.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `hops` | integer | - | 관계 탐색 깊이 (1=직접 관계, 2=2단계) |

**질문 유형**: 지배구조

### get_tool_catalog (priority: 65, category: meta)

현재 대화에서 등록된 도구 목록을 조회합니다. 새로 추가된 도구도 현재 registry 기준으로 자동 반영됩니다.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `include_parameters` | boolean | - | true면 각 도구의 파라미터까지 함께 출력 |

### list_live_filings (priority: 64, category: company)

기업의 실시간 공시 목록을 조회합니다. OpenDART 또는 EDGAR public source 기준으로 최신 filing 메타데이터를 반환합니다. 사용 시점: '최근 공시 뭐 있었어?', '최근 30일 10-Q', '이번 달 공시 목록' 질문. 사용하지 말 것: 이미 저장된 로컬 docs 목록만 보면 되면 list_filings를 사용하세요.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `days` | integer | - | 최근 며칠 범위를 볼지 (기본 30일) |
| `limit` | integer | - | 최대 반환 건수 (기본 20) |
| `keyword` | string | - | 제목/설명 keyword 필터 |
| `forms` | string | - | EDGAR form 필터. 쉼표 구분 예: '10-K,10-Q' |
| `final_only` | boolean | - | DART에서 최종보고서만 볼지 여부 |

**질문 유형**: 공시, 사업, 종합

### openapi (priority: 60, category: global)

DART/EDGAR OpenAPI 직접 호출 — 실시간 공시 검색, 원본 API 접근.

**Actions:**

| action | 설명 |
|--------|------|
| `dartCall` | DART API 엔드포인트 호출 (endpoint, params 필수) |
| `searchFilings` | DART 공시 키워드 검색 (keyword 필수) |
| `capabilities` | 사용 가능한 API 목록 조회 |

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `endpoint` | string | - | API 엔드포인트 (action=dartCall일 때) |
| `params` | string | - | API 파라미터 (JSON 문자열) |
| `keyword` | string | - | 검색어 (action=searchFilings일 때) |

**질문 유형**: 공시

### system (priority: 60, category: meta)

시스템 메타 정보 — 기능 목록, 종목 검색, 데이터 상태 조회.

**Actions:**

| action | 설명 |
|--------|------|
| `spec` | 시스템 스펙 조회 |
| `features` | 사용 가능한 기능 목록 |
| `searchCompany` | 종목 검색 (keyword 필수). 예: system(action='searchCompany', keyword='삼성') |
| `dataStatus` | 데이터 다운로드 상태 |
| `suggest` | 질문 추천 |

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `keyword` | string | - | 검색어 (action=searchCompany일 때) |

**질문 유형**: 종합

### get_rank (priority: 60, category: analysis)

기업의 전체 시장 및 섹터 내 규모 순위를 조회합니다. 매출/자산/성장률 순위와 상위 %를 반환. 규모 분류(대형/중형/소형) 포함. 사용 시점: 시장 내 위치 파악, '이 회사 규모가 어느 정도야?' 질문. 사용하지 말 것: 재무 수치 자체가 필요하면 get_data를 사용하세요.

**질문 유형**: 종합

### trace_topic (priority: 60, category: company)

topic 데이터의 출처를 추적합니다. 각 블록이 docs(공시원문), finance(재무제표), report(정기보고서) 중 어디서 왔는지 확인합니다. 사용 시점: 데이터 신뢰성을 확인할 때, 수치의 원본 소스를 밝힐 때. 사용하지 말 것: 데이터 내용 자체를 보려면 show_topic을 사용하세요.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `topic` | string | O | 추적할 topic (예: businessOverview, IS, dividend) |

**질문 유형**: 리스크, 공시, 지배구조

### timeseries_filter (priority: 60, category: finance)

특정 계정의 시계열 데이터를 기간 범위로 필터링하여 반환합니다. 사용자가 '최근 3년 매출 추이', '2020년부터 영업이익', '특정 계정 시계열' 같은 요청을 할 때 사용하세요. account는 계정명(snakeId), since/until은 기간 필터(예: 2020, 2022Q2)입니다.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `account` | string | O | 계정명 (예: revenue, operating_income, total_assets) |
| `since` | string | - | 시작 기간 (예: 2020, 2021Q1) |
| `until` | string | - | 종료 기간 (예: 2024, 2024Q4) |

### get_timeseries (priority: 60, category: finance)

특정 계정과목의 분기별/연도별 시계열을 조회합니다. 예: get_timeseries('sales', 'IS') → 매출액 분기별 시계열. 사용 시점: 특정 계정의 세밀한 추이 분석, 분기별 패턴 확인. 사용하지 말 것: 전체 재무제표가 필요하면 get_data(IS/BS/CF)를 사용하세요.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `account` | string | O | 계정명 (snakeId, 예: sales, operating_profit, total_assets, n... |
| `statement` | string | - | 재무제표 유형 (IS, BS, CF) |

### sensitivity (priority: 60, category: valuation)

WACC와 영구성장률 조합에 따른 주당 내재가치 민감도 테이블을 생성합니다. 사용 시점: DCF 결과의 핵심 가정 변화에 따른 가치 변동 확인.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `wacc_range` | string | - | WACC ± 범위 (%p, 기본 2) |
| `growth_range` | string | - | 영구성장률 ± 범위 (%p, 기본 1) |

**질문 유형**: 투자

### stress_test (priority: 60, category: valuation)

CCAR 스타일 스트레스 테스트를 수행하여 경기침체 시 기업의 생존 가능성을 평가합니다. 3년간 매출/마진 변화, 부채비율 추이, 배당 지속 가능성, 생존 위험도를 산출합니다. 사용 시점: 극단적 경제 상황에서 기업의 재무 복원력 평가.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `scenario` | string | - | 스트레스 시나리오 (adverse/china_slowdown/semiconductor_down 등) |

**질문 유형**: 리스크

### get_price_history (priority: 60, category: market)

기간별 주가 이력(OHLCV)을 조회합니다. 차트 분석, 추세 확인에 사용합니다. 사용 시점: '주가 추이', '차트', '최근 N일 주가' 질문.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `stockCode` | string | O | 종목코드 (예: '005930') |
| `start` | string | - | 시작일 (YYYY-MM-DD, 비워두면 최근 3개월) |
| `end` | string | - | 종료일 (YYYY-MM-DD, 비워두면 오늘) |

**질문 유형**: 투자

### get_digest (priority: 60, category: analysis)

시장 전체 공시 변화 다이제스트를 조회합니다. 최근 공시에서 가장 큰 텍스트 변화를 보인 기업/토픽을 요약합니다. 사용 시점: '시장 동향', '이번 주 주요 공시', '어디서 변화가 컸어?' 질문. 사용하지 말 것: 특정 기업 분석에는 diff_topic이 적절합니다.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `sector` | string | - | 섹터 필터 (예: 'IT', '금융'). 비워두면 전체 시장. |
| `top_n` | integer | - | 상위 N개 변화 항목 (기본 20) |

**질문 유형**: 종합

### get_engine_spec (priority: 60, category: meta)

특정 엔진의 상세 스펙을 조회합니다. 엔진명 예시: insight(인사이트), sector(섹터분류), rank(규모순위), dart.finance(재무제표), dart.report(정기보고서). 각 엔진이 제공하는 구체적 지표·영역·분류 기준을 확인할 수 있습니다.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `engine` | string | O | 엔진명 (예: insight, sector, rank, dart.finance, dart.report) |

### discover_features (priority: 60, category: meta)

카테고리별 사용 가능한 기능을 상세히 안내합니다. category: finance, report, disclosure, notes, analysis, raw, all. 사용자가 '어떤 기능이 있어?', '주석 데이터 뭐가 있어?' 같은 질문에 사용하세요.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `category` | string | - | 카테고리 (finance, report, disclosure, notes, analysis, raw, ... |

### navigate_viewer (priority: 60, category: ui)

공시 뷰어에서 특정 섹션을 표시합니다. 사용자가 '배당 섹션 보여줘', '사업개요로 이동' 같은 요청을 할 때 사용하세요. topic은 list_topics로 확인할 수 있습니다.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `topic` | string | O | 이동할 topic (예: businessOverview, dividend, BS) |
| `period` | string | - | 특정 기간 (예: 2024Q4). 비워두면 최신 |
| `chapter` | string | - | 챕터 인덱스. 비워두면 첫 번째 |

### suggest_questions (priority: 58, category: meta)

현재 기업의 데이터 상태에 맞는 추천 질문 5~8개를 생성합니다. 사용자가 '무엇을 물어보면 돼?', '추천 질문 보여줘'라고 할 때 사용하세요. 현재 company가 없으면 stockCode를 넣어 호출할 수 있습니다.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `stockCode` | string | - | 현재 회사가 없을 때 사용할 종목코드 |

### run_stress_test (priority: 55, category: analysis)

경기침체, 금리 상승, 매출 급감 등 극단 시나리오에서의 재무 영향을 시뮬레이션합니다. 사용 시점: '위기 상황', '스트레스 테스트', '최악의 경우', '충격 시나리오' 질문.

**질문 유형**: 리스크, 투자

### get_sections (priority: 55, category: company)

기업의 전체 공시 지도(sections)를 조회합니다. 어떤 topic이 어떤 장(chapter)에 있는지, source(docs/finance/report)가 무엇인지 확인. show(topic, block)으로 접근하기 전에 먼저 이 도구로 전체 구조를 파악하세요.

**질문 유형**: 공시, 사업

### list_filings (priority: 55, category: company)

기업의 로컬 docs 기준 공시 문서 목록을 조회합니다. 이미 저장된 parquet/docs에서 filings() 결과를 보여줍니다. 사용 시점: 로컬에 수집된 문서 목록을 확인할 때. 사용하지 말 것: 실시간 최근 공시가 필요하면 list_live_filings, 본문이 필요하면 read_filing을 사용하세요.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `limit` | integer | - | 최대 반환 건수 (기본 20) |

**질문 유형**: 공시, 종합

### get_evidence (priority: 55, category: company)

공시 원문의 증거 블록을 검색합니다. topic의 실제 텍스트/테이블 블록을 기간별로 조회합니다. 사용 시점: 주장의 근거를 원문에서 찾을 때, 리스크/전략 분석에서 원문 인용이 필요할 때. period를 비워두면 최신 기간 우선으로 반환합니다. EDGAR topic 예: '10-K::item1ARiskFactors', DART topic 예: 'riskFactor'.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `topic` | string | O | 조회할 topic (예: riskFactor, businessOverview, 10-K::item1Bu... |
| `period` | string | - | 특정 기간 (예: 2024Q4, 2023Q4). 비워두면 최신 기간 우선 |

**질문 유형**: 리스크, 공시, 사업

### analyze_supply_risk (priority: 55, category: analysis)

공급망 리스크를 종합 평가합니다: 공급사/고객사 집중도, 재무 건전성, 원재료 관련 공시. 사용 시점: '공급망 위험', '거래처 집중도', '원재료 리스크', '고객 의존도' 관련 질문. supply chain 분석 + insight 건전성 + 원재료/리스크 공시 텍스트를 결합합니다.

**질문 유형**: 리스크, 종합

### get_summary (priority: 55, category: finance)

데이터의 요약 통계(평균, 최솟값, 최댓값, 표준편차, CAGR, 추세)를 계산합니다. 사용 시점: 전반적 데이터 개요, 장기 추세 요약이 필요할 때. 사용하지 말 것: 특정 연도 수치가 필요하면 get_data, 비율은 compute_ratios를 사용하세요.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `module_name` | string | O | 분석할 모듈명 (예: IS, BS, dividend) |

### custom_ratio (priority: 55, category: finance)

사용자 정의 재무비율을 계산합니다. 분자/분모 계정명을 지정하면 기간별 비율(%)을 반환합니다. 사용자가 '연구개발비/매출 비율', '인건비/영업이익' 같은 커스텀 비율을 요청할 때 사용하세요.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `numerator` | string | O | 분자 계정명 (예: research_development) |
| `denominator` | string | O | 분모 계정명 (예: revenue) |
| `label` | string | - | 결과 컬럼 라벨 |

**질문 유형**: 건전성, 수익성

### monte_carlo (priority: 55, category: valuation)

Monte Carlo 시뮬레이션으로 매출/영업이익/FCF의 확률 분포(5th~95th 백분위)를 산출합니다. 10,000회 반복으로 기업 실적의 변동성과 위험을 정량화합니다. 사용 시점: 단일 점 추정이 아닌 확률적 범위로 실적 예측이 필요할 때.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `scenario` | string | - | 기반 거시경제 시나리오 (baseline/adverse/china_slowdown/rate_hike/s... |
| `iterations` | string | - | 시뮬레이션 반복 횟수 (기본 10000) |

**질문 유형**: 리스크, 투자

### get_runtime_capabilities (priority: 55, category: meta)

DartLab UI 대화에서 실제로 가능한 기능 범위를 요약합니다. EDGAR에서 더 받을 수 있는 데이터, OpenAPI 범위, GPT/Codex 연결 시 가능한 코딩 범위를 물을 때 우선 사용하세요.

### show_chart (priority: 55, category: ui)

차트를 생성하여 사용자에게 표시합니다. chart_type: trend(추세), waterfall(폭포), radar(레이더), heatmap(히트맵). 사용자가 '차트로 보여줘', '추세 그래프' 같은 요청을 할 때 사용하세요.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `chart_type` | string | O | 차트 유형 (trend, waterfall, radar, heatmap) |
| `data_module` | string | O | 데이터 소스 모듈명 (예: IS, BS, ratios) |
| `metrics` | string | - | 쉼표 구분 지표 목록 (예: revenue,operating_income) |

### run_monte_carlo (priority: 50, category: analysis)

확률적 시뮬레이션으로 매출/이익의 분포와 신뢰구간을 추정합니다. 사용 시점: '확률 분석', '몬테카를로', '시뮬레이션', '불확실성' 질문.

**질문 유형**: 밸류에이션, 리스크

### get_notes (priority: 50, category: company)

K-IFRS 주석(재무제표 각주)을 조회합니다. 키워드를 지정하면 관련 주석을 검색, 비워두면 전체 주석 topic 목록을 반환합니다. 사용 시점: 회계정책 확인, 우발채무 세부사항, 관계회사 거래, 금융상품 공정가치, 리스 부채 세부. 사용하지 말 것: 재무제표 본문 수치는 get_data(BS/IS/CF)가 적절합니다.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `keyword` | string | - | 검색할 키워드 (예: '우발채무', '리스', '관계회사', '공정가치'). 비워두면 전체 목록 |

**질문 유형**: 리스크, 공시, 종합

### fred_series (priority: 50, category: )

FRED 경제지표 시계열 조회. GDP, 실업률, CPI, 금리 등 80만+ 시리즈 조회 가능. transform으로 YoY/MoM/이동평균 변환 적용 가능.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `series_id` | string | O | FRED 시리즈 ID (예: GDP, UNRATE, CPIAUCSL, FEDFUNDS, SP500) |
| `start` | string | - | 시작일 (YYYY-MM-DD). 생략하면 전체 기간. |
| `end` | string | - | 종료일 (YYYY-MM-DD). 생략하면 최신까지. |
| `transform` | enum(raw, yoy, mom, ma) | - | 변환: raw(원본), yoy(전년비%), mom(전월비%), ma(이동평균). 기본: raw. |
| `window` | integer | - | 이동평균 윈도우 (transform=ma일 때). 기본: 12. |

### fred_search (priority: 50, category: )

FRED 시리즈 검색. 키워드로 관련 경제지표를 찾습니다. 시리즈 ID를 모를 때 사용하세요. 예: 'inflation', 'unemployment', 'housing'.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `query` | string | O | 검색 키워드 (영문). 예: 'GDP', 'consumer price', 'unemployment ra... |
| `limit` | integer | - | 최대 결과 수 (기본: 10). |

### fred_compare (priority: 50, category: )

복수 FRED 시계열을 나란히 비교합니다. normalize_to로 기준일=100 정규화하면 단위가 다른 지표도 추세 비교 가능.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `series_ids` | array | O | 비교할 시리즈 ID 목록 (예: ["GDP", "UNRATE", "FEDFUNDS"]). |
| `start` | string | - | 시작일 (YYYY-MM-DD). |
| `end` | string | - | 종료일 (YYYY-MM-DD). |
| `normalize_to` | string | - | 정규화 기준일 (YYYY-MM-DD). 지정하면 해당 날짜=100 기준. |

### fred_catalog (priority: 50, category: )

FRED 주요 경제지표 카탈로그 조회. 그룹: growth(성장), inflation(물가), rates(금리), employment(고용), markets(시장), housing(주택), money(통화). 그룹 미지정 시 전체 ~50개 핵심 지표 목록 반환.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `group` | enum(growth, inflation, rates, employment, markets, housing, money) | - | 카탈로그 그룹. 생략하면 전체 목록. |

### fred_correlation (priority: 50, category: )

FRED 시계열 간 상관분석. 복수 시리즈의 상관행렬, 특정 쌍의 선행/후행(lead-lag) 관계를 분석합니다. 예: 금리와 실업률의 시차 관계, GDP와 S&P500의 선행/후행 구조.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `series_ids` | array | O | 상관분석할 시리즈 ID 목록 (2개 이상). |
| `start` | string | - | 시작일 (YYYY-MM-DD). |
| `end` | string | - | 종료일 (YYYY-MM-DD). |
| `lead_lag_pair` | array | - | 선행/후행 분석 대상 쌍 (예: ["FEDFUNDS", "UNRATE"]). 선택사항. |
| `max_lag` | integer | - | 선행/후행 최대 시차 (기본: 12). |

### get_openapi_capabilities (priority: 50, category: global)

DART/EDGAR OpenAPI surface를 요약합니다. 사용자가 OpenDart, OpenEdgar, 공개 API로 뭘 할 수 있는지 물을 때 먼저 호출하세요.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `market` | string | - | all, dart, edgar 중 하나 |

### create_chart (priority: 50, category: analysis)

기업의 재무 데이터를 차트로 시각화합니다. 매출 추이, 수익성, 현금흐름, 배당, 인사이트 레이더 등을 ChartSpec JSON으로 생성합니다. 사용자가 '차트 보여줘', '매출 추이 그래프', '시각화' 같은 요청을 할 때 사용하세요.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `chart_type` | enum(auto, revenue_trend, cashflow, balance_sheet, profitability, dividend, insight_radar, ratio_sparklines...) | - | 차트 유형. auto는 사용 가능한 모든 차트를 자동 생성. revenue_trend=손익추이, cas... |

### show_comparison (priority: 50, category: ui)

기간간 비교 뷰를 표시합니다. 사용자가 '기간 비교', '전년 대비 보여줘' 같은 요청을 할 때 사용하세요.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `topics` | string | O | 쉼표 구분 topic 목록 (예: BS,IS,CF) |
| `periods` | string | - | 쉼표 구분 기간 목록 (예: 2023Q4,2024Q4). 비워두면 최근 2개 |

### open_comparison_view (priority: 50, category: ui)

두 종목을 좌우 비교하는 뷰를 엽니다. 사용자가 'A vs B 비교', '두 회사 비교해줘' 같은 요청을 할 때 사용하세요.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `company_a` | string | O | 첫 번째 종목 (코드 또는 이름) |
| `company_b` | string | O | 두 번째 종목 (코드 또는 이름) |
| `topics` | string | - | 비교할 topic 목록 (쉼표 구분, 예: BS,IS,ratios) |

### show_block (priority: 45, category: company)

sections의 특정 topic/block 데이터를 조회합니다. block=null이면 블록 목차(block, type, source, preview)를 반환. block=N이면 해당 블록의 실제 데이터(text 또는 수평화 table)를 반환. get_sections로 topic 목록을 확인한 뒤 사용하세요.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `topic` | string | O | topic명 (예: companyOverview, dividend, BS) |
| `block` | integer | - | blockOrder (null이면 블록 목차, 숫자면 해당 블록 데이터) |

**질문 유형**: 공시

### run_codex_task (priority: 45, category: coding)

Codex CLI에 현재 워크스페이스 코드 작업을 위임합니다. 명시적인 코드 수정, 리팩터링, 테스트 보강, 리뷰 요청에서만 사용하세요. workspace-write sandbox를 사용하면 실제 파일이 수정될 수 있습니다.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `prompt` | string | O | Codex에 전달할 코드 작업 지시문 |
| `sandbox` | string | - | read-only, workspace-write, danger-full-access 중 하나 |
| `model` | string | - | Codex CLI에 전달할 모델명. 비우면 CLI 기본값 사용 |
| `timeout_seconds` | integer | - | 최대 대기 시간(초) |

### render_dashboard (priority: 45, category: ui)

위젯을 조합하여 동적 대시보드를 구성합니다. 사용자가 '대시보드 보여줘', '종합 현황판' 같은 요청을 할 때 사용하세요.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `widgets` | string | O | 쉼표 구분 위젯 목록 (예: chart:trend,chart:radar,table:BS,comparison) |
| `title` | string | - | 대시보드 제목 |

### chart (priority: 40, category: ui)

UI 차트/뷰어 제어 — 차트 생성, 뷰어 이동.

**Actions:**

| action | 설명 |
|--------|------|
| `navigate` | 뷰어 특정 위치로 이동 (target 필수). 예: chart(action='navigate', target='businessOverview') |
| `chart` | 차트 생성 (chartType, module 선택). 예: chart(action='chart', chartType='auto') |

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `target` | string | - | 이동할 topic/위치 (action=navigate일 때) |
| `chartType` | string | - | 차트 종류 (action=chart일 때) |
| `module` | string | - | 데이터 모듈 (action=chart일 때) |

**질문 유형**: 종합

### export_to_excel (priority: 40, category: export)

기업 데이터를 Excel(.xlsx) 파일로 내보냅니다. modules: 쉼표 구분 시트 선택 (IS,BS,CF,ratios,dividend,audit,employee,executive 등 Company의 모든 property). 비워두면 데이터가 있는 모든 모듈 자동 포함.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `modules` | string | - | 포함할 시트 (쉼표 구분, 예: 'IS,BS,ratios,dividend'). 비워두면 전체. |

### batch_query (priority: 40, category: company)

복수 종목에 동일한 topic을 일괄 조회하여 비교합니다. 사용자가 '삼성전자와 SK하이닉스 재무 비교', '여러 종목 배당 비교' 같은 요청을 할 때 사용하세요. codes는 쉼표로 구분된 종목코드(최대 10개), topic은 조회할 데이터 모듈입니다.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `codes` | string | O | 쉼표로 구분된 종목코드 (예: 005930,000660,035420) |
| `topic` | string | - | 조회할 topic (예: BS, IS, ratios, companyOverview) |

**질문 유형**: 종합

### call_edgar_openapi (priority: 40, category: global)

EDGAR OpenAPI를 직접 호출합니다. action 예시: search, company, submissions, filings, company_facts, company_concept, frame.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `identifier` | string | - | ticker 또는 CIK |
| `query` | string | - | search용 검색어 |
| `forms` | string | - | 쉼표 구분 form 목록 예: 10-K,10-Q |
| `since` | string | - | 시작일 |
| `until` | string | - | 종료일 |
| `taxonomy` | string | - | taxonomy 예: us-gaap |
| `tag` | string | - | tag 예: RevenueFromContractWithCustomerExcludingAssessedTax |
| `unit` | string | - | frame unit 예: USD |
| `period` | string | - | frame period 예: CY2024Q4I |

### run_coding_task (priority: 40, category: coding)

표준 coding runtime을 통해 워크스페이스 코드 작업을 실행합니다. backend를 바꾸면 미래에 Codex 외 다른 coding backend도 같은 인터페이스로 호출할 수 있습니다.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `prompt` | string | O | coding backend에 전달할 코드 작업 지시문 |
| `backend` | string | - | 사용할 coding backend 이름. 현재 기본값은 codex |
| `sandbox` | string | - | read-only, workspace-write, danger-full-access 중 하나 |
| `model` | string | - | backend에 전달할 모델명. 비우면 backend 기본값 사용 |
| `timeout_seconds` | integer | - | 최대 대기 시간(초) |

### highlight_section (priority: 40, category: ui)

특정 섹션에서 키워드를 하이라이트합니다. 사용자가 특정 텍스트를 찾거나 강조하고 싶을 때 사용하세요.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `topic` | string | O | 대상 topic (예: riskFactor, businessOverview) |
| `keyword` | string | O | 하이라이트할 키워드 |

### export_with_template (priority: 35, category: export)

저장된 템플릿으로 Excel 파일을 생성합니다. 템플릿 ID 예시: preset_full(전체), preset_summary(요약), preset_governance(지배구조). 사용자가 만든 커스텀 템플릿도 ID로 사용 가능합니다.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `template_id` | string | O | 사용할 템플릿 ID (예: preset_full, preset_summary, t_1234567890) |

### get_topic_coverage (priority: 35, category: company)

topic의 기간 커버리지 요약을 조회합니다. 몇 기간 데이터가 있는지, text/table 여부, 총 글자 수를 확인합니다. 사용 시점: 분석 전에 데이터 범위를 파악할 때, 특정 topic이 언제부터 공시되는지 확인할 때. topic을 비워두면 전체 topic의 커버리지를 반환합니다.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `topic` | string | - | 조회할 topic (비워두면 전체). 부분 매칭 지원 (예: 'risk') |

**질문 유형**: 공시

### openapi_save (priority: 35, category: global)

DART/EDGAR OpenAPI saver를 실행해 로컬 parquet를 생성합니다. DART dataset: finance, report, filings, xbrl. EDGAR dataset: docs, finance.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `market` | string | O | dart 또는 edgar |
| `identifier` | string | O | 회사명/종목코드/ticker/CIK |
| `dataset` | string | O | 저장할 데이터 종류 |
| `start` | string | - | DART 시작 연도/일자 |
| `end` | string | - | DART 종료 연도/일자 |
| `quarter` | integer | - | DART 분기 |
| `since_year` | integer | - | EDGAR docs 시작 연도 |
| `full` | boolean | - | DART finance 전체 계정 |
| `categories` | string | - | DART report 카테고리 목록 |

### pin_insight (priority: 35, category: ui)

핵심 인사이트를 사이드바에 고정합니다. 분석 중 발견한 중요 사항을 사용자가 쉽게 참조할 수 있도록 핀합니다.

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `insight` | string | O | 고정할 인사이트 텍스트 |
| `category` | string | - | 카테고리 (risk, financial, valuation, general) |
| `priority` | string | - | 중요도 (high, normal, low) |

### create_template (priority: 30, category: export)

Excel 내보내기 템플릿을 생성합니다. 시트 구성을 JSON으로 정의하면 저장되어 다음에도 재사용 가능합니다. 프리셋: preset_full(전체), preset_summary(요약), preset_governance(지배구조).

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `name` | string | O | 템플릿 이름 (예: '내 분석 양식') |
| `sheets_json` | string | O | 시트 목록 JSON. 예: [{"source":"IS","label":"손익계산서"},{"source"... |

### list_templates (priority: 30, category: export)

저장된 Excel 내보내기 템플릿 목록을 조회합니다. 프리셋과 사용자 커스텀 템플릿을 모두 포함합니다.

### download_data (priority: 30, category: global)

데이터를 다운로드합니다. stock_code를 지정하면 해당 종목만, 비워두면 카테고리 전체를 다운로드합니다. category: docs(공시문서), finance(재무), report(정기보고서), edgarDocs(미국 공시문서, ticker 필요).

**Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `stock_code` | string | - | 종목코드 또는 ticker (비워두면 전체) |
| `category` | string | - | 카테고리 (docs, finance, report, edgarDocs) |

### get_coding_runtime_status (priority: 30, category: meta)

현재 등록된 coding backend와 가용 상태를 조회합니다. 아직 provider와 분리된 코드 작업 런타임의 상태를 확인할 때 사용하세요.

### data_status (priority: 25, category: global)

로컬에 저장된 데이터 현황(카테고리별 파일 수)을 조회합니다. '데이터 몇 개 있어?', '어떤 데이터가 있지?' 같은 질문에 사용하세요.

---

## Scan Axis (11개 축)

`dartlab.scan(axis, target)` 형태로 전종목 횡단분석.

| 축 | 한글 | 설명 | target 파라미터 | 필수 | 반환타입 |
|----|------|------|----------------|------|---------|
| `governance` | 거버넌스 | 지배구조 (지분율, 사외이사, 보수비율, 감사의견) | stockCode 필터 | - | DataFrame |
| `workforce` | 인력/급여 | 직원수, 평균급여, 성장률, 고액보수 | stockCode 필터 | - | DataFrame |
| `capital` | 주주환원 | 배당, 자사주, 증자/감자, 환원 분류 | stockCode 필터 | - | DataFrame |
| `debt` | 부채구조 | 사채만기, 부채비율, ICR, 위험등급 | stockCode 필터 | - | DataFrame |
| `account` | 계정 | 전종목 단일 계정 시계열 (매출액, 영업이익 등) | snakeId | O | DataFrame |
| `ratio` | 비율 | 전종목 단일 재무비율 시계열 (ROE, 부채비율 등) | ratioName | O | DataFrame |
| `digest` | 다이제스트 | 시장 전체 공시 변화 다이제스트 | stockCode 필터 | - | DataFrame |
| `network` | 네트워크 | 상장사 관계 네트워크 (출자/지분/계열) | stockCode 필터 | - | dict |
| `cashflow` | 현금흐름 | OCF/ICF/FCF + 현금흐름 패턴 분류 (8종) | stockCode 필터 | - | DataFrame |
| `audit` | 감사리스크 | 감사의견, 감사인변경, 특기사항 종합 리스크 | stockCode 필터 | - | DataFrame |
| `insider` | 내부자지분 | 최대주주 지분변동, 자기주식 현황, 경영권 안정성 | stockCode 필터 | - | DataFrame |

**한글 별칭:**

- `account`: 계정
- `audit`: 감사, 감사리스크
- `capital`: 주주환원, 배당
- `cashflow`: 현금흐름, 현금
- `debt`: 부채
- `digest`: 다이제스트, 변화
- `governance`: 거버넌스, 지배구조
- `insider`: 내부자, 지분
- `network`: 네트워크, 관계
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

## 질문 유형별 도구 매핑

registerTool()의 questionTypes + priority에서 자동 생성.

| 질문 유형 | 우선 도구 (priority 순) |
|----------|----------------------|
| 건전성 | explore(95) > show_topic(95) > finance(90) > get_data(90) > get_insight(85) > list_topics(85) > analyze(80) > compute_ratios(80) > get_scan_data(70) > get_ratio_series(65) > custom_ratio(55) |
| 공시 | explore(95) > show_topic(95) > list_topics(85) > search_dart_filings(85) > get_report_data(75) > get_dart_filing_text(75) > diff_topic(70) > call_dart_openapi(70) > read_filing(66) > get_disclosure_changes(65) > analyze_disclosure_change(65) > list_live_filings(64) > openapi(60) > trace_topic(60) > get_sections(55) > list_filings(55) > get_evidence(55) > get_notes(50) > show_block(45) > get_topic_coverage(35) |
| 규제 | research(65) |
| 뉴스 | research(65) |
| 동향 | research(65) |
| 리스크 | explore(95) > show_topic(95) > finance(90) > get_data(90) > get_insight(85) > list_topics(85) > analyze(80) > run_audit(75) > diff_topic(70) > detect_anomalies(70) > read_filing(66) > research(65) > get_disclosure_changes(65) > analyze_disclosure_change(65) > economic_forecast(65) > trace_topic(60) > stress_test(60) > run_stress_test(55) > get_evidence(55) > analyze_supply_risk(55) > monte_carlo(55) > run_monte_carlo(50) > get_notes(50) |
| 배당 | explore(95) > show_topic(95) > finance(90) > get_data(90) > list_topics(85) > analyze(80) > get_report_data(75) > diff_topic(70) |
| 밸류에이션 | get_current_price(80) > run_valuation(75) > get_consensus(75) > run_forecast(70) > run_monte_carlo(50) |
| 변화 | get_disclosure_changes(65) |
| 사업 | explore(95) > show_topic(95) > list_topics(85) > search_dart_filings(85) > get_dart_filing_text(75) > diff_topic(70) > call_dart_openapi(70) > read_filing(66) > list_live_filings(64) > get_sections(55) > get_evidence(55) |
| 산업 | research(65) |
| 성장성 | explore(95) > show_topic(95) > finance(90) > get_data(90) > list_topics(85) > analyze(80) > forecast_revenue(80) > run_forecast(70) > diff_topic(70) > compute_growth(70) > forecast(70) > analyze_disclosure_change(65) > yoy_analysis(65) > get_ratio_series(65) > proforma_forecast(65) |
| 수익성 | explore(95) > show_topic(95) > finance(90) > get_data(90) > get_insight(85) > list_topics(85) > analyze(80) > compute_ratios(80) > get_ratio_series(65) > custom_ratio(55) |
| 실시간 | research(65) |
| 종합 | explore(95) > show_topic(95) > finance(90) > get_data(90) > get_insight(85) > list_topics(85) > analyze(80) > compute_ratios(80) > run_audit(75) > run_valuation(75) > get_company_info(75) > market(70) > get_sector_info(70) > diff_topic(70) > run_simulation(70) > get_scan_data(70) > read_filing(66) > research(65) > get_disclosure_changes(65) > analyze_disclosure_change(65) > list_live_filings(64) > system(60) > get_rank(60) > get_digest(60) > list_filings(55) > analyze_supply_risk(55) > get_notes(50) > chart(40) > batch_query(40) |
| 지배구조 | explore(95) > show_topic(95) > list_topics(85) > analyze(80) > get_report_data(75) > get_scan_data(70) > network_graph(65) > trace_topic(60) |
| 투자 | explore(95) > show_topic(95) > list_topics(85) > intrinsic_value(85) > price_target(85) > analyze(80) > forecast_revenue(80) > get_current_price(80) > run_valuation(75) > scenario(75) > get_consensus(75) > market(70) > get_sector_info(70) > run_forecast(70) > forecast(70) > run_simulation(70) > economic_forecast(65) > proforma_forecast(65) > get_fund_flow(65) > sensitivity(60) > get_price_history(60) > run_stress_test(55) > monte_carlo(55) |

**도구 연쇄 패턴:**

- **explore**: 연쇄 사용: finance로 숫자를 먼저 확인한 후, 이 도구로 공시 원문에서 맥락과 근거를 보강하세요.
- **finance**: 연쇄 사용: 숫자 확인 후 explore(action='search')로 공시 원문에서 변화 원인을 찾으세요.

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

### 핵심 property

| property | 반환 | 설명 |
|----------|------|------|
| `BS` | DataFrame | 재무상태표 |
| `IS` | DataFrame | 손익계산서 |
| `CIS` | DataFrame | 포괄손익계산서 |
| `CF` | DataFrame | 현금흐름표 |
| `sections` | DataFrame | merged topic x period company table |
| `ratios` | RatioResult | 재무비율 |
| `index` | DataFrame | 회사 구조 인덱스 |
| `insights` | AnalysisResult | 7영역 인사이트 등급 |

### 핵심 메서드

| 메서드 | 설명 |
|--------|------|
| `show(topic)` | topic payload 조회 |
| `trace(topic)` | source provenance 조회 |
| `diff()` | 기간간 변화 감지 |
| `filings()` | 공시 문서 목록 |

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
