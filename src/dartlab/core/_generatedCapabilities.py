"""런타임 capabilities 카탈로그 (자동 생성).

이 파일은 scripts/generateSpec.py가 자동 생성합니다. 직접 수정 금지.
"""

CAPABILITIES: dict[str, dict] = {
    "ChartResult": {
        "kind": "class",
        "summary": "chart() 반환 객체 — 시각화 + 렌더링."
    },
    "Company": {
        "aicontext": "개별 종목 분석의 시작점. explore/finance/analysis 수퍼툴이 이 객체를 소비.\n\"삼성전자 분석해줘\" → Company(\"005930\") 생성 → briefing → LLM 해석.",
        "capabilities": "종목코드 (\"005930\"), 회사명 (\"삼성전자\"), 영문 ticker (\"AAPL\") 모두 지원\ncanHandle() 체인: provider priority 순 자동 라우팅 (DART → EDGAR)\n새 국가 추가 시 이 파일 수정 불필요 — provider 패키지만 추가\n핵심 인터페이스: show(topic) / index / trace(topic) / diff()\nnamespace: docs (원문) / finance (숫자) / report (정형공시) / profile (merge)\n바로가기: BS/IS/CF/CIS, ratios, ratioSeries, timeseries\n메타: sections, topics, filings(), insights, market, currency",
        "guide": "\"삼성전자 재무제표\" -> c = Company(\"005930\"); c.IS\n\"사업 개요 보여줘\" -> c.show(\"businessOverview\")\n\"어떤 데이터 있어?\" -> c.index 또는 c.topics\n\"출처 추적\" -> c.trace(\"revenue\")\n\"기간 변화\" -> c.diff()\n\"인사이트 등급\" -> c.insights\n\"리뷰 보고서\" -> c.review()\n\"Apple 분석\" -> Company(\"AAPL\") (자동 EDGAR 라우팅)",
        "kind": "function",
        "requires": "DART: 사전 다운로드 데이터 (dartlab.downloadAll() 또는 자동 다운로드).\nEDGAR: 인터넷 연결 (On-demand 수집).",
        "seeAlso": "search: 종목 검색 (종목코드 모를 때)\nscan: 전종목 횡단분석 (기업 비교)\nanalysis: 14축 전략분석\ngather: 주가/수급/거시 데이터",
        "summary": "종목코드/회사명/ticker → 적절한 Company 인스턴스 생성."
    },
    "Company.BS": {
        "aicontext": "ask()/chat()에서 자산/부채/자본 구조 분석 컨텍스트",
        "capabilities": "XBRL 정규화 재무상태표 (finance 우선)\ndocs 서술형 fallback\n최대 10년 분기별 시계열",
        "guide": "\"재무상태표 보여줘\" → c.BS\n\"자산/부채 구조\" → c.BS로 확인\n\"유동비율은?\" → c.ratios 또는 c.BS에서 계산",
        "kind": "property",
        "requires": "데이터: finance 또는 docs (자동 다운로드)",
        "seeAlso": "IS: 손익계산서 (수익성 분석)\nCF: 현금흐름표 (현금창출력)\nratios: 재무비율 (BS 기반 안정성 비율 포함)\nselect: 특정 계정만 추출 + 시각화",
        "summary": "재무상태표 (Balance Sheet) — 계정명 × 기간 DataFrame."
    },
    "Company.CF": {
        "aicontext": "ask()/chat()에서 현금창출력/투자/재무활동 분석 컨텍스트",
        "capabilities": "XBRL 정규화 현금흐름표 (finance 우선)\ndocs 서술형 fallback\n영업/투자/재무 활동 분류",
        "guide": "\"현금흐름표 보여줘\" → c.CF\n\"영업현금흐름 추이\" → c.select(\"CF\", [\"영업활동으로인한현금흐름\"])\n\"FCF 확인\" → c.ratios에서 FCF 비율 또는 c.CF에서 직접 계산",
        "kind": "property",
        "requires": "데이터: finance 또는 docs (자동 다운로드)",
        "seeAlso": "IS: 손익계산서 (발생주의 vs 현금주의 비교)\nBS: 재무상태표 (현금성자산 확인)\nratios: 재무비율 (현금흐름 관련 비율 포함)",
        "summary": "현금흐름표 (Cash Flow Statement) — 계정명 × 기간 DataFrame."
    },
    "Company.CIS": {
        "aicontext": "ask()/chat()에서 기타포괄손익/총포괄이익 분석 컨텍스트",
        "capabilities": "XBRL 정규화 포괄손익계산서 (finance 우선)\ndocs 서술형 fallback\n기타포괄손익 항목 포함",
        "guide": "\"포괄손익계산서 보여줘\" → c.CIS\n\"기타포괄손익 항목은?\" → c.CIS",
        "kind": "property",
        "requires": "데이터: finance 또는 docs (자동 다운로드)",
        "seeAlso": "IS: 일반 손익계산서 (당기순이익까지)\nSCE: 자본변동표 (포괄손익이 자본에 미치는 영향)",
        "summary": "포괄손익계산서 (Comprehensive Income Statement) — 계정명 × 기간 DataFrame."
    },
    "Company.IS": {
        "aicontext": "ask()/chat()에서 수익성/매출 구조 분석 컨텍스트",
        "capabilities": "XBRL 정규화 손익계산서 (finance 우선)\ndocs 서술형 fallback\n최대 10년 분기별 시계열",
        "guide": "\"손익계산서 보여줘\" → c.IS\n\"매출/영업이익 추이\" → c.IS 또는 c.select(\"IS\", [\"매출액\", \"영업이익\"])\n\"수익 구조 분석\" → c.IS + c.analysis(\"수익구조\")",
        "kind": "property",
        "requires": "데이터: finance 또는 docs (자동 다운로드)",
        "seeAlso": "BS: 재무상태표 (자산/부채 구조)\nCF: 현금흐름표 (실제 현금 기반)\nCIS: 포괄손익계산서 (기타포괄손익 포함)\nselect: 특정 계정 추출 + 시각화",
        "summary": "손익계산서 (Income Statement) — 계정명 × 기간 DataFrame."
    },
    "Company.SCE": {
        "aicontext": "ask()/chat()에서 자본 구조 변동 분석 컨텍스트",
        "capabilities": "XBRL 정규화 자본변동표\n연결 기준 자본 구성요소별 변동\n연도별 시계열",
        "guide": "\"자본변동표 보여줘\" → c.SCE\n\"자본 구성 변화\" → c.SCE",
        "kind": "property",
        "requires": "데이터: finance (자동 다운로드)",
        "seeAlso": "sceMatrix: 3차원 매트릭스 형태 (원인별 상세 추적)\nCIS: 포괄손익계산서 (자본변동의 원천)\nBS: 재무상태표 (자본 잔액)",
        "summary": "자본변동표 (Statement of Changes in Equity) — 계정명 × 연도 DataFrame."
    },
    "Company.analysis": {
        "aicontext": "ask()/chat()에서 분석 결과를 컨텍스트로 주입\nreview/reviewer가 내부적으로 analysis 결과를 소비",
        "capabilities": "14축 분석: 수익구조, 자금조달, 자산구조, 현금흐름, 수익성, 성장성, 안정성, 효율성, 종합평가, 이익품질, 비용구조, 자본배분, 투자효율, 재무정합성\n축 없이 호출 시 14축 가이드 반환\n개별 축 분석 시 Company 바인딩 (self 자동 전달)",
        "guide": "\"14축 분석 뭐가 있어?\" → c.analysis() (가이드 반환)\n\"수익구조 분석해줘\" → c.analysis(\"수익구조\")\n\"안정성 분석\" → c.analysis(\"안정성\")",
        "kind": "method",
        "requires": "데이터: finance (자동 다운로드)",
        "seeAlso": "review: 14축 분석을 14개 섹션 보고서로 조합\ninsights: 7영역 등급 요약 (analysis보다 요약적)\nratios: 재무비율 시계열 (analysis의 입력 데이터)",
        "summary": "재무제표 완전 분석 — 14축, 단일 종목 심층."
    },
    "Company.annual": {
        "aicontext": "연도 단위 추세 분석 — forecast, ratioSeries의 기초 데이터",
        "capabilities": "BS/IS/CF 계정별 연도 시계열\n분기 데이터를 연도 단위로 집계\nfinance XBRL 정규화 기반",
        "guide": "\"연���별 시계열\" → c.annual\n\"연간 매출 추이\" → series, years = c.annual; series[\"IS\"][\"sales\"]",
        "kind": "property",
        "requires": "데이터: finance (자동 다운로드)",
        "seeAlso": "timeseries: 분기별 시계열 (더 세밀)\ncumulative: 분기별 누적 시계열\nratioSeries: 연도별 재무비율 시계열",
        "summary": "연도별 시계열 (연결 기준)."
    },
    "Company.ask": {
        "aicontext": "Tier 1 시스템 주도 분석. 질문 분류 후 엔진이 계산한 결과를\n컨텍스트로 조립하여 LLM이 해석/설명만 수행.",
        "capabilities": "엔진 계산 결과를 컨텍스트로 조립하여 LLM에 전달\n질문 분류 기반 분석 패키지 자동 선택 (financial, valuation, risk 등)\n멀티 provider 지원 (openai, ollama, codex 등)\n스트리밍 응답 지원",
        "guide": "\"영업이익률 분석해줘\" → c.ask(\"영업이익률 추세는?\")\n\"AI한테 질문하고 싶어\" → c.ask(\"질문\")\n\"스트리밍으로 답변받기\" → c.ask(\"질문\", stream=True)",
        "kind": "method",
        "requires": "API 키: LLM provider API 키 (OPENAI_API_KEY 등)",
        "seeAlso": "chat: 에이전트 모드 (tool calling 기반 심화 분석)\nreviewer: 구조화된 AI 보고서 (자유 질문이 아닌 섹션별)\nreview: AI 없는 데이터 검토서",
        "summary": "LLM에게 이 기업에 대해 질문."
    },
    "Company.audit": {
        "aicontext": "감사 리스크 종합 평가 — 투자 의사결정의 핵심 안전장치\n감사의견 변경, 계속기업 불확실성은 최고 경고 수준",
        "capabilities": "감사의견 추이 (적정/한정/부적정/의견거절)\n감사인 변경 이력 + 사유\n계속기업 불확실성 플래그\n핵심감사사항 (KAM) 추출\n내부회계관리제도 검토의견",
        "guide": "\"감사의견 확인\" → c.audit()\n\"감사인 바뀌었어?\" → c.audit()[\"auditorChanges\"]\n\"계속기업 의문은?\" → c.audit()[\"goingConcern\"]",
        "kind": "method",
        "requires": "데이터: docs + report (자동 다운로드)",
        "seeAlso": "governance: 지배구조 분석 (감사위원회 구성 포함)\ninsights: 종합 등급 (감사 리스크도 반영)\nreview: 재무정합성 섹션에서 감사 결과 활용",
        "summary": "감사 리스크 종합 분석."
    },
    "Company.canHandle": {
        "kind": "method",
        "summary": "DART 종목코드(6자) 또는 한글 회사명이면 처리 가능."
    },
    "Company.capital": {
        "aicontext": "주주환원 정책 평가 — 배당수익률/성향/자사주 정량 데이터\n시장 횡단 비교로 상대적 환원 수준 판단",
        "capabilities": "배당수익률 + 배당성향 추이\n자사주 매입/소각 이력\n총주주환원율 (배당 + 자사주)\n시장 전체 주주환원 횡단 비교",
        "guide": "\"배당 정보\" → c.capital() 또는 c.show(\"dividend\")\n\"주주환원율은?\" → c.capital()\n\"전체 상장사 배당 비교\" → c.capital(\"all\")",
        "kind": "method",
        "requires": "데이터: DART 정기보고서 (자동 수집)",
        "seeAlso": "show: c.show(\"dividend\")로 docs 기반 배당 상세\nsceMatrix: 자본변동표 (배당/자사주가 자본에 미치는 영향)\ndebt: 부채 구조 (자본 정책의 다른 면)",
        "summary": "주주환원 분석 (배당, 자사주, 총환원율)."
    },
    "Company.chat": {
        "aicontext": "Tier 2 에이전트 모드. Tier 1 결과를 본 LLM이 부족하다고 판단하면\n저수준 tool(시계열 조회, 공시 검색 등)을 직접 호출하여 심화 분석.",
        "capabilities": "Tier 2 LLM 주도 분석 (tool calling)\nLLM이 부족한 정보를 자율적으로 도구 호출하여 보충\n원본 시계열, 공시 텍스트 검색, 복수 기업 비교 등 심화 탐색\n멀티 턴 대화 지원",
        "guide": "\"심층 분석해줘\" → c.chat(\"질문\")\n\"AI가 직접 데이터 찾아서 분석\" → c.chat(\"질문\")\n\"여러 단계 분석 필요한 질문\" → c.chat(\"복합 질문\")",
        "kind": "method",
        "requires": "API 키: tool calling 지원 LLM provider API 키",
        "seeAlso": "ask: 단일 턴 질문 (chat보다 빠르지만 덜 심층)\nreviewer: 구조화된 AI 보고서",
        "summary": "에이전트 모드: LLM이 도구를 선택하여 심화 분석."
    },
    "Company.codeName": {
        "kind": "method",
        "summary": "종목코드 → 회사명 변환."
    },
    "Company.contextSlices": {
        "aicontext": "ask()/chat()의 시스템 프롬프트에 직접 주입되는 데이터\nLLM이 소비하는 최종 형태의 컨텍스트",
        "capabilities": "retrievalBlocks를 LLM 컨텍스트 윈도우에 맞게 슬라이싱\n토큰 예산 내에서 최대한 많은 관련 정보를 담는 압축 포맷\ntopic/period 기준 우선순위 정렬",
        "guide": "\"LLM에 들어가는 컨텍스트\" → c.contextSlices\n\"AI가 보는 데이터\" → c.contextSlices",
        "kind": "property",
        "requires": "데이터: docs (자동 다운로드)",
        "seeAlso": "retrievalBlocks: 슬라이싱 전 전체 retrieval 블록\nask: contextSlices를 내부적으로 소비하는 AI 질문 인터페이스",
        "summary": "LLM 투입용 context slice DataFrame."
    },
    "Company.cumulative": {
        "aicontext": "Q4 누적이 연간 실적 — 연중 진행률 파악에 활용",
        "capabilities": "IS/CF 계정별 분기 누적(YTD) 시계열\nQ1→Q2→Q3→Q4 누적 합산\nfinance XBRL 정규화 기반",
        "guide": "\"누적 시계열\" → c.cumulative\n\"올해 누적 매출\" → series, periods = c.cumulative",
        "kind": "property",
        "requires": "데이터: finance (자동 다운로드)",
        "seeAlso": "timeseries: 분기별 standalone (누적이 아닌 개별 분기)\nannual: 연도별 집계",
        "summary": "분기별 누적 시계열 (연결 기준)."
    },
    "Company.currency": {
        "kind": "property",
        "seeAlso": "market: 시장 코드",
        "summary": "통화 코드 (DART 제공자는 항상 KRW)."
    },
    "Company.debt": {
        "aicontext": "부채 구조/건전성 정량 평가 — 차입금 의존도, 만기 구조\n시장 횡단 비교로 상대적 재무 안정성 판단",
        "capabilities": "총차입금 + 순차입금 규모\n부채비율 + 차입금의존도\n단기/장기 차입금 비율\n시장 전체 부채 구조 횡단 비교",
        "guide": "\"부채 구조 분석\" → c.debt()\n\"부채비율은?\" → c.debt() 또는 c.ratios\n\"전체 상장사 부채 비교\" → c.debt(\"all\")",
        "kind": "method",
        "requires": "데이터: DART 정기보고서 (자동 수집)",
        "seeAlso": "BS: 재무상태표 (부채 원본 데이터)\nratios: 재무비율 (부채비율 포함)\ncapital: 주주환원 (자본 정책의 다른 면)",
        "summary": "부채 구조 분석 (차입금, 부채비율, 만기 구조)."
    },
    "Company.diff": {
        "aicontext": "기간간 공시 변경 감지 — 사업 방향 전환, 리스크 요인 변화 탐지\nwatch()보다 세밀한 줄 단위 변경 추적",
        "capabilities": "전체 topic 변경 요약 (변경량 스코어링)\n특정 topic 기간별 변경 이력\n두 기간 줄 단위 diff (추가/삭제/변경)",
        "guide": "\"공시에서 뭐가 바뀌었어?\" → c.diff()\n\"사업개요 변경 이력\" → c.diff(\"businessOverview\")\n\"2023 vs 2024 차이\" → c.diff(\"businessOverview\", \"2023\", \"2024\")",
        "kind": "method",
        "requires": "데이터: docs (2개 이상 기간 필요)",
        "seeAlso": "watch: 변화 중요도 스코어링 (diff보다 요약적)\nkeywordTrend: 키워드 ��도 추이 (텍스트 변화의 다른 관점)\nshow: 특정 기간 원문 조회",
        "summary": "기간간 텍스트 변경 비교."
    },
    "Company.disclosure": {
        "aicontext": "특정 유형 공시 존재 여부 확인 → 분석 범위 동적 결정\n최근 공시 빈도/유형 패턴으로 기업 이벤트 감지",
        "capabilities": "전체 공시유형 조회 (정기, 주요사항, 발행, 지분, 외부감사 등)\n기간, 유형, 키워드 필터링\n최종보고서만 필터 (정정 이전 제외)",
        "guide": "\"최근 공시 뭐 나왔어?\" → c.disclosure(days=30)\n\"주요사항 공시 있어?\" → c.disclosure(type=\"B\")\n\"사업보고서 언제 나왔어?\" → c.disclosure(keyword=\"사업보고서\")",
        "kind": "method",
        "requires": "API 키: DART_API_KEY",
        "seeAlso": "liveFilings: 실시간 최신 공시 (정규화된 포맷)\nreadFiling: 공시 원문 텍스트 읽기\nfilings: 로컬 보유 공시 목록",
        "summary": "OpenDART 전체 공시 목록 조회."
    },
    "Company.filings": {
        "aicontext": "어떤 공시가 보유돼 있는지 확인하여 분석 범위 결정에 활용",
        "capabilities": "로컬에 보유한 공시 문서 목록\n기간별, 문서유형별 정리\nDART 뷰어 링크 포함",
        "guide": "\"이 회사 공시 목록 보여줘\" → c.filings()\n\"어떤 보고서가 있어?\" → c.filings()로 보유 문서 확인",
        "kind": "method",
        "requires": "데이터: docs (자동 다운로드)",
        "seeAlso": "disclosure: OpenDART API 기반 실시간 공시 목록 (로컬 보유가 아닌 전체)\nliveFilings: 최신 공시 실시간 조회\nupdate: 누락 공시 증분 수집",
        "summary": "공시 문서 목록 + DART 뷰어 링크."
    },
    "Company.forecast": {
        "aicontext": "매출 예측 결과를 valuation, simulation과 조합하여 종합 전망 생성\n신뢰구간으로 불확실성 정도 전달",
        "capabilities": "선형회귀 + CAGR + 이동평균 앙상블\n섹터별 성장률 보정\n신뢰구간 (상한/하한) 제공",
        "guide": "\"매출 예측해줘\" → c.forecast()\n\"5년 예측\" → c.forecast(horizon=5)\n\"예측 신뢰구간\" → result.upper, result.lower",
        "kind": "method",
        "requires": "데이터: finance (자동 다운로드)",
        "seeAlso": "valuation: 예측 기반 적정가치 산출\nsimulation: 시나리오별 영향 추정\nannual: 예측의 입력 데이터 (과거 연도별 실적)",
        "summary": "매출 앙상블 예측 (다중 모델 가중 평균)."
    },
    "Company.gather": {
        "aicontext": "ask()/chat()에서 주가/수급/거시 데이터를 컨텍스트로 주입\n기업 분석 시 시장 데이터 보충 자료로 활용",
        "capabilities": "price: OHLCV 주가 시계열 (KR Naver / US Yahoo)\nflow: 외국인/기관 수급 동향 (KR 전용)\nmacro: ECOS(KR) / FRED(US) 거시지표 시계열\nnews: Google News RSS 뉴스 수집\n자동 fallback 체인, circuit breaker, TTL 캐시",
        "guide": "\"주가 데이터\" → c.gather(\"price\")\n\"외국인/기관 수급\" → c.gather(\"flow\")\n\"거시경제 지표\" → c.gather(\"macro\")\n\"뉴스 수집\" → c.gather(\"news\") 또는 c.news()",
        "kind": "method",
        "requires": "price/flow/news: 없음 (공개 API)\nmacro: API 키 -- ECOS_API_KEY (KR) 또는 FRED_API_KEY (US)",
        "seeAlso": "news: 뉴스 전용 단축 메서드\nask: gather 데이터를 컨텍스트로 활용한 AI 분석",
        "summary": "외부 시장 데이터 수집 — 4축 (price/flow/macro/news)."
    },
    "Company.getRatios": {
        "kind": "method",
        "summary": "Deprecated — use ``c.ratios`` property instead."
    },
    "Company.getTimeseries": {
        "kind": "method",
        "summary": "Deprecated — use ``c.timeseries`` property instead."
    },
    "Company.governance": {
        "aicontext": "지배구조 리스크 평가 — 사외이사/감사위원/최대주주 정량 데이터\n시장 횡단 비교로 상대적 거버넌스 수준 판단",
        "capabilities": "사외이사 비율 + 감사위원회 구성\n최대주주 지분율 + 특수관계인\n시장 전체 거버넌스 횡단 비교",
        "guide": "\"지배구조 분석\" → c.governance()\n\"사외이사 비율은?\" → c.governance()\n\"전체 상장사 거버넌스 비교\" → c.governance(\"all\")",
        "kind": "method",
        "requires": "데이터: DART 정기보고서 (자동 수집)",
        "seeAlso": "network: 출자/계열사 관계 (거버넌스의 다른 관점)\naudit: 감사 리스크 (감사위원회와 연관)",
        "summary": "지배구조 분석 (이사회, 감사위원, 최대주주)."
    },
    "Company.index": {
        "aicontext": "LLM이 Company 전체 구조를 파악하는 핵심 진입점\nask()에서 어떤 데이터를 참조할지 결정하는 기초 정보",
        "capabilities": "docs sections + finance + report 전체를 하나의 목차로 통합\n각 항목의 chapter, topic, label, kind, source, periods, shape, preview 제공\nsections 메타데이터 + 존재 확인만으로 구성 (파서 미호출, lazy)\nviewer/렌더러가 소비하는 메타데이터 원천",
        "guide": "\"전체 목차 보여줘\" → c.index\n\"어떤 데이터가 있는지 구조적으로\" → c.index",
        "kind": "property",
        "requires": "데이터: docs/finance/report 중 하나 이상 (자동 다운로드)",
        "seeAlso": "topics: topic 단위 요약 (index보다 간결)\nsections: 전체 sections 지도 (index의 원본)\nprofile: 통합 프로필 접근자",
        "summary": "현재 공개 Company 구조 인덱스 DataFrame -- 전체 데이터 목차."
    },
    "Company.insights": {
        "aicontext": "ask()/chat()에서 재무 건전성 종합 판단의 핵심 데이터\n7영역 등급 + 이상치 + 투자 프로파일을 컨텍스트로 주입",
        "capabilities": "7영역 등급 평가 (실적, 수익성, 성장, 안정성, 현금흐름, 효율, 밸류에이션)\n이상치 자동 탐지 (급변, 임계 초과)\n텍스트 요약 + 투자 프로파일 분류",
        "guide": "\"이 회사 재무 등급은?\" → c.insights.grades()\n\"이상 징후 있어?\" → c.insights.anomalies\n\"투자 프로파일\" → c.insights.profile",
        "kind": "property",
        "requires": "데이터: finance (자동 다운로드)",
        "seeAlso": "analysis: 14축 개별 상세 분석 (insights보다 세밀)\nreview: 14섹션 보고서 (insights를 내부적으로 참조)\nratios: 재무비율 시계열 (insights의 입력 데이터)",
        "summary": "종합 인사이트 분석 (7영역 등급 + 이상치 + 요약)."
    },
    "Company.keywordTrend": {
        "aicontext": "공시 텍스트의 키워드 빈도 변화로 전략 방향 전환 감지\nAI, ESG, 탄소중립 등 트렌드 키워드 모니터링",
        "capabilities": "공시 텍스트에서 키워드 빈도 추이 분석\n54개 내장 키워드 세트 (AI, ESG, 탄소중립 등)\ntopic별 x 기간별 빈도 매트릭스\n복수 키워드 동시 검색",
        "guide": "\"AI 언급 추이\" → c.keywordTrend(\"AI\")\n\"ESG 관련 변화\" → c.keywordTrend(\"ESG\")\n\"전체 키워드 트렌드\" → c.keywordTrend()",
        "kind": "method",
        "requires": "데이터: docs (자동 다운로드)",
        "seeAlso": "diff: 텍스트 줄 단위 변경 비교 (키워드가 아닌 전체 변경)\nwatch: 변화 중요도 스코어링",
        "summary": "공시 텍스트 키워드 빈도 추이 (topic x period x keyword)."
    },
    "Company.listing": {
        "capabilities": "KOSPI + KOSDAQ 전체 상장법인\n종목코드, 종목명, 시장구분, 업종",
        "kind": "method",
        "requires": "데이터: listing (자동 다운로드)",
        "summary": "KRX 전체 상장법인 목록 (KIND 기준)."
    },
    "Company.liveFilings": {
        "aicontext": "최신 공시 모니터링으로 기업 이벤트(배당, 유증, 합병 등) 실시간 감지\nreadFiling()과 조합하여 최신 공시 원문 분석",
        "capabilities": "OpenDART API 실시간 공시 조회\n기간, 건수, 키워드 필터링\n정규화된 컬럼 (docId, filedAt, title, formType 등)",
        "guide": "\"최근 공시 확인해줘\" → c.liveFilings()\n\"이번 주 공시 있어?\" → c.liveFilings(days=7)\n\"배당 관련 공시\" → c.liveFilings(keyword=\"배당\")",
        "kind": "method",
        "requires": "API 키: DART_API_KEY",
        "seeAlso": "disclosure: 과거 전체 공시 이력 조회\nreadFiling: 공시 원문 텍스트 읽기\nwatch: 공시 변화 중요도 스코어링",
        "summary": "OpenDART 기준 실시간 공시 목록 조회."
    },
    "Company.market": {
        "kind": "property",
        "seeAlso": "currency: 통화 코드",
        "summary": "시장 코드 (DART 제공자는 항상 KR)."
    },
    "Company.network": {
        "aicontext": "그룹 계열사/출자 구조 파악 — 지배구조 분석의 기초 데이터\n순환출자 탐지로 거버넌스 리스크 감지",
        "capabilities": "그룹 계열사 목록 (members)\n출자/피출자 연결 + 지분율 (edges)\n순환출자 경로 탐지 (cycles)\nego 서브그래프 (peers)\n인터랙티브 네트워크 시각화 (브라우저)",
        "guide": "\"계열사 관계도\" → c.network() 또는 c.network().show()\n\"같은 그룹 계열사\" → c.network(\"members\")\n\"출자/지분 구조\" → c.network(\"edges\")\n\"순환출자 있어?\" → c.network(\"cycles\")",
        "kind": "method",
        "requires": "데이터: DART 대량보유/임원 공시 (자동 수집)",
        "seeAlso": "governance: 이사회/감사위원/최대주주 분석\ncapital: 주주환원 분석",
        "summary": "관계 네트워크 (지분출자 + 그룹 계열사 지도)."
    },
    "Company.news": {
        "aicontext": "최근 뉴스로 시장 반응, 이슈, 이벤트 파악\nask()/chat()에서 정성적 시장 맥락 보충",
        "capabilities": "Google News RSS 기반 뉴스 수집\n제목, 날짜, 소스, 링크\n기간 조절 가능",
        "guide": "\"최근 뉴스 보여줘\" → c.news()\n\"이번 주 뉴스\" → c.news(days=7)",
        "kind": "method",
        "requires": "없음 (공개 RSS)",
        "seeAlso": "liveFilings: 최신 공시 (뉴스가 아닌 공식 공시)\ngather: 뉴스 포함 4축 외부 데이터 수집",
        "summary": "최근 뉴스 수집."
    },
    "Company.notes": {
        "aicontext": "K-IFRS 주석에서 회계정책, 우발부채, 관계사 거래 등 정성 정보 추출",
        "capabilities": "K-IFRS 재무제표 주석(notes) 데이터 접근\n주석 항목별 조회",
        "guide": "\"주석사항 보여줘\" → c.notes\n\"회계정책 확인\" → c.notes에서 해당 항목 조회",
        "kind": "property",
        "requires": "데이터: HuggingFace finance parquet (자동 다운로드)",
        "seeAlso": "BS: 재무상태표 (주석이 보충하는 본문)\nrawFinance: 재무 원본 데이터",
        "summary": "K-IFRS 주석사항 접근자."
    },
    "Company.priority": {
        "kind": "method",
        "summary": "낮을수록 먼저 시도. DART=10 (기본 provider)."
    },
    "Company.profile": {
        "aicontext": "c.sections는 내부적으로 profile.sections를 반환\n분석/리뷰에서 통합된 데이터를 소비하는 기본 경로",
        "capabilities": "docs sections를 spine으로, finance/report 데이터를 merge하여 통합 뷰 제공\nprofile.sections로 source 우선순위(finance > report > docs) 적용된 sections 접근\nprofile.show(topic)으로 merge된 결과 조회",
        "guide": "\"통합 프로필\" → c.profile\n\"merge된 sections\" → c.profile.sections",
        "kind": "property",
        "requires": "데이터: docs (자동 다운로드). finance/report는 있으면 자동 merge.",
        "seeAlso": "sections: profile.sections의 단축 접근\nshow: profile 기반 topic 데이터 조회",
        "summary": "docs spine + finance/report merge layer -- 통합 프로필 접근자."
    },
    "Company.rank": {
        "aicontext": "시장/섹터 내 상대 위치 파악 — 피어 비교 분석의 기초\nsizeClass로 대형/중형/소형주 분류",
        "capabilities": "전체 시장 내 매출/자산 순위\n섹터 내 상대 순위\n매출 성장률 기반 규모 분류 (large/mid/small)",
        "guide": "\"이 회사 순위는?\" → c.rank\n\"시장에서 몇 등이야?\" → c.rank.revenueRank\n\"대형주야?\" → c.rank.sizeClass",
        "kind": "property",
        "requires": "데이터: buildSnapshot() 사전 실행 필요",
        "seeAlso": "sector: 섹터 분류 (rank의 기준 그룹)\ninsights: 종합 등급 평가",
        "summary": "전체 시장 + 섹터 내 규모 순위 (매출/자산/성장률)."
    },
    "Company.ratioSeries": {
        "aicontext": "프로그래밍 방식 비율 접근 — insights/analysis 엔진이 내부적으로 소비",
        "capabilities": "수익성/안정성/성장성/효율성/밸류에이션 비율\n연도별 dict 구조 (timeseries/annual과 동일 형태)\nfinance XBRL 기반 정확한 비율",
        "guide": "\"비율 시계열 dict\" → c.ratioSeries\n\"ROE 연도별 리스트\" → series, years = c.ratioSeries; series[\"RATIO\"][\"roe\"]",
        "kind": "property",
        "requires": "데이터: finance (자동 다운로드)",
        "seeAlso": "ratios: DataFrame 형태 재무비율 (사용자 열람용)\nannual: 연도별 재무 시계열 (비율이 아닌 원본 금액)",
        "summary": "재무비율 연도별 시계열 (IS/BS/CF와 동일한 dict 구조)."
    },
    "Company.ratios": {
        "aicontext": "ask()/chat()에서 재무 건전성/수익성 평가의 핵심 데이터\ninsights, review가 내부적으로 ratios를 소비",
        "capabilities": "수익성/안정성/성장성/효율성/밸류에이션 5대 분류\n분기별 시계열 비율 자동 계산\nfinance XBRL 기반 정확한 비율",
        "guide": "\"재무비율 보여줘\" → c.ratios\n\"ROE 추이\" → c.ratios에서 ROE 행 확인\n\"부채비율은?\" → c.ratios에서 안정성 분류 확인",
        "kind": "property",
        "requires": "데이터: finance (자동 다운로드)",
        "seeAlso": "ratioSeries: dict 구조 재무비율 (프로그래밍 용도)\ninsights: 재무비율 기반 등급 + 이상치 분석\nselect: c.select(\"ratios\", [\"ROE\"]) 특정 비율 추출",
        "summary": "재무비율 시계열 (분류/항목 x 기간 DataFrame)."
    },
    "Company.rawDocs": {
        "aicontext": "원본 데이터 구조 파악 — 파싱 전 상태로 디버깅/검증에 활용",
        "capabilities": "HuggingFace docs 카테고리 원본 데이터 직접 접근\n가공/정규화 이전 상태 그대로 반환",
        "guide": "\"원본 공시 데이터 보여줘\" → c.rawDocs\n\"가공 전 데이터 확인\" → c.rawDocs",
        "kind": "property",
        "requires": "데이터: HuggingFace docs parquet (자동 다운로드)",
        "seeAlso": "sections: docs 가공 후 topic x period 통합 지도\nrawFinance: 재무제표 원본 데이터\nrawReport: 정기보고서 원본 데이터",
        "summary": "공시 문서 원본 parquet 전체 (가공 전)."
    },
    "Company.rawFinance": {
        "aicontext": "XBRL 정규화 전 원본 구조 파악 — 매핑 검증에 활용",
        "capabilities": "HuggingFace finance 카테고리 원본 데이터 직접 접근\nXBRL 정규화 이전 상태 그대로 반환",
        "guide": "\"원본 재무 데이터 보여줘\" → c.rawFinance\n\"XBRL 원본 확인\" → c.rawFinance",
        "kind": "property",
        "requires": "데이터: HuggingFace finance parquet (자동 다운로드)",
        "seeAlso": "BS: 가공된 재무상태표\nIS: 가공된 손익계산서\nrawDocs: 공시 문서 원본",
        "summary": "재무제표 원본 parquet 전체 (가공 전)."
    },
    "Company.rawReport": {
        "aicontext": "정기보고서 API 원본 확인 — report topic 매핑 검증에 활용",
        "capabilities": "HuggingFace report 카테고리 원본 데이터 직접 접근\n정기보고서 API 데이터 가공 이전 상태 반환",
        "guide": "\"원본 보고서 데이터 보여줘\" → c.rawReport\n\"정기보고서 원본 확인\" → c.rawReport",
        "kind": "property",
        "requires": "데이터: HuggingFace report parquet (자동 다운로드)",
        "seeAlso": "rawDocs: 공시 문서 원본\nrawFinance: 재무제표 원본\nshow: 가공된 topic 데이터 조회",
        "summary": "정기보고서 원본 parquet 전체 (가공 전)."
    },
    "Company.readFiling": {
        "aicontext": "공시 원문 텍스트를 LLM 컨텍스트에 주입하여 심층 분석 수행\nsections=True로 구조화하면 특정 섹션만 선택적 분석 가능",
        "capabilities": "접수번호(str) 직접 지정 또는 DataFrame row 자동 파싱\n전문 텍스트 또는 ZIP 기반 구조화 섹션 반환\n텍스트 길이 제한 (truncation) 지원",
        "guide": "\"이 공시 내용 보여줘\" → c.readFiling(접수번호)\n\"공시 원문 분석해줘\" → c.readFiling()으로 원문 확보 후 ask()로 분석",
        "kind": "method",
        "requires": "API 키: DART_API_KEY",
        "seeAlso": "liveFilings: 최신 공시 목록에서 접수번호 확인\ndisclosure: 과거 공시 목록에서 접수번호 확인",
        "summary": "접수번호 또는 liveFilings row로 공시 원문을 읽는다."
    },
    "Company.research": {
        "aicontext": "재무 + 시장 + 공시 통합 리포트 — ask()에서 종합 분석 컨텍스트\n섹션별 선택적 생성으로 필요한 부분만 딥다이브",
        "capabilities": "재무 분석 (수익성, 성장, 안정성, 현금흐름)\n시장 포지션 + 섹터 비교\n공시 기반 정성 분석 (사업모델, 리스크)\n섹션별 선택적 생성",
        "guide": "\"종합 리서치 보고서\" → c.research()\n\"재무+리스크만 분석\" → c.research(sections=[\"financial\", \"risk\"])",
        "kind": "method",
        "requires": "데이터: finance + docs (자동 다운로드)",
        "seeAlso": "review: 14섹션 구조화 보고서 (research보다 구조적)\ninsights: 7영역 등급 요약 (research보다 간결)\nanalysis: 14축 개별 분석",
        "summary": "종합 기업분석 리포트 (재무 + 시장 + 공시 통합)."
    },
    "Company.resolve": {
        "kind": "method",
        "summary": "종목코드 또는 회사명 → 종목코드 변환."
    },
    "Company.retrievalBlocks": {
        "aicontext": "ask()/chat()에서 원문 기반 답변 생성 시 소스로 사용\nretrieval 기반 컨텍스트 주입의 원천 데이터",
        "capabilities": "docs 원문을 markdown 형태 그대로 보존한 검색용 블록\n각 블록은 topic/subtopic/period 단위로 분할\nRAG, 벡터 검색, 원문 참조에 최적화된 포맷",
        "guide": "\"원문 검색용 블록\" → c.retrievalBlocks\n\"RAG용 데이터\" → c.retrievalBlocks",
        "kind": "property",
        "requires": "데이터: docs (자동 다운로드)",
        "seeAlso": "contextSlices: retrievalBlocks를 LLM 윈도우에 맞게 슬라이싱한 결과\nsections: 구조화된 데이터 지도 (retrievalBlocks의 원본)",
        "summary": "원문 markdown 보존 retrieval block DataFrame."
    },
    "Company.review": {
        "aicontext": "reviewer()가 이 결과를 소비하여 AI 해석 생성\nask()에서 재무분석 컨텍스트로 활용",
        "capabilities": "14개 섹션 전체 보고서 (수익구조~재무정합성)\n단일 섹션 지정 가능\n4개 출력 형식 (rich, html, markdown, json)\n섹션간 순환 서사 자동 감지\n레이아웃 커스텀",
        "guide": "\"재무 검토서 만들어줘\" → c.review()\n\"수익구조 분석\" → c.review(\"수익구조\")\n\"AI 의견 포함 보고서\" → c.reviewer() (review + AI 해석)",
        "kind": "method",
        "requires": "데이터: finance + report (자동 다운로드)",
        "seeAlso": "reviewer: review() + AI 섹션별 종합의견 (AI 해석 포함)\nanalysis: 14축 개별 분석 (review가 내부적으로 소비)\ninsights: 7영역 등급 + 이상치 요약",
        "summary": "재무제표 구조화 보고서 — 14개 섹션 데이터 검토서."
    },
    "Company.reviewer": {
        "aicontext": "review() 결과(재무비율, 추세, 동종업계 비교)를 LLM에 제공\nLLM이 각 섹션을 해석하여 종합의견 생성\nguide 파라미터로 분석 관점 커스텀",
        "capabilities": "review() 데이터 위에 AI 섹션별 종합의견 추가\n도메인 특화 가이드로 분석 관점 지정 가능\n각 섹션 시작에 AI 해석 삽입",
        "guide": "\"AI가 분석한 보고서\" → c.reviewer()\n\"반도체 관점에서 분석\" → c.reviewer(guide=\"반도체 사이클 관점에서 평가해줘\")\n\"특정 섹션만 AI 분석\" → c.reviewer(\"수익구조\")",
        "kind": "method",
        "requires": "AI: provider 설정 (dartlab.setup() 참조)\n데이터: finance + report (자동 다운로드)",
        "seeAlso": "review: AI 없는 순수 데이터 검토서 (reviewer의 기반)\nask: 자유 질문 기반 AI 분석\nchat: 에이전트 모드 심화 분석",
        "summary": "AI 분석 보고서 — review() + 섹션별 AI 종합의견."
    },
    "Company.sce": {
        "kind": "property",
        "summary": "자본변동표 DataFrame (연결 기준)."
    },
    "Company.sceMatrix": {
        "aicontext": "자본 변동 원인 분석 — 배당/자사주/유증 등 자본 이벤트 추적",
        "capabilities": "원인(cause) x 세부(detail) x 연도 3차원 매트릭스\n자본 구성요소별 변동 원인 추적\nfinance XBRL 정규화 기반",
        "guide": "\"자본변동표 매트릭스\" → c.sceMatrix\n\"자본 변동 원인 추적\" → matrix, years = c.sceMatrix",
        "kind": "property",
        "requires": "데이터: finance (자동 다운로드)",
        "seeAlso": "SCE: DataFrame 형태 자본변동표 (sceMatrix의 2D 뷰)\nBS: 재무상태표 (자본 잔액 확인)\ncapital: 주주환원 분석 (배당/자사주)",
        "summary": "자본변동표 연도별 매트릭스 (연결 기준)."
    },
    "Company.search": {
        "kind": "method",
        "summary": "회사명 부분 검색 (KIND 목록 기준)."
    },
    "Company.sections": {
        "aicontext": "회사 전체 지도 — 모든 분석의 출발점\nask()/chat()에서 topic 탐색 컨텍스트",
        "capabilities": "topic × period 수평화 통합 DataFrame\ndocs/finance/report 3-source 병합\nshow(topic)/trace(topic)/diff() 의 근간 데이터",
        "guide": "\"이 회사 전체 데이터 지도\" → c.sections\n\"어떤 topic이 있어?\" → c.sections 또는 c.topics",
        "kind": "property",
        "requires": "데이터: docs (필수), finance/report (선택, 자동 다운로드)",
        "seeAlso": "topics: sections 기반 topic 요약 (더 간결)\nshow: 특정 topic 데이터 조회\nindex: 전체 구조 메타데이터 목차",
        "summary": "sections — docs + finance + report 통합 지도."
    },
    "Company.sector": {
        "aicontext": "섹터 분류 결과로 동종업계 비교, 섹터 파라미터 자동 선택\nanalysis/valuation에서 섹터별 벤치마크 기준으로 활용",
        "capabilities": "WICS 11대 섹터 + 하위 산업그룹 자동 분류\nKIND 업종명 + 주요제품 키워드 기반 매칭\noverride 테이블 우선 → 키워드 → 업종명 순 fallback",
        "guide": "\"이 회사 어떤 섹터야?\" → c.sector\n\"업종 분류\" → c.sector",
        "kind": "property",
        "requires": "데이터: KIND 상장사 목록 (자동 로드)",
        "seeAlso": "sectorParams: 섹터별 밸���에이션 파라미터 (할인율, PER 등)\nrank: 섹�� 내 규모 순위\ninsights: 섹터 기준 등급 평가",
        "summary": "WICS 투자 섹터 분류 (KIND 업종 + 키워드 기반)."
    },
    "Company.sectorParams": {
        "aicontext": "valuation()에서 DCF 할인율, 성장률 자동 적용\n섹터 특성 반영된 밸류에이션 파라미터",
        "capabilities": "섹터별 할인율, 성장률, PER 멀티플 제공\n섹터 분류 결과에 연동된 파라미터 자동 선택",
        "guide": "\"이 섹터 할인율은?\" → c.sectorParams.discountRate\n\"PER 멀티플\" → c.sectorParams.perMultiple",
        "kind": "property",
        "requires": "데이터: sector 분류 결과 (자동 연산)",
        "seeAlso": "sector: 섹터 분류 정보 (sectorParams의 기반)\nvaluation: 밸류에이션 (sectorParams를 내부적으로 소비)",
        "summary": "현재 종목의 섹터별 밸류에이션 파라미터."
    },
    "Company.select": {
        "aicontext": "특정 계정의 시계열 추출 — 추세 분석 및 차트 생성의 기본 도구\n.chart() 체이닝으로 시각화까지 한 번에",
        "capabilities": "show() 결과에서 특정 계정/항목만 추출\n기간 필터링 (특정 연도만)\n.chart() 체이닝으로 바로 시각화\n한글/영문 계정명 모두 지원",
        "guide": "\"매출액 추이 그래프\" → c.select(\"IS\", [\"매출액\"]).chart()\n\"영업이익만 뽑아줘\" → c.select(\"IS\", [\"영업이익\"])\n\"2023-2024 자본 비교\" → c.select(\"BS\", [\"자본총계\"], [\"2024\", \"2023\"])",
        "kind": "method",
        "requires": "데이터: docs (자동 다운로드)",
        "seeAlso": "show: 전체 topic ��이터 조회 (select의 원본)\ntable: docs 마크다운 테이블 구조화 파싱",
        "summary": "show() 결과에서 행(indList) + 열(colList) 필터."
    },
    "Company.show": {
        "aicontext": "120+ topic에 대한 단일 접근점 — LLM이 데이터를 조회하는 핵심 도구\nperiod 리스트로 기간 비교 뷰 생성 가능",
        "capabilities": "120+ topic 접근 (재무제표, 사업내용, 지배구조, 임원현황 등)\n기간별 수평화 (topic × period 매트릭스)\n블록 단위 drill-down (목차 → 상세)\ndocs/finance/report 3개 소스 자동 통합\n세로 뷰 (period 리스트 전달 시)",
        "guide": "\"배당 정보 보여줘\" → c.show(\"dividend\")\n\"사업 개요 확인\" → c.show(\"businessOverview\")\n\"2023년 손익계산서\" → c.show(\"IS\", period=\"2023\")\n\"연도별 비교\" → c.show(\"IS\", period=[\"2022\", \"2023\"])",
        "kind": "method",
        "requires": "데이터: docs (자동 다운로드). finance topic은 finance 데이터도 필요.",
        "seeAlso": "select: show() 결과에서 특정 행/열 필터 + 차트\ntrace: 데이터 출처 추적\ntopics: 사용 가능한 topic 전체 목록\ndiff: 기간간 텍스트 변경 비교",
        "summary": "topic의 데이터를 반환."
    },
    "Company.simulation": {
        "aicontext": "거시경제 충격 시나리오별 재무 영향 정량화\nask()에서 리스크 질문 시 시뮬레이션 결과 컨텍스트로 활용",
        "capabilities": "기본 시나리오: 금리인상, 경기침체, 원화약세, 수요급감 등\n시나리오별 매출/영업이익/현금흐름 영향 추정\n섹터 민감도 반영",
        "guide": "\"금리인상 영향은?\" → c.simulation(scenarios=[\"금리인상\"])\n\"경기침체 시 실적 전망\" → c.simulation(scenarios=[\"경기침체\"])\n\"전체 시나리오 분석\" → c.simulation()",
        "kind": "method",
        "requires": "데이터: finance (자동 다운로드)",
        "seeAlso": "forecast: 기본 시나리오 매출 예측\nvaluation: 적정가치 산출\ngather: 거시경제 지표 수집 (macro 축)",
        "summary": "경제 시나리오 시뮬레이션 (거시경제 충격 → 재무 영향)."
    },
    "Company.sources": {
        "aicontext": "데이터 가용성 사전 점검 — 분석 가능 범위 판단의 기초",
        "capabilities": "3개 데이터 source(docs, finance, report) 존재 여부/규모 한눈에 확인\n각 source의 row/col 수와 shape 문자열 제공\n데이터 로드 전 가용성 사전 점검",
        "guide": "\"데이터 뭐가 있어?\" → c.sources\n\"docs/finance/report 상태\" → c.sources",
        "kind": "property",
        "requires": "없음 (메타데이터만 조회, 데이터 파싱 불필요)",
        "seeAlso": "topics: topic 단위 상세 데이터 지도\ntrace: 특정 topic의 출처 추적",
        "summary": "docs/finance/report 3개 source의 가용 현황 요약."
    },
    "Company.status": {
        "capabilities": "로컬 데이터 현황 (종목별 docs/finance/report 보유 여부)\n최종 업데이트 일시",
        "kind": "method",
        "summary": "로컬에 보유한 전체 종목 인덱스."
    },
    "Company.table": {
        "aicontext": "docs 원문 테이블을 구조화하여 정량 분석에 활용\nnumeric=True로 금액 문자열을 수치화하면 계산 가능",
        "capabilities": "docs 원문의 markdown table을 Polars DataFrame으로 변환\nsubtopic 지정으로 특정 표만 추출\nnumeric 모드로 금액 문자열을 float 변환\nperiod 필터로 특정 기간 컬럼만 선택",
        "guide": "\"직원 현황 테이블\" → c.table(\"employee\")\n\"표 데이터를 숫자로\" → c.table(topic, numeric=True)",
        "kind": "method",
        "requires": "데이터: docs (자동 다운로드)",
        "seeAlso": "show: topic 전체 데이터 (table은 subtopic 단위 파싱)\nselect: show() 결과에서 행/열 필터",
        "summary": "subtopic wide 셀의 markdown table을 구조화 DataFrame으로 파싱."
    },
    "Company.timeseries": {
        "aicontext": "insights, forecast, valuation 등 분석 엔진의 핵심 입력 데이터\n분기별 추세 분석의 기초",
        "capabilities": "BS/IS/CF 계정별 분기 standalone 시계열\n최대 10년 분기별 데이터\nfinance XBRL 정규화 기반",
        "guide": "\"분기별 시계열 데이터\" → c.timeseries\n\"매출 분기별 추이\" → series, periods = c.timeseries; series[\"IS\"][\"sales\"]",
        "kind": "property",
        "requires": "데이터: finance (자동 다운로드)",
        "seeAlso": "annual: 연도별 집계 시계열\ncumulative: 분기별 누적(YTD) 시계열\nBS: DataFrame 형태 재무상태표 (timeseries의 다른 뷰)",
        "summary": "분기별 standalone 시계열 (연결 기준)."
    },
    "Company.topics": {
        "aicontext": "LLM이 가용 topic 목록을 파악하는 데 사용\n분석 범위 결정 시 참조",
        "capabilities": "docs/finance/report 모든 source의 topic을 하나의 DataFrame으로 통합\nchapter 순서대로 정렬, 각 topic의 블록 수/기간 수/최신 기간 표시\n어떤 데이터가 있는지 한눈에 파악",
        "guide": "\"어떤 데이터가 있어?\" → c.topics\n\"topic 목록\" → c.topics",
        "kind": "property",
        "requires": "데이터: docs/finance/report 중 하나 이상 (자동 다운로드)",
        "seeAlso": "show: 특정 topic 데이터 조회\nsections: topic x period 전체 지도 (topics보다 상세)\nindex: 전체 구조 메타데이터 목차",
        "summary": "topic별 요약 DataFrame -- 전체 데이터 지도."
    },
    "Company.trace": {
        "aicontext": "데이터 출처 신뢰도 판단 — finance > report > docs 우선순위 확인\n분석 결과의 근거 투명성 확보",
        "capabilities": "topic별 데이터 출처 확인 (docs, finance, report)\n출처 선택 이유 (우선순위, fallback 경로)\n각 출처별 데이터 행 수, 기간 수, 커버리지",
        "guide": "\"이 데이터 어디서 온 거야?\" → c.trace(\"BS\")\n\"데이터 출처 확인\" → c.trace(topic)",
        "kind": "method",
        "requires": "데이터: docs + finance + report (보유한 것만 추적)",
        "seeAlso": "show: topic 데이터 조회 (trace로 출처 확인 후 열람)\nsources: 3개 source 전체 가용 현황",
        "summary": "topic 데이터의 출처(docs/finance/report)와 선택 근거 추적."
    },
    "Company.update": {
        "aicontext": "데이터 최신성 유지에 활용 — 분석 전 자동 갱신 트리거 가능",
        "capabilities": "DART API로 최신 공시 확인 후 누락분만 수집\n카테고리별 선택 수집",
        "guide": "\"최신 공시 반영해줘\" → c.update()\n\"데이터 업데이트\" → c.update()로 증분 수집",
        "kind": "method",
        "requires": "API 키: DART_API_KEY",
        "seeAlso": "filings: 현재 보유 공시 목록 확인\ndisclosure: OpenDART 전체 공시 조회",
        "summary": "누락된 최신 공시를 증분 수집."
    },
    "Company.valuation": {
        "aicontext": "DCF/DDM/상대가치 종합 적정가치 — 투자 판단의 핵심 출력\nask()에서 \"적정가치\" 질문 시 자동으로 이 결과 활용",
        "capabilities": "DCF (현금흐름 할인) 모델\nDDM (배당 할인) 모델\n상대가치 (PER/PBR/EV-EBITDA) 비교\n모델별 적정가 + 종합 가중 평균",
        "guide": "\"적정가치 구해줘\" → c.valuation()\n\"DCF 밸류에이션\" → c.valuation().dcf\n\"PER 기준 가치\" → c.valuation().relative",
        "kind": "method",
        "requires": "데이터: finance (자동 다운로드)",
        "seeAlso": "forecast: 매출 예측 (valuation의 입력)\nsectorParams: 섹터별 할인율/멀티플 (valuation이 내부 사용)\nsimulation: 시나리오별 가치 변동 추정",
        "summary": "종합 밸류에이션 (DCF + DDM + 상대가치)."
    },
    "Company.view": {
        "aicontext": "시각적 탐색 인터페이스 — 사용자가 브라우저에서 직접 데이터 탐색",
        "capabilities": "로컬 서버 기반 공시 뷰어 실행\n브라우저에서 sections/index 탐색",
        "guide": "\"공시 뷰어 열어줘\" → c.view()\n\"브라우저에서 보기\" → c.view()",
        "kind": "method",
        "requires": "데이터: HuggingFace docs parquet (자동 다운로드)",
        "seeAlso": "index: 뷰어가 소비하는 메타데이터 (프로그래밍 접근)\nsections: 뷰어의 원본 데��터",
        "summary": "브라우저에서 공시 뷰어를 엽니다."
    },
    "Company.watch": {
        "aicontext": "공시 변화 중요도 자동 평가 — 분석 우선순위 결정에 활용\n텍스트 변화량 + 재무 영향 통합 스코어",
        "capabilities": "전체 topic 변화 중요도 스코어링\n텍스트 변화량 + 재무 영향 통합 평가\n특정 topic 상세 변화 내역",
        "guide": "\"뭐가 크게 바뀌었어?\" → c.watch()\n\"리스크 관련 변화\" → c.watch(\"riskManagement\")",
        "kind": "method",
        "requires": "데이터: docs (자동 다운로드)",
        "seeAlso": "diff: 줄 단위 상세 변경 비교 (watch보다 세밀)\nkeywordTrend: 키워드 빈도 추이",
        "summary": "공시 변화 감지 — 중요도 스코어링 기반 변화 요약."
    },
    "Company.workforce": {
        "aicontext": "인력 효율성/근무환경 정량 평가 — 1인당 매출, 급여 수준 비교\n시장 횡단 비교로 인적자원 경쟁력 판단",
        "capabilities": "직원수 + 정규직/비정규직 비율\n평균 급여 + 1인당 매출\n평균 근속연수\n시장 전체 인력 횡단 비교",
        "guide": "\"직원 현황\" → c.workforce()\n\"평균 급여는?\" → c.workforce()\n\"전체 상장사 인력 비교\" → c.workforce(\"all\")",
        "kind": "method",
        "requires": "데이터: DART 정기보고서 (자동 수집)",
        "seeAlso": "governance: 이사회/감사위원 구성 (인력의 다른 관점)\nshow: c.show(\"employee\")로 docs 기반 직원 상세",
        "summary": "인력/급여 분석 (직원수, 평균급여, 근속연수)."
    },
    "Fred": {
        "kind": "class",
        "summary": "FRED 경제지표 facade."
    },
    "OpenDart": {
        "kind": "class",
        "summary": "OpenDART API 통합 클라이언트."
    },
    "OpenEdgar": {
        "kind": "class",
        "summary": "SEC public API facade."
    },
    "Review": {
        "aicontext": "review 수퍼툴이 이 클래스의 기능을 AI에게 노출.\nblocks action으로 블록 카탈로그, section으로 섹션별 리뷰.",
        "capabilities": "buildReview(company): 템플릿 기반 전체 리뷰 자동 생성 (2부 14축)\nReview([blocks...]): 블록 자유 조립 (맞춤 보고서)\nReview(stockCode=..., sections=[...]): 직접 구성\nrender(fmt): rich/html/markdown/json 4종 렌더링\ntoHtml(), toMarkdown(), toJson() 편의 메서드\nJupyter/Colab/Marimo 자동 HTML 렌더링 (_repr_html_)",
        "guide": "\"분석 보고서 보여줘\" -> c.review() 또는 buildReview(company)\n\"수익구조만 보고 싶어\" -> c.review(\"수익구조\")\n\"HTML로 내보내기\" -> review.toHtml()\n\"블록 목록 보여줘\" -> blocks(company) (카탈로그 테이블)\n\"매출 성장률 블록만\" -> b = blocks(c); b[\"growth\"]",
        "kind": "class",
        "requires": "Company 객체 (buildReview 사용 시) 또는 Block 리스트.",
        "seeAlso": "analysis: 14축 전략분석 엔진 (Review의 데이터 공급원)\nblocks: 블록 사전 (한글/영문/tab-complete)\nCompany.review: Company에서 바로 호출",
        "summary": "분석 리뷰 — 14축 전략분석 결과를 구조화 보고서로 렌더링."
    },
    "SelectResult": {
        "kind": "class",
        "summary": "select() 반환 객체 — DataFrame 위임 + 체이닝."
    },
    "analysis": {
        "aicontext": "reviewer()가 analysis 결과를 소비하여 AI 해석 생성\nask()에서 재무분석 컨텍스트로 활용\n70개 calc* 함수의 개별 결과를 LLM에 주입 가능",
        "capabilities": "Part 1 — 사업구조: 수익구조, 자금조달, 자산구조, 현금흐름\nPart 2 — 핵심비율: 수익성, 성장성, 안정성, 효율성, 종합평가\nPart 3 — 심화분석: 이익품질, 비용구조, 자본배분, 투자효율, 재무정합성\nPart 4 — 가치평가: DCF, DDM, 상대가치, RIM, 목표주가, 역내재성장률, 민감도\n각 축은 Company를 받아 dict를 반환하는 순수 함수 집합\nreview()가 이 결과를 소비하여 구조화 보고서 생성",
        "guide": "\"이 회사 수익구조?\" -> analysis(\"수익구조\", company) — 매출원가율, 판관비율 등\n\"재무 건전한가?\" -> analysis(\"안정성\", company) — 부채비율, 유동비율, ICR\n\"이익이 진짜야?\" -> analysis(\"이익품질\", company) — 발생주의 비율, OCF/NI\n\"적정가치?\" -> analysis(\"가치평가\", company) — DCF/DDM/상대/RIM/목표가\n\"전체 종합?\" -> analysis(\"종합평가\", company) — 15축 통합 스코어\n15축 전부 보고 싶으면 review() 사용 권장",
        "kind": "function",
        "requires": "데이터: finance (자동 다운로드)",
        "seeAlso": "review: analysis 결과를 구조화 보고서로 렌더링\nscan: 전종목 비교 (analysis는 단일 종목 심층)\nCompany.insights: 7영역 인사이트 등급 (빠른 요약)",
        "summary": "재무제표 완전 분석 — 15축, 단일 종목 심층."
    },
    "ask": {
        "aicontext": "재무비율, 추세, 동종업계 비교를 자동 계산하여 LLM에 제공\nsections 서술형 데이터 + finance 숫자 데이터 동시 주입\ntool calling provider에서는 LLM이 추가 데이터 자율 탐색",
        "capabilities": "자연어로 기업 분석 질문 (종목 자동 감지)\n스트리밍 출력 (기본) / 배치 반환 / Generator 직접 제어\n엔진 자동 계산 → LLM 해석 (Engine-First)\n데이터 모듈 include/exclude로 분석 범위 제어\n자체 검증 (reflect=True)",
        "guide": "\"삼성전자 분석해줘\" -> ask(\"삼성전자 재무건전성 분석해줘\")\n\"이 회사 괜찮아?\" -> ask(\"종목코드\", \"이 회사 투자해도 괜찮아?\")\n\"AI 설정 어떻게 해?\" -> dartlab.setup()으로 provider/키 설정 안내\nprovider 미설정 시 자동 감지. 설정 방법: dartlab.llm.configure(provider=\"openai\", api_key=\"sk-...\")\n보안: API 키는 로컬 .env에만 저장, 외부 전송 절대 없음",
        "kind": "function",
        "requires": "AI: provider 설정 (dartlab.setup() 참조)",
        "seeAlso": "chat: 대화형 연속 분석 (멀티턴)\nCompany: 프로그래밍 방식 데이터 접근\nscan: 전종목 비교 (ask보다 직접적)",
        "summary": "LLM에게 기업에 대해 질문."
    },
    "audit": {
        "aicontext": "투자 의사결정 전 감사 리스크 사전 점검에 사용\ngoingConcern 플래그로 계속기업 불확실성 즉시 감지\n감사인 변경 + 한정의견 조합으로 회계 신뢰도 평가",
        "capabilities": "감사의견 추이 (최근 5년, 적정/한정/부적정/의견거절)\n감사인 변경 이력 + 변경 사유\n계속기업 불확실성 플래그\n핵심감사사항 (KAM) 추출\n내부회계관리제도 검토의견",
        "guide": "\"이 회사 감사의견 괜찮아?\" -> audit(\"005930\")\n\"감사인 바뀐 적 있어?\" -> audit()에서 auditorChanges 확인\n\"계속기업 불확실성 있어?\" -> audit()에서 goingConcern 확인",
        "kind": "function",
        "requires": "데이터: docs + report (자동 다운로드)",
        "seeAlso": "insights: 7영역 종합 등급 (audit는 감사 특화)\nresearch: 종합 리포트 (audit 결과 포함)\ngovernance: 지배구조 횡단 비교 (감사위원회 정보)",
        "summary": "감사 Red Flag 분석."
    },
    "capabilities": {
        "aicontext": "AI가 \"dartlab에 뭐가 있는지\" 모를 때 탐색용.\ncapabilities() → 목차 확인 → capabilities(\"analysis\") → 상세 확인 → execute_code.\ncapabilities(search=\"재무건전성\") → 질문 관련 API 검색 → 코드 생성.",
        "capabilities": "CAPABILITIES dict에서 부분 조회 가능.\nkey 없이 호출 시 전체 키 목록(summary 포함) 반환.\nkey 지정 시 해당 항목의 상세(guide, capabilities, seeAlso 등) 반환.\nsearch 지정 시 자연어 질문 기반 관련 API 검색 (상위 10개).",
        "guide": "\"dartlab 뭐 할 수 있어?\" -> capabilities()\n\"분석 기능 뭐 있어?\" -> capabilities(\"analysis\")\n\"scan 어떻게 써?\" -> capabilities(\"scan\")\n\"재무건전성 관련 API?\" -> capabilities(search=\"재무건전성\")",
        "kind": "function",
        "requires": "없음",
        "seeAlso": "ask: AI 질문 (capabilities로 기능 파악 후 ask로 분석)\nsetup: AI provider 설정 (capabilities 확인 후 설정)",
        "summary": "dartlab 전체 기능 카탈로그 조회."
    },
    "capital": {
        "aicontext": "배당주 스크리닝, 주주환원 정책 비교에 사용\n배당수익률/배당성향 조합으로 지속가능성 판단\n자사주 매입/소각 이력으로 주주 친화도 평가",
        "capabilities": "전체 상장사 주주환원 정책 횡단 비교\n배당수익률, 배당성향, 자사주 매입/소각 이력\n유상증자/무상증자 이력",
        "guide": "\"배당 좋은 기업 찾아줘\" -> capital() DataFrame 정렬\n\"자사주 매입한 기업?\" -> capital() 결과 필터링\n\"주주환원 비교해줘\" -> capital()로 횡단 비교",
        "kind": "function",
        "requires": "데이터: report (dartlab.downloadAll(\"report\")로 사전 다운로드)",
        "seeAlso": "debt: 부채 구조 횡단 비교 (배당 여력과 부채 부담 동시 분석)\nworkforce: 인력/급여 횡단 비교 (인력 투자 vs 주주 환원)\ninsights: 개별 기업 배당 등급 분석 (capital은 전체 시장)",
        "summary": "한국 상장사 전체 주주환원 스캔."
    },
    "chat": {
        "aicontext": "ask()와 동일한 기본 컨텍스트 + 저수준 도구 접근\nLLM이 부족하다 판단하면 추가 데이터 자율 수집\ncompany=None이면 scan/gather/system 도구만 활성화",
        "capabilities": "LLM이 dartlab 도구를 자율적으로 선택/실행\n원본 공시 탐색, 계정 시계열 비교, 섹터 통계 등 심화 분석\n최대 N회 도구 호출 반복 (multi-turn)\n도구 호출/결과 콜백으로 UI 연동\n종목 없이도 동작 (시장 전체 질문, 메타 질문 등)",
        "guide": "\"깊게 분석해줘\" -> chat(\"005930\", \"배당 추세를 분석하고 이상 징후를 찾아줘\")\n\"시장 전체 거버넌스 비교\" -> chat(\"코스피 거버넌스 좋은 회사 찾아줘\")\n\"dartlab 뭐 할 수 있어?\" -> chat(\"dartlab 기능 알려줘\")\nask()보다 심화 분석이 필요할 때 사용. LLM이 자율적으로 도구 호출",
        "kind": "function",
        "requires": "AI: provider 설정 (tool calling 지원 provider 권장)",
        "seeAlso": "ask: 단일 질문 (간단한 분석)\nCompany: 프로그래밍 방식 직접 접근\nscan: 전종목 횡단분석",
        "summary": "에이전트 모드: LLM이 도구를 선택하여 심화 분석."
    },
    "codeToName": {
        "kind": "function",
        "summary": "종목코드 → 회사명."
    },
    "collect": {
        "aicontext": "사용자가 특정 종목의 최신 데이터를 직접 수집할 때 사용.",
        "capabilities": "종목별 DART 공시 데이터 직접 수집 (finance, docs, report)\n멀티키 병렬 수집 (DART_API_KEYS 쉼표 구분)\n증분 수집 — 이미 있는 데이터는 건너뜀\n카테고리별 선택 수집",
        "guide": "\"데이터 수집해줘\" -> DART_API_KEY 필요. dartlab.setup(\"dart-key\", \"YOUR_KEY\")로 설정 안내\n\"삼성전자 재무 데이터 수집\" -> collect(\"005930\", categories=[\"finance\"])\n보안: 키는 로컬 .env에만 저장, 외부 전송 절대 없음",
        "kind": "function",
        "requires": "API 키: DART_API_KEY",
        "seeAlso": "Company: 수집된 데이터로 Company 생성하여 분석\nsearch: 종목코드 모를 때 먼저 검색",
        "summary": "지정 종목 DART 데이터 수집 (OpenAPI)."
    },
    "collectAll": {
        "capabilities": "전체 상장종목 DART 공시 데이터 일괄 수집\n미수집 종목만 선별 수집 (mode=\"new\") 또는 전체 재수집 (mode=\"all\")\n멀티키 병렬 수집 (DART_API_KEYS 쉼표 구분)\n카테고리별 선택 (finance, docs, report)",
        "guide": "\"전종목 데이터 수집\" -> collectAll() 안내. DART_API_KEY 필요\n\"재무 데이터만 수집\" -> collectAll(categories=[\"finance\"])\n보안: 키는 로컬 .env에만 저장, 외부 전송 절대 없음",
        "kind": "function",
        "requires": "API 키: DART_API_KEY",
        "seeAlso": "collect: 특정 종목만 수집\ndownloadAll: HuggingFace 사전구축 데이터 (API 키 불필요, 더 빠름)",
        "summary": "전체 상장종목 DART 데이터 일괄 수집."
    },
    "config": {
        "kind": "module",
        "summary": "dartlab 전역 설정."
    },
    "core": {
        "kind": "module",
        "summary": ""
    },
    "dataDir": {
        "kind": "module",
        "summary": "str(object='') -> str"
    },
    "debt": {
        "aicontext": "재무 안정성 리스크 스크리닝에 사용\n부채비율/이자보상배율 극단값으로 위험 기업 탐지\n단기/장기 차입 구조 분석으로 유동성 리스크 평가",
        "capabilities": "전체 상장사 부채 구조 횡단 비교\n부채비율, 차입금 의존도, 이자보상배율\n단기/장기 차입금 구성, 사채 발행 현황",
        "guide": "\"부채비율 높은 기업?\" -> debt() DataFrame 정렬\n\"재무 안정적인 기업 찾아줘\" -> debt() 결과 필터링\n\"부채 구조 비교해줘\" -> debt()로 횡단 비교",
        "kind": "function",
        "requires": "데이터: report (dartlab.downloadAll(\"report\")로 사전 다운로드)",
        "seeAlso": "capital: 주주환원 횡단 비교 (부채 vs 배당 균형 분석)\ninsights: 개별 기업 안정성 등급 (debt는 전체 시장)\nscan: 전종목 횡단 비교 통합 인터페이스",
        "summary": "한국 상장사 전체 부채 구조 스캔."
    },
    "digest": {
        "aicontext": "시장 전체에서 공시 변화가 큰 기업을 중요도 순으로 제공\n섹터별 필터링으로 관심 업종의 변화 포착\n마크다운/JSON 출력으로 LLM 컨텍스트에 직접 주입 가능",
        "capabilities": "전체 상장사 공시 변화 중요도 순위\n섹터별 필터링\n텍스트 변화량 + 재무 변화 통합 스코어링\nDataFrame/마크다운/JSON 출력",
        "guide": "\"최근 공시 변화 큰 기업?\" -> digest()\n\"반도체 섹터 공시 변화\" -> digest(sector=\"반도체\")\n\"시장 동향 요약해줘\" -> digest(format=\"markdown\")",
        "kind": "function",
        "requires": "데이터: docs (dartlab.downloadAll(\"docs\")로 사전 다운로드)",
        "seeAlso": "scan: 전종목 횡단 비교 통합 (digest는 공시 변화 특화)\nCompany.diff: 개별 기업 기간간 변화 (digest는 시장 전체)\ncheckFreshness: 데이터 최신성 확인 (digest 전 갱신 여부 판단)",
        "summary": "시장 전체 공시 변화 다이제스트."
    },
    "downloadAll": {
        "capabilities": "HuggingFace 사전 구축 데이터 일괄 다운로드\nfinance (~600MB, 2700+종목), docs (~8GB, 2500+종목), report (~320MB, 2700+종목)\n이어받기/병렬 다운로드 지원 (huggingface_hub)\n전사 분석(scanAccount, governance, digest 등)에 필요한 데이터 사전 준비",
        "guide": "\"데이터 어떻게 받아?\" -> downloadAll(\"finance\") 안내. API 키 불필요\n\"scan 쓰려면?\" -> downloadAll(\"finance\") + downloadAll(\"report\") 필요\nfinance 먼저 (600MB), report 다음 (320MB), docs는 대용량 주의 (8GB)",
        "kind": "function",
        "requires": "없음 (HuggingFace 공개 데이터셋)",
        "seeAlso": "scan: 다운로드된 데이터로 전종목 비교\ncollect: DART API로 직접 수집 (최신 데이터, API 키 필요)",
        "summary": "HuggingFace에서 전체 시장 데이터 다운로드."
    },
    "forecast": {
        "aicontext": "매출 성장 전망 수치를 DCF/밸류에이션에 입력으로 활용\n신뢰구간으로 예측 불확실성 정량화\n업종 성장률 반영으로 단순 추세 외삽보다 현실적 전망",
        "capabilities": "매출 시계열 기반 앙상블 예측 (ARIMA + 선형 + 지수평활)\n업종 성장률 가중 보정\n신뢰구간 (80%, 95%) 제공\n최대 N년 전망 (기본 3년)",
        "guide": "\"매출 전망 보여줘\" -> forecast(\"005930\")\n\"5년 뒤 매출 예측\" -> forecast(\"005930\", horizon=5)\n\"이 회사 성장할까?\" -> forecast()로 매출 추세 확인",
        "kind": "function",
        "requires": "데이터: finance (자동 다운로드)",
        "seeAlso": "valuation: 밸류에이션 (forecast 결과를 DCF에 활용)\nsimulation: 시나리오별 재무 영향 (forecast는 기본 전망)\ninsights: 성장성 등급 (forecast는 미래 추정)",
        "summary": "매출 앙상블 예측."
    },
    "fuzzySearch": {
        "kind": "function",
        "summary": "한글 fuzzy 종목 검색 — 초성 매칭 + Levenshtein 거리."
    },
    "gather": {
        "aicontext": "ask()/chat()에서 주가/수급/거시 데이터를 컨텍스트로 주입 가능\n기업 분석 시 시장 데이터 보충 자료로 활용",
        "capabilities": "price: OHLCV 시계열 (KR Naver/US Yahoo, 기본 1년, 최대 6000거래일)\nflow: 외국인/기관 수급 동향 (KR 전용, Naver)\nmacro: ECOS(KR 12개) / FRED(US 25개) 거시지표 시계열\nnews: Google News RSS 뉴스 수집 (최근 30일)\n자동 fallback 체인, circuit breaker, TTL 캐시",
        "guide": "\"주가 추이 보여줘\" -> gather(\"price\", \"005930\")\n\"외국인 매매 동향\" -> gather(\"flow\", \"005930\")\n\"금리 추이 알려줘\" -> gather(\"macro\", \"BASE_RATE\") 또는 gather(\"macro\", \"FEDFUNDS\")\n\"최근 뉴스 찾아줘\" -> gather(\"news\", \"삼성전자\")\n\"미국 거시지표 전체\" -> gather(\"macro\", market=\"US\") 또는 gather(\"US\")\n주가+수급은 scan과 다름. scan은 재무 기반 횡단, gather는 시장 실시간.",
        "kind": "function",
        "requires": "price/flow/news: 없음 (공개 API)\nmacro: API 키 — ECOS_API_KEY (KR) 또는 FRED_API_KEY (US)",
        "seeAlso": "scan: 재무 기반 전종목 횡단분석 (거버넌스, 현금흐름 등)\nCompany: 개별 종목 공시/재무 데이터\nanalysis: 14축 전략분석 (재무비율, 수익구조 등)",
        "summary": "외부 시장 데이터 통합 수집 — 4축, 전부 Polars DataFrame."
    },
    "getKindList": {
        "kind": "function",
        "summary": "KRX KIND 상장법인 전체 목록."
    },
    "governance": {
        "aicontext": "전체 시장의 지배구조 리스크 스크리닝에 사용\n최대주주 지분율 극단값, 사외이사 미선임 기업 탐지\ngovernance 점수가 낮은 기업군 필터링 후 심화 분석 연계",
        "capabilities": "전체 상장사 지배구조 횡단 비교\n최대주주 지분율, 사외이사 비율, 감사위원회 설치 여부\n지분 변동 추이, 특수관계인 거래",
        "guide": "\"지배구조 좋은 기업 찾아줘\" -> governance()로 횡단 비교\n\"최대주주 지분율 높은 기업?\" -> governance() DataFrame 정렬\n\"사외이사 비율 낮은 곳은?\" -> governance() 결과 필터링",
        "kind": "function",
        "requires": "데이터: report (dartlab.downloadAll(\"report\")로 사전 다운로드)",
        "seeAlso": "network: 기업 간 지분 관계 시각화 (governance는 개별 기업 지표)\nscan: 전종목 횡단 비교 통합 인터페이스\nworkforce: 인력/급여 횡단 비교 (governance와 함께 ESG 분석)",
        "summary": "한국 상장사 전체 지배구조 스캔."
    },
    "insights": {
        "aicontext": "기업의 재무 건전성을 7영역 등급으로 요약\n강점/약점 자동 식별로 분석 포커스 결정\n동종업계 백분위로 상대적 위치 즉시 파악",
        "capabilities": "수익성, 성장성, 안정성, 효율성, 현금흐름, 밸류에이션, 배당 — 7영역\n각 영역 A~F 등급 부여 + 근거 지표\n종합 등급 + 강점/약점 요약\n동종업계 백분위 위치",
        "guide": "\"이 회사 재무 어때?\" -> insights(\"005930\")\n\"수익성 등급 알려줘\" -> insights()에서 grades 조회\n\"강점이 뭐야?\" -> insights()에서 strengths 확인",
        "kind": "function",
        "requires": "데이터: finance (자동 다운로드)",
        "seeAlso": "audit: 감사 Red Flag 분석 (insights는 재무 등급)\nvaluation: 밸류에이션 상세 (insights는 종합 등급)\nresearch: 종합 리포트 (insights 결과 포함)",
        "summary": "7영역 등급 분석."
    },
    "listing": {
        "aicontext": "전종목 대상 필터링/통계에 사용. scan()과 조합하여 시장 전체 분석.",
        "capabilities": "KR 전체 상장법인 목록 (KOSPI + KOSDAQ)\n종목코드, 종목명, 시장구분, 업종 포함\nUS listing은 향후 지원 예정",
        "guide": "\"상장된 회사 몇 개야?\" -> listing()으로 전체 목록 조회 후 개수\n\"코스닥 회사 목록?\" -> listing()에서 market 필터\nAPI 키 불필요.",
        "kind": "function",
        "requires": "데이터: listing (자동 다운로드)",
        "seeAlso": "search: 키워드로 특정 종목 검색\nscan: 전종목 횡단 비교 분석",
        "summary": "전체 상장법인 목록."
    },
    "llm": {
        "kind": "module",
        "summary": "LLM 기반 기업분석 엔진."
    },
    "nameToCode": {
        "kind": "function",
        "summary": "회사명 → 종목코드. 정확히 일치하는 첫 번째 결과."
    },
    "network": {
        "aicontext": "기업 간 지분 관계 파악에 사용\n그룹사 구조, 모자회사 관계 시각적 탐색\nnodes/edges 데이터로 프로그래밍 방식 관계 분석 가능",
        "capabilities": "상장사 간 지분 관계 네트워크 시각화\n브라우저에서 인터랙티브 그래프 표시\n노드(기업) + 엣지(지분 관계) 구조",
        "guide": "\"상장사 관계 보여줘\" -> network().show()\n\"기업 간 지분 관계 알려줘\" -> network()로 네트워크 데이터 접근\n\"그룹사 구조 시각화\" -> network().show()로 브라우저 렌더링",
        "kind": "function",
        "requires": "데이터: docs (자동 다운로드)",
        "seeAlso": "governance: 개별 기업 지배구조 상세 (network는 전체 관계 지도)\nscan: 전종목 횡단 비교 (network는 관계 중심)",
        "summary": "한국 상장사 전체 관계 지도."
    },
    "plugins": {
        "aicontext": "확장 기능 탐색 시 설치된 플러그인 목록 확인\n플러그인이 제공하는 topic을 show()에서 사용 가능\n플러그인 유무에 따라 분석 범위 동적 결정",
        "capabilities": "설치된 dartlab 플러그인 자동 탐색\n플러그인 메타데이터 (이름, 버전, 제공 topic) 조회",
        "guide": "\"플러그인 뭐 있어?\" -> plugins()\n\"확장 기능 목록\" -> plugins()로 설치된 플러그인 확인\n\"ESG 플러그인 있어?\" -> plugins()에서 검색",
        "kind": "function",
        "requires": "없음",
        "seeAlso": "reload_plugins: 새 플러그인 설치 후 재스캔\nCompany.show: 플러그인 topic 조회 (plugins가 제공한 topic 사용)",
        "summary": "로드된 플러그인 목록 반환."
    },
    "reload_plugins": {
        "aicontext": "pip install 후 세션 재시작 없이 플러그인 즉시 활성화\n새로 인식된 topic이 Company.show()에서 바로 사용 가능",
        "capabilities": "새로 설치한 플러그인 즉시 인식 (세션 재시작 불필요)\nentry_points 재스캔",
        "guide": "\"새 플러그인 설치했는데 안 보여\" -> reload_plugins()\n\"플러그인 재스캔\" -> reload_plugins()",
        "kind": "function",
        "requires": "없음",
        "seeAlso": "plugins: 현재 로드된 플러그인 확인 (reload 전후 비교)\nCompany.show: 플러그인 topic 조회",
        "summary": "플러그인 재스캔 — pip install 후 재시작 없이 즉시 인식."
    },
    "research": {
        "aicontext": "재무 + 시장 + 공시 통합 리포트 자동 생성\n마크다운 구조로 LLM이 섹션별 참조 가능\n섹션 선택으로 특정 관점만 추출 가능",
        "capabilities": "재무분석 + 시장분석 통합 리포트\n섹션별 선택 생성 가능\n재무비율 추세, 동종업계 비교, 시장 포지션\n구조화된 마크다운 출력",
        "guide": "\"기업 분석 리포트 만들어줘\" -> research(\"005930\")\n\"재무분석만 보고 싶어\" -> research(\"005930\", includeMarket=False)\n\"종합 분석해줘\" -> research()로 전체 리포트 생성",
        "kind": "function",
        "requires": "데이터: finance + docs (자동 다운로드)",
        "seeAlso": "insights: 7영역 등급 (research는 서술형 리포트)\nask: AI가 해석하는 분석 (research는 엔진 기반 구조화)\nforecast: 매출 예측 (research 리포트에 포함)",
        "summary": "종합 기업분석 리포트."
    },
    "scan": {
        "aicontext": "시장 전체 비교/순위 질문에 사용. 개별 종목 분석은 Company 메서드 사용.",
        "capabilities": "governance: 최대주주 지분, 사외이사, 감사위원회 종합 등급\nworkforce: 임직원 수, 평균급여, 근속연수\ncapital: 배당수익률, 배당성향, 자사주\ndebt: 사채만기, 부채비율, ICR, 위험등급\naccount: 전종목 단일 계정 시계열 (매출액, 영업이익 등)\nratio: 전종목 단일 재무비율 시계열 (ROE, 부채비율 등)\ncashflow: OCF/ICF/FCF + 현금흐름 패턴 분류\naudit: 감사의견, 감사인변경, 특기사항, 감사독립성\ninsider: 최대주주 지분변동, 자기주식, 경영권 안정성\nquality: Accrual Ratio + CF/NI -- 이익의 현금 뒷받침\nliquidity: 유동비율 + 당좌비율 -- 단기 지급능력\ngrowth: 매출/영업이익/순이익 CAGR + 성장 패턴 분류\nprofitability: 영업이익률/순이익률/ROE/ROA + 등급\ndigest: 시장 전체 공시 변화 다이제스트\nnetwork: 상장사 관계 네트워크 (출자/지분/계열)",
        "guide": "\"다른 회사랑 비교 가능해?\" -> scan(\"account\") 또는 scan(\"ratio\") 안내\n\"거버넌스 좋은 회사?\" -> scan(\"governance\")로 등급 A 필터\n\"배당 많이 주는 회사?\" -> scan(\"capital\")로 배당수익률 정렬\n\"ROE 높은 회사?\" -> scan(\"ratio\", \"roe\")로 전종목 비교\n\"삼성전자랑 SK하이닉스 비교\" -> scan(\"account\", \"sales\", code=\"005930,000660\")\nAPI 키 불필요. 사전 다운로드 데이터만으로 동작.",
        "kind": "function",
        "requires": "데이터: 축별로 다름 (dartlab.downloadAll() 참조)\ngovernance/workforce/capital/debt/audit/insider: report\naccount/ratio: finance\nnetwork/digest: docs",
        "seeAlso": "analysis: 개별 종목 14축 전략분석\nCompany.insights: 단일 종목 7영역 종합 분석\ngather: 주가/수급 데이터 (모멘텀 보완)",
        "summary": "시장 전체 횡단분석 -- 15축, 전부 Polars DataFrame."
    },
    "scanAccount": {
        "aicontext": "전종목 동일 계정을 한 번에 비교하여 이상치/트렌드 탐지\n피벗 테이블 형태로 시계열 분석 즉시 가능\nKR/US 양쪽 시장 동일 인터페이스로 글로벌 비교",
        "capabilities": "전체 상장종목의 특정 계정 시계열 횡단 비교\n한글/영문 계정명 모두 지원 (\"매출액\" = \"sales\")\nDART(KR) + EDGAR(US) 양쪽 지원\n분기별/연간 선택, 연결/별도 선택",
        "guide": "\"전종목 매출 비교\" -> scan(\"account\", \"매출액\")\n\"전체 기업 자산 순위\" -> scan(\"account\", \"total_assets\") 후 정렬\n\"미국 기업 매출 비교\" -> scan(\"account\", \"sales\", market=\"edgar\")",
        "kind": "function",
        "requires": "데이터: finance (dartlab.downloadAll(\"finance\")로 사전 다운로드)",
        "seeAlso": "scanRatio: 전종목 재무비율 횡단 비교 (scanAccount는 원시 계정)\nscan: 전종목 횡단 비교 통합 인터페이스\nCompany.finance: 개별 기업 재무 상세",
        "summary": "전종목 단일 계정 시계열."
    },
    "scanRatio": {
        "aicontext": "전종목 동일 비율을 한 번에 비교하여 업종별 분포 파악\nROE/영업이익률 등 핵심 비율의 시장 전체 추이 분석\n이상치 기업 탐지 및 피어 그룹 벤치마킹에 활용",
        "capabilities": "전체 상장종목의 특정 재무비율 시계열 횡단 비교\nROE, 영업이익률, 부채비율 등 주요 비율 지원\nDART(KR) + EDGAR(US) 양쪽 지원\n분기별/연간 선택",
        "guide": "\"전종목 ROE 비교\" -> scan(\"ratio\", \"roe\")\n\"영업이익률 높은 기업 순위\" -> scan(\"ratio\", \"operatingMargin\") 후 정렬\n\"미국 기업 ROE 비교\" -> scan(\"ratio\", \"roe\", market=\"edgar\")",
        "kind": "function",
        "requires": "데이터: finance (dartlab.downloadAll(\"finance\")로 사전 다운로드)",
        "seeAlso": "scanAccount: 전종목 원시 계정 횡단 비교 (scanRatio는 가공된 비율)\nscan: 전종목 횡단 비교 통합 인터페이스\ninsights: 개별 기업 등급 (scanRatio는 시장 전체)",
        "summary": "전종목 단일 재무비율 시계열."
    },
    "search": {
        "aicontext": "종목코드를 모를 때 사용. 결과에서 종목코드 확인 후 Company 생성.",
        "capabilities": "한글 입력 시 DART 종목 검색 (종목명, 종목코드)\n영문 입력 시 EDGAR 종목 검색 (ticker, 회사명)\n부분 일치, 초성 검색 지원 (KR)",
        "guide": "\"삼성전자 종목코드 뭐야?\" -> search(\"삼성전자\")로 종목코드 확인\n\"애플 티커?\" -> search(\"AAPL\")로 EDGAR 종목 검색\nAPI 키 불필요. listing 데이터만으로 동작.",
        "kind": "function",
        "requires": "데이터: listing (자동 다운로드)",
        "seeAlso": "Company: 종목코드 확인 후 Company 생성하여 상세 분석\nlisting: 전체 상장법인 목록 조회",
        "summary": "종목 검색 (KR + US 통합)."
    },
    "searchName": {
        "kind": "function",
        "summary": "회사명 부분 검색."
    },
    "setup": {
        "aicontext": "AI 분석 기능 사용 전 provider 설정 상태 확인\n미설정 provider 감지 시 setup() 안내로 연결\n설정 완료 여부를 프로그래밍 방식으로 체크 가능",
        "capabilities": "전체 AI provider 설정 현황 테이블 표시\nprovider별 대화형 설정 (키 입력 → .env 저장)\nChatGPT OAuth 브라우저 로그인\nOpenAI/Gemini/Groq/Cerebras/Mistral API 키 설정\nOllama 로컬 LLM 설치 안내",
        "guide": "\"AI 설정 어떻게 해?\" -> setup()으로 전체 현황 확인\n\"ChatGPT 연결하고 싶어\" -> setup(\"chatgpt\")\n\"OpenAI 키 등록\" -> setup(\"openai\")\n\"Ollama 어떻게 써?\" -> setup(\"ollama\")",
        "kind": "function",
        "requires": "없음",
        "seeAlso": "ask: AI 질문 (setup 완료 후 사용)\nchat: AI 대화 (setup 완료 후 사용)\nllm.configure: 프로그래밍 방식 provider 설정",
        "summary": "AI provider 설정 안내 + 인터랙티브 설정."
    },
    "simulation": {
        "aicontext": "거시 변수 변동이 개별 기업 재무에 미치는 영향 정량화\n업종별 민감도 차등으로 현실적 스트레스 테스트\n복수 시나리오 동시 비교로 리스크 범위 파악",
        "capabilities": "거시경제 시나리오별 재무 영향 시뮬레이션\n기본 시나리오: 금리 인상, 경기 침체, 원자재 급등, 환율 변동\n매출/영업이익/순이익 변동 추정\n업종별 민감도 차등 적용",
        "guide": "\"금리 오르면 이 회사 어떻게 돼?\" -> simulation(\"005930\")\n\"경기 침체 시나리오\" -> simulation()에서 해당 시나리오 확인\n\"환율 영향 분석\" -> simulation()으로 환율 변동 시나리오 조회",
        "kind": "function",
        "requires": "데이터: finance (자동 다운로드)",
        "seeAlso": "forecast: 매출 예측 (simulation은 시나리오별 변동)\nvaluation: 밸류에이션 (시나리오별 적정가치 비교에 활용)\nresearch: 종합 리포트 (simulation 결과 포함)",
        "summary": "경제 시나리오 시뮬레이션."
    },
    "table": {
        "capabilities": "yoy: 전년 동기 대비 변동률\nsummary: 평균/CAGR/추세 요약\npivot: 계정별 피벗 테이블\nformat: 한국어 단위 포맷팅\ngrowth: 성장률 행렬\nratio: 재무비율 계산",
        "kind": "function",
        "summary": "테이블 가공 엔진 -- DataFrame 변환/포맷팅."
    },
    "text": {
        "kind": "module",
        "summary": "텍스트 분석 도구."
    },
    "valuation": {
        "aicontext": "적정주가 범위 산출로 투자 판단 근거 제공\nDCF/DDM/상대가치 3가지 관점의 교차 검증\nshares 자동 조회로 주당 가치 즉시 산출",
        "capabilities": "DCF (잉여현금흐름 할인 모형)\nDDM (배당할인 모형)\n상대가치 (PER/PBR/EV-EBITDA 동종업계 비교)\n적정주가 범위 산출",
        "guide": "\"적정 주가 얼마야?\" -> valuation(\"005930\")\n\"이 회사 저평가야?\" -> valuation()에서 summary 확인\n\"DCF 해줘\" -> valuation()에서 dcf 항목 조회",
        "kind": "function",
        "requires": "데이터: finance (자동 다운로드)",
        "seeAlso": "forecast: 매출 예측 (valuation의 DCF 입력에 활용)\ninsights: 밸류에이션 등급 (valuation은 절대/상대 가치 상세)\nresearch: 종합 리포트 (valuation 결과 포함)",
        "summary": "종합 밸류에이션 (DCF + DDM + 상대가치)."
    },
    "verbose": {
        "kind": "module",
        "summary": "bool(x) -> bool"
    },
    "workforce": {
        "aicontext": "업종별 인력 효율성 비교에 사용\n평균급여 대비 매출/이익 생산성 분석 연계\n직원 수 증감 추이로 사업 확장/축소 신호 탐지",
        "capabilities": "전체 상장사 임직원 현황 횡단 비교\n임직원 수, 평균 근속연수, 평균 급여, 성별 비율\n업종별/규모별 비교",
        "guide": "\"평균 급여 높은 기업?\" -> workforce() DataFrame 정렬\n\"직원 수 많은 기업 순위\" -> workforce() 결과 필터링\n\"인력 현황 비교해줘\" -> workforce()로 횡단 비교",
        "kind": "function",
        "requires": "데이터: report (dartlab.downloadAll(\"report\")로 사전 다운로드)",
        "seeAlso": "governance: 지배구조 횡단 비교 (workforce와 함께 ESG 분석)\ncapital: 주주환원 횡단 비교 (인력 투자 vs 주주 환원 비교)\nscan: 전종목 횡단 비교 통합 인터페이스",
        "summary": "한국 상장사 전체 인력/급여 스캔."
    }
}
